#!/usr/bin/env python3
"""
CuPy-accelerated batched Monte Carlo crest-factor optimizer.
Implements a GEMM-based trigonometric phase evaluation to maximize GPU throughput.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import scipy.io as sio

# Fallbacks and reuse from the existing CPU implementation
from multitone.optimizer import (
    load_attenuation,
    format_phase_filename,
    format_audio_filename,
    optimize as optimize_cpu
)
from multitone.synthesize import crest_factor_dB, frq_lst_vol_att

def optimize_gpu(
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
    batch_size: int = 1024,
) -> None:
    # --- 1. GPU Fallback Mechanism ---
    try:
        import cupy as cp
    except ImportError:
        print("WARNING: CuPy not found or GPU unavailable. Falling back to CPU...")
        optimize_cpu(
            fraction=fraction, fsam=fsam, sbit=sbit, ilowfreq=ilowfreq,
            nch=nch, attvol=attvol, dur=dur, maxiter=maxiter,
            last_best_iter=last_best_iter, rd=rd, ext=ext, seed=seed,
            output_dir=output_dir
        )
        return

    if seed is not None:
        np.random.seed(seed)
        cp.random.seed(seed)

    # --- 2. Setup and Metadata ---
    total_iters = maxiter
    maxiter = maxiter + last_best_iter - 1

    fllow = 20.0
    flhig = fsam / 2.0 * 0.9

    FrqPriLst_full, FrqAttLst_full = load_attenuation(fraction, fsam)
    slice_start = ilowfreq - 1
    FrqPriLst = FrqPriLst_full[slice_start:]
    FrqAttLst = FrqAttLst_full[slice_start:]

    FrqPriLen = len(FrqPriLst)
    lfl = int(FrqPriLst[0])
    
    # Track threshold using CPU-equivalent floats
    cfact0 = np.full(nch, 18.0)

    print(f"GPU Optimizer started: Fraction={fraction}, Fs={fsam}, Sbit={sbit}, Nch={nch}")
    print(f"Slice start index: LFL={lfl} Hz, Nfr={FrqPriLen}")
    print(f"Batch Size: {batch_size}, Precision: float32 (GPU) / float64 (CPU strict check)")
    print(f"Iterations: {last_best_iter} to {maxiter}\n")

    start_time = time.time()
    '''
    # --- 3. GPU Precomputation (The GEMM Approach) ---
    L = fsam * dur
    t_gpu = cp.arange(L, dtype=cp.float32) / fsam
    frq_gpu = cp.asarray(FrqPriLst, dtype=cp.float32)
    vol_gpu = cp.asarray(FrqAttLst, dtype=cp.float32)

    # Linear amplitude
    vs_gpu = 10.0 ** (vol_gpu / 20.0)

    # Precompute cos(2*pi*f*t) and sin(2*pi*f*t) matrices: shape (N, L)
    A = 2.0 * cp.pi * frq_gpu[:, None] * t_gpu[None, :]
    C = cp.cos(A)
    S = cp.sin(A)
    
    del A  # Free up memory immediately
    cp.get_default_memory_pool().free_all_blocks()
    # ------------------------------------------------
    '''
    # --- 3. GPU Precomputation (Fixed for Phase Accuracy) ---
    L = fsam * dur
    
    # 1. Generate t, frq, and A in strict float64 to prevent large-angle precision loss
    t_gpu_64 = cp.arange(L, dtype=cp.float64) / fsam
    frq_gpu_64 = cp.asarray(FrqPriLst, dtype=cp.float64)
    
    A_64 = 2.0 * cp.pi * frq_gpu_64[:, None] * t_gpu_64[None, :]
    
    # 2. Evaluate trigonometry in float64 so phase wraps flawlessly
    C_64 = cp.cos(A_64)
    S_64 = cp.sin(A_64)
    
    # 3. Cast the resulting perfect waves to float32 for high-speed GEMM
    # (Amplitude precision is ~10^-7, which is completely fine for ranking CF)
    C = cp.asarray(C_64, dtype=cp.float32)
    S = cp.asarray(S_64, dtype=cp.float32)
    
    vol_gpu = cp.asarray(FrqAttLst, dtype=cp.float32)
    vs_gpu = 10.0 ** (vol_gpu / 20.0)

    # Free the heavy float64 matrices to keep VRAM clean
    del t_gpu_64, frq_gpu_64, A_64, C_64, S_64
    cp.get_default_memory_pool().free_all_blocks()
    # ------------------------------------------------

    current_iter = last_best_iter

    while current_iter <= maxiter:
        current_b = min(batch_size, maxiter - current_iter + 1)

        # Generate batch of random phases (B, N)
        PhiLst = cp.random.uniform(0, cp.pi, size=(current_b, FrqPriLen), dtype=cp.float32)

        # U = vs * cos(Phi), V = vs * sin(Phi) : shape (B, N)
        U = vs_gpu[None, :] * cp.cos(PhiLst)
        V = vs_gpu[None, :] * cp.sin(PhiLst)

        # GEMM Magic: Y = U @ C - V @ S -> shape (B, L)
        ycd_batch = cp.matmul(U, C) - cp.matmul(V, S)

        # Scale-invariant batched crest factor computation
        peak = cp.max(cp.abs(ycd_batch), axis=1)
        rms = cp.sqrt(cp.mean(ycd_batch**2, axis=1))
        cfact_batch = 20.0 * cp.log10(peak / rms)

        best_idx = int(cp.argmin(cfact_batch).item())
        best_cfact_batch = float(cfact_batch[best_idx].item())

        print(
            f"iter {current_iter + current_b - 1:06d}: cfact0={cfact0[0]:10.4f} dB "
            f"[batch best: {best_cfact_batch:7.4f} dB]",
            end="\r",
        )

        # --- 4. Strict CPU Evaluation for Winners ---
        # If GPU float32 raw unquantized score beats the current threshold
        if best_cfact_batch < cfact0[0]:
            best_phi = PhiLst[best_idx].get()
            iter_of_best = current_iter + best_idx

            # Synthesize precise CPU version (with normalization and quantization)
            ycd = frq_lst_vol_att(
                FrqLst=FrqPriLst, PhiLst=best_phi, VolLst=FrqAttLst, VolAtt=attvol,
                Rounded=rd, Dur=dur, Frs=fsam, Sab=sbit, NCh=nch,
            )
            cfact = crest_factor_dB(ycd, sbit)

            # Strict check using quantized double-precision crest factor
            if cfact[0] < cfact0[0]:
                for j in range(nch):
                    cfact0[j] = cfact[j]

                # Save Phase Data
                phi_filename = format_phase_filename(
                    nch=nch, fraction=fraction, lfl=lfl, fsam=fsam, sbit=sbit,
                    fllow=int(fllow), flhig=int(flhig), nfr=FrqPriLen,
                    iteration=iter_of_best, cfact=cfact0[0]
                )
                sio.savemat(os.path.join(output_dir, phi_filename), {
                    "Fraction": np.int32(fraction),
                    "iLowFreq": np.int32(ilowfreq),
                    "Fsam": np.int32(fsam),
                    "Sbit": np.int32(sbit),
                    "FrqPriLst": FrqPriLst[:, np.newaxis].astype(np.float64),
                    "PhiLst": best_phi[:, np.newaxis].astype(np.float64),
                    "cfact0": cfact0.astype(np.float64),
                })

                # Save Audio Data
                try:
                    import soundfile as sf
                    audio_filename = format_audio_filename(
                        nch=nch, fraction=fraction, lfl=lfl, fllow=int(fllow),
                        flhig=int(flhig), nfr=FrqPriLen, fsam=fsam, sbit=sbit,
                        dur=dur, attvol=attvol, iteration=iter_of_best,
                        cfact=cfact0[0], rd=rd, ext=ext
                    )
                    sf.write(os.path.join(output_dir, audio_filename), ycd, fsam, subtype=f"PCM_{sbit}")
                except ImportError:
                    pass

                print(f"\n  *** NEW BEST: iter={iter_of_best:06d}, cfact={cfact0[0]:.4f} dB ***")
                print(f"      Phase file: {phi_filename}")

        current_iter += current_b

    elapsed = time.time() - start_time
    print(f"\nGPU Optimizer complete in {elapsed:.1f}s")
    print(f"Best crest factor: {cfact0[0]:.4f} dB")


def main() -> None:
    parser = argparse.ArgumentParser(description="CuPy Batched Monte Carlo crest-factor optimizer")
    parser.add_argument("--fraction", type=int, default=12, choices=[3, 6, 12])
    parser.add_argument("--fsam", type=int, default=96000, choices=[44100, 48000, 88200, 96000, 176400, 192000])
    parser.add_argument("--sbit", type=int, default=24, choices=[16, 24, 32])
    parser.add_argument("--ilowfreq", type=int, default=4)
    parser.add_argument("--nch", type=int, default=1, choices=[1, 2])
    parser.add_argument("--attvol", type=float, default=-0.25)
    parser.add_argument("--dur", type=int, default=1)
    parser.add_argument("--maxiter", type=int, default=100000)
    parser.add_argument("--last-best-iter", type=int, default=1)
    parser.add_argument("--rd", type=str, default="RD", choices=["RD", "NO"])
    parser.add_argument("--ext", type=str, default=".flac")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output-dir", type=str, default=".")
    
    # New GPU-specific arg
    parser.add_argument("--batch-size", type=int, default=1024,
                        help="Number of phase sets to evaluate simultaneously per GPU batch")

    args = parser.parse_args()

    optimize_gpu(
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
        batch_size=args.batch_size,
    )

if __name__ == "__main__":
    main()