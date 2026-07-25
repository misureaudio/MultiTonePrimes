#!/usr/bin/env python3
"""
Port of PhiLstMuTNewMin.m

Monte Carlo optimizer that searches for the phase combination yielding
the lowest crest factor for a multitone test signal.

Usage:
    python -m multitone.optimizer [--fraction FRACTION] [--fsam FSAM] [--sbit SBIT]
                                   [--ilowfreq ILOWFREQ] [--nch NCH]
                                   [--attvol ATT] [--dur DUR] [--maxiter ITER]
                                   [--ext EXT] [--rd RD] [--seed SEED]

Examples:
    # Default: Fraction=12, 96kHz, 24-bit, mono
    python -m multitone.optimizer

    # Fraction=3, 48kHz, starting from iteration 10001
    python -m multitone.optimizer --fraction 3 --fsam 48000 --maxiter 100000
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import scipy.io as sio

from multitone.primes import mut_primes
from multitone.synthesize import crest_factor_dB, frq_lst_vol_att

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Pre-computed attenuation data file names (must be in the data/ directory)
ATTEN_DATA = {
    3: "fr03pri384k.mat",
    6: "fr06pri384k.mat",
    12: "fr12pri384k.mat",
}

# Variable name mapping: (fraction, fsam) → (mat_variable_name,)
# e.g., Fraction=12, Fs=96000 → 'fr12frqprilim096k'
FSAM_KEY = {
    44100: "044k",
    48000: "048k",
    88200: "088k",
    96000: "096k",
    176400: "176k",
    192000: "192k",
}


def load_attenuation(fraction: int, fsam: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Load the frequency-attenuation lookup table for the given fraction and
    sampling rate.

    Returns
    -------
    FrqPriLst : ndarray
        Frequency values (Hz).
    FrqAttLst : ndarray
        Per-frequency attenuation (dB).
    """
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    mat_file = os.path.join(data_dir, ATTEN_DATA[fraction])

    if not os.path.exists(mat_file):
        print(f"ERROR: Attenuation data file not found: {mat_file}", file=sys.stderr)
        sys.exit(1)

    mat = sio.loadmat(mat_file)

    key = f"fr{fraction:02d}frqprilim{FSAM_KEY[fsam]}"
    if key not in mat:
        print(
            f"ERROR: Variable '{key}' not found in {mat_file}. "
            f"Available keys: {list(mat.keys())}",
            file=sys.stderr,
        )
        sys.exit(1)

    data = mat[key]  # shape (N, 2): [frequency, attenuation_dB]

    # MATLAB optimizer slices from iLowFreq:lll (1-indexed)
    # We handle that in the main function
    return data[:, 0], data[:, 1]


# ---------------------------------------------------------------------------
# File name formatting
# ---------------------------------------------------------------------------

def format_phase_filename(
    nch: int,
    fraction: int,
    lfl: int,
    fsam: int,
    sbit: int,
    fllow: int,
    flhig: int,
    nfr: int,
    iteration: int,
    cfact: float,
) -> str:
    """Generate the .mat file name for the best phase set."""
    return (
        f"PhiLstMuTNewMin[Nch {nch}][Frac {fraction:02d}]"
        f"[LFL {lfl:03d}][{fsam:06d}-{sbit:02d}]"
        f"[{fllow:05d}-{flhig:05d}][Nfr {nfr:03d}]"
        f"[{iteration:06d}]-[{cfact:7.4f}].mat"
    )


def format_audio_filename(
    nch: int,
    fraction: int,
    lfl: int,
    fllow: int,
    flhig: int,
    nfr: int,
    fsam: int,
    sbit: int,
    dur: int,
    attvol: float,
    iteration: int,
    cfact: float,
    rd: str,
    ext: str,
) -> str:
    """Generate the audio file name."""
    return (
        f"PrimeToneNewPhi[Nch {nch}][Frac {fraction:02d}]"
        f"[LFL {lfl:03d}][{fllow:05d}-{flhig:05d}]"
        f"[Nfr {nfr:03d}]-[{fsam}-{sbit}]-[{dur}s]-[{attvol:5.2f}dB]"
        f"-[{iteration:06d}]-[{cfact:7.4f}]-[{rd}]{ext}"
    )


# ---------------------------------------------------------------------------
# Main optimizer
# ---------------------------------------------------------------------------

def optimize(
    fraction: int = 12,
    fsam: int = 96000,
    sbit: int = 24,
    ilowfreq: int = 4,
    nch: int = 1,
    attvol: float = -0.25,
    dur: int = 1,
    maxiter: int = 100000,
    last_best_iter: int = 1,
    rd: str = "RD",
    ext: str = ".flac",
    seed: int | None = None,
    output_dir: str = ".",
) -> None:
    """
    Run the Monte Carlo crest-factor minimization.

    Parameters
    ----------
    fraction : int
        Octave subdivisions (3, 6, or 12).
    fsam : int
        Sampling frequency (Hz).
    sbit : int
        Bit depth (16, 24, or 32).
    ilowfreq : int
        Index into the frequency-attenuation array to start from (1-indexed
        in MATLAB; we use 0-indexed here, so MATLAB iLowFreq=4 → Python 3).
    nch : int
        Number of channels (1 or 2).
    attvol : float
        Peak level attenuation (dB).
    dur : int
        Duration of the preview signal (seconds).
    maxiter : int
        Maximum number of iterations.
    last_best_iter : int
        Starting iteration number (for resuming).
    rd : str
        Rounding mode: 'RD' or 'NO'.
    ext : str
        Audio file extension ('.flac' or '.wav').
    seed : int or None
        Random seed (None = no fixed seed, matches MATLAB's rng('shuffle')).
    output_dir : str
        Directory for output files.
    """
    # Adjust iteration count (MATLAB: MaxIter = MaxIter + LastBestIter - 1)
    maxiter = maxiter + last_best_iter - 1

    # Frequency limits
    fllow = 20.0
    flhig = fsam / 2.0 * 0.9  # 90% of Nyquist

    # Load attenuation data
    FrqPriLst_full, FrqAttLst_full = load_attenuation(fraction, fsam)

    # MATLAB uses 1-indexed: FrqPriLst = mat_data(iLowFreq:lll, 1)
    # Python is 0-indexed, so we slice from (ilowfreq - 1)
    slice_start = ilowfreq - 1  # MATLAB iLowFreq=4 → Python index 3
    FrqPriLst = FrqPriLst_full[slice_start:]
    FrqAttLst = FrqAttLst_full[slice_start:]

    FrqPriLen = len(FrqPriLst)
    lfl = int(FrqPriLst[0])  # lowest frequency in the sliced list

    # Initial crest factor threshold
    cfact0 = np.full(nch, 18.0)

    print(
        f"Optimizer started: Fraction={fraction}, Fs={fsam}, "
        f"Sbit={sbit}, Nch={nch}, iLowFreq={ilowfreq}, "
        f"Frequencies={FrqPriLen}, Range={fllow:.0f}-{flhig:.0f} Hz"
    )
    print(f"Slice start index (MATLAB iLowFreq={ilowfreq}): "
          f"LFL={lfl} Hz, Nfr={FrqPriLen}")
    print(f"Initial cfact threshold: {cfact0[0]:.4f} dB")
    print(f"Iterations: {last_best_iter} to {maxiter}")
    print()

    start_time = time.time()

    for i in range(last_best_iter, maxiter + 1):
        # Random phases: rand(N, 1) * pi → uniform in [0, π]
        PhiLst = np.random.rand(FrqPriLen) * np.pi

        # Synthesize waveform
        ycd = frq_lst_vol_att(
            FrqLst=FrqPriLst,
            PhiLst=PhiLst,
            VolLst=FrqAttLst,
            VolAtt=attvol,
            Rounded=rd,
            Dur=dur,
            Frs=fsam,
            Sab=sbit,
            NCh=nch,
        )

        # Compute crest factor
        cfact = crest_factor_dB(ycd, sbit)

        # Print progress
        print(
            f"iter {i:06d}: cfact0={cfact0[0]:10.4f} → "
            f"cfact={cfact[0]:10.4f} dB",
            end="\r",
        )

        # If this is better, save
        if cfact[0] < cfact0[0]:
            for j in range(nch):
                cfact0[j] = cfact[j]

            # Save phase set as .mat (compatible with MATLAB)
            phi_filename = format_phase_filename(
                nch=nch,
                fraction=fraction,
                lfl=lfl,
                fsam=fsam,
                sbit=sbit,
                fllow=int(fllow),
                flhig=int(flhig),
                nfr=FrqPriLen,
                iteration=i,
                cfact=cfact0[0],
            )
            phi_path = os.path.join(output_dir, phi_filename)
            sio.savemat(phi_path, {
                "Fraction": np.int32(fraction),
                "iLowFreq": np.int32(ilowfreq),
                "Fsam": np.int32(fsam),
                "Sbit": np.int32(sbit),
                "FrqPriLst": FrqPriLst[:, np.newaxis].astype(np.float64),
                "PhiLst": PhiLst[:, np.newaxis].astype(np.float64),
                "cfact0": cfact0.astype(np.float64),
            })

            # Save preview audio
            try:
                import soundfile as sf

                audio_filename = format_audio_filename(
                    nch=nch,
                    fraction=fraction,
                    lfl=lfl,
                    fllow=int(fllow),
                    flhig=int(flhig),
                    nfr=FrqPriLen,
                    fsam=fsam,
                    sbit=sbit,
                    dur=dur,
                    attvol=attvol,
                    iteration=i,
                    cfact=cfact0[0],
                    rd=rd,
                    ext=ext,
                )
                audio_path = os.path.join(output_dir, audio_filename)

                # For FLAC, soundfile wants int32 for 24-bit
                sf.write(audio_path, ycd, fsam, subtype=f"PCM_{sbit}")
            except ImportError:
                print("\n  (soundfile not installed — skipping audio output)")

            print(f"\n  *** NEW BEST: iter={i}, cfact={cfact0[0]:.4f} dB ***")
            print(f"      Phase file: {phi_filename}")

    elapsed = time.time() - start_time
    print(f"\nOptimizer complete in {elapsed:.1f}s")
    print(f"Best crest factor: {cfact0[0]:.4f} dB")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Monte Carlo crest-factor minimization for multitone test signals"
    )
    parser.add_argument("--fraction", type=int, default=12, choices=[3, 6, 12],
                        help="Octave subdivisions (3, 6, or 12)")
    parser.add_argument("--fsam", type=int, default=96000,
                        choices=[44100, 48000, 88200, 96000, 176400, 192000],
                        help="Sampling frequency (Hz)")
    parser.add_argument("--sbit", type=int, default=24, choices=[16, 24, 32],
                        help="Bit depth")
    parser.add_argument("--ilowfreq", type=int, default=4,
                        help="Low frequency index (1-indexed, MATLAB style)")
    parser.add_argument("--nch", type=int, default=1, choices=[1, 2],
                        help="Number of channels")
    parser.add_argument("--attvol", type=float, default=-0.25,
                        help="Peak level attenuation (dB)")
    parser.add_argument("--dur", type=int, default=1,
                        help="Preview duration (seconds)")
    parser.add_argument("--maxiter", type=int, default=100000,
                        help="Maximum iterations")
    parser.add_argument("--last-best-iter", type=int, default=1,
                        help="Starting iteration (for resuming)")
    parser.add_argument("--rd", type=str, default="RD", choices=["RD", "NO"],
                        help="Rounding mode")
    parser.add_argument("--ext", type=str, default=".flac",
                        help="Audio file extension")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed (None = shuffle)")
    parser.add_argument("--output-dir", type=str, default=".",
                        help="Output directory")

    args = parser.parse_args()

    if args.seed is not None:
        np.random.seed(args.seed)

    optimize(
        fraction=args.fraction,
        fsam=args.fsam,
        sbit=args.sbit,
        ilowfreq=args.ilowfreq,
        nch=args.nch,
        attvol=args.attvol,
        dur=args.dur,
        maxiter=args.maxiter,
        last_best_iter=args.last_best_iter,
        rd=args.rd,
        ext=args.ext,
        seed=args.seed,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
