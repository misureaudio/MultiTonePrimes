#!/usr/bin/env python3
"""
Port of PhiLstMuTNewSig.m

Production signal generator: loads an optimized phase set from a .mat file
and synthesizes a long-duration multitone audio file.

Usage:
    python -m multitone.producer PHASE_MAT_FILE [--dur DUR] [--nch NCH] [--ext EXT]

Examples:
    # Generate 30-minute stereo FLAC from a phase file
    python -m multitone.producer \\
        "PhiLstMuTNewMin[Nch 1][Frac 03][LFL 043][048000-24][00020-21600][Nfr 027][060159]-[ 8.4655].mat" \\
        --dur 1800 --nch 2

    # Quick 1-second mono WAV for verification
    python -m multitone.producer phase_file.mat --dur 1 --nch 1 --ext .wav
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import scipy.io as sio

from multitone.synthesize import crest_factor_dB, frq_lst_vol_att

# ---------------------------------------------------------------------------
# Attenuation data loading (same logic as optimizer)
# ---------------------------------------------------------------------------

ATTEN_DATA = {
    3: "fr03pri384k.mat",
    6: "fr06pri384k.mat",
    12: "fr12pri384k.mat",
}

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
    Load the full frequency-attenuation lookup table (no iLowFreq slicing —
    the producer uses the complete frequency range).

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
    return data[:, 0], data[:, 1]


# ---------------------------------------------------------------------------
# File name formatting
# ---------------------------------------------------------------------------

def format_audio_filename(
    nch: int,
    fraction: int,
    fllow: int,
    flhig: int,
    nfr: int,
    fsam: int,
    sbit: int,
    dur: int,
    attvol: float,
    cfact0: float,
    rd: str,
    ext: str,
) -> str:
    """Generate the output audio file name."""
    return (
        f"PrimeToneNewPhi[Nch {nch}][Frac {fraction:03d}]"
        f"[{fllow:05d}-{flhig:05d}][Nfr {nfr:03d}]"
        f"-[{fsam}-{sbit}]-[{dur}s]-[{attvol:5.2f}dB]"
        f"-[{cfact0:7.4f}]-[{rd}]{ext}"
    )


# ---------------------------------------------------------------------------
# Main producer
# ---------------------------------------------------------------------------

def produce(
    phase_mat_path: str,
    dur: int = 1800,
    nch: int = 2,
    attvol: float = -0.25,
    rd: str = "RD",
    ext: str = ".flac",
) -> None:
    """
    Load an optimized phase set and synthesize the production audio file.

    Parameters
    ----------
    phase_mat_path : str
        Path to the .mat file produced by the optimizer.
    dur : int
        Duration of the output signal (seconds).
    nch : int
        Number of channels (1 or 2).
    attvol : float
        Peak level attenuation (dB).
    rd : str
        Rounding mode: 'RD' or 'NO'.
    ext : str
        Audio file extension ('.flac' or '.wav').
    """
    # Load phase file
    if not os.path.exists(phase_mat_path):
        print(f"ERROR: Phase file not found: {phase_mat_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading phase file: {phase_mat_path}")
    philstws = sio.loadmat(phase_mat_path)

    # Extract parameters from the phase file
    FrqPriLst = philstws["FrqPriLst"].flatten()
    PhiLst = philstws["PhiLst"].flatten()
    # MATLAB scalars saved with savemat come back as 2D (1,1) arrays
    Fraction = int(philstws["Fraction"].item())
    Fsam = int(philstws["Fsam"].item())
    Sbit = int(philstws["Sbit"].item())
    CFact0 = philstws["cfact0"].flatten()

    frqprilen = len(FrqPriLst)
    fllow = int(FrqPriLst[0])
    flhig = int(FrqPriLst[-1])

    print(f"  Fraction: {Fraction}")
    print(f"  Sampling rate: {Fsam} Hz")
    print(f"  Bit depth: {Sbit}-bit")
    print(f"  Frequencies: {frqprilen} (range: {fllow} Hz – {flhig} Hz)")
    print(f"  Phase count: {len(PhiLst)}")
    print(f"  Recorded cfact: {CFact0[0]:.4f} dB")
    print()

    # Load attenuation data (full range, no slicing)
    FrqPriLst_full, FrqAttLst = load_attenuation(Fraction, Fsam)

    # The producer uses the FULL attenuation array, not sliced
    # But the phase file has a specific frequency list — we need to match
    # the attenuation values to the frequencies in the phase file.
    #
    # The MATLAB code loads the full attenuation array and passes it to
    # FrqLstVolAtt along with philstws.FrqPriLst. The FrqLstVolAtt function
    # iterates over FrqLst (which comes from the phase file) and uses
    # VolLst (the attenuation) index-by-index.
    #
    # So the attenuation list must match the phase file's frequency list.
    # In the MATLAB code, FrqAttLst is loaded from the full array but the
    # iteration is over philstws.FrqPriLst which has the same length as
    # FrqAttLst only if both are the same array.
    #
    # Looking at the MATLAB producer more carefully:
    #   FrqPriLst = fr12frqprilim096k(:,1);   % full array
    #   FrqAttLst = fr12frqprilim096k(:,2);   % full array
    #   [ycd,...] = FrqLstVolAtt(philstws.FrqPriLst, philstws.PhiLst, FrqAttLst, ...)
    #
    # The phase file's FrqPriLst is a SUBSET of the full array (sliced from
    # iLowFreq). But FrqAttLst is the FULL array. This means the MATLAB code
    # passes mismatched lengths — FrqPriLst from the phase file vs FrqAttLst
    # from the full array.
    #
    # Wait — let me re-read. The phase file saves FrqPriLst which was the
    # SLICED version. The producer loads the FULL FrqAttLst. In the call to
    # FrqLstVolAtt, it passes philstws.FrqPriLst (sliced) and FrqAttLst (full).
    # This would be a length mismatch in MATLAB...
    #
    # Actually, looking at the optimizer's save:
    #   save(..., 'FrqPriLst', ...)   — this is the SLICED FrqPriLst
    # And the producer loads:
    #   FrqPriLst = fr12frqprilim096k(:,1);  — FULL array
    #   FrqAttLst = fr12frqprilim096k(:,2);  — FULL array
    #   FrqLstVolAtt(philstws.FrqPriLst, philstws.PhiLst, FrqAttLst, ...)
    #
    # So philstws.FrqPriLst (sliced, from the .mat) is used for frequencies,
    # but FrqAttLst (full, from the attenuation .mat) is used for attenuation.
    # These have DIFFERENT lengths.
    #
    # This would cause a dimension mismatch in MATLAB. Let me check if there's
    # an alternative interpretation...
    #
    # Actually, I think the intent is that the attenuation array should match
    # the frequency list. The safest approach: build a frequency→attenuation
    # lookup from the full array, then extract the attenuation values for
    # the frequencies in the phase file.

    # Build frequency → attenuation lookup from the full attenuation array
    att_lookup = dict(zip(FrqPriLst_full, FrqAttLst))

    # Extract attenuation values for the frequencies in the phase file
    FrqAttLst_matched = np.array([att_lookup[f] for f in FrqPriLst])

    if len(FrqAttLst_matched) != len(FrqPriLst):
        print(f"ERROR: Length mismatch: FrqPriLst={len(FrqPriLst)}, "
              f"FrqAttLst_matched={len(FrqAttLst_matched)}", file=sys.stderr)
        sys.exit(1)

    print(f"  Attenuation matched: {len(FrqAttLst_matched)} values")
    print(f"  Synthesizing {dur}s signal at {Fsam} Hz ({nch} channels)...")

    # Synthesize
    ycd = frq_lst_vol_att(
        FrqLst=FrqPriLst,
        PhiLst=PhiLst,
        VolLst=FrqAttLst_matched,
        VolAtt=attvol,
        Rounded=rd,
        Dur=dur,
        Frs=Fsam,
        Sab=Sbit,
        NCh=nch,
    )

    # Compute and display crest factor
    cfact = crest_factor_dB(ycd, Sbit)
    print(f"  Crest factor: L={cfact[0]:.4f} dB", end="")
    if nch > 1:
        print(f"  R={cfact[1]:.4f} dB", end="")
    print()

    # Write audio file
    try:
        import soundfile as sf

        audio_filename = format_audio_filename(
            nch=nch,
            fraction=Fraction,
            fllow=fllow,
            flhig=flhig,
            nfr=frqprilen,
            fsam=Fsam,
            sbit=Sbit,
            dur=dur,
            attvol=attvol,
            cfact0=CFact0[0],
            rd=rd,
            ext=ext,
        )
        audio_path = os.path.join(os.getcwd(), audio_filename)

        sf.write(audio_path, ycd, Fsam, subtype=f"PCM_{Sbit}")
        print(f"  Written: {audio_filename}")
    except ImportError:
        print("\n  (soundfile not installed — skipping audio output)")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Produce multitone audio signal from an optimized phase file"
    )
    parser.add_argument("phase_mat", type=str,
                        help="Path to the phase .mat file from the optimizer")
    parser.add_argument("--dur", type=int, default=1800,
                        help="Duration in seconds (default: 1800 = 30 min)")
    parser.add_argument("--nch", type=int, default=2, choices=[1, 2],
                        help="Number of channels (default: 2)")
    parser.add_argument("--attvol", type=float, default=-0.25,
                        help="Peak level attenuation (dB)")
    parser.add_argument("--rd", type=str, default="RD", choices=["RD", "NO"],
                        help="Rounding mode")
    parser.add_argument("--ext", type=str, default=".flac",
                        help="Audio file extension")

    args = parser.parse_args()
    produce(args.phase_mat, args.dur, args.nch, args.attvol, args.rd, args.ext)


if __name__ == "__main__":
    main()
