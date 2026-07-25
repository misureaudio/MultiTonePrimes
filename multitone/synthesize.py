"""
Port of FrqLstVolAtt.m

Synthesizes multitone audio waveforms from frequency lists, phases, and
per-frequency attenuation values. Applies peak normalization and quantizes
to the target bit depth.

Key details (verified against MATLAB source):
  - Uses cos() (not sin) for each tone
  - Normalizes peak to full scale before applying overall attenuation
  - 24-bit audio stored as int32 with lower 8 bits zero-padded (×256)
  - Stereo = same signal on both channels
"""

from __future__ import annotations

import numpy as np


def frq_lst_vol_att(
    FrqLst: np.ndarray,
    PhiLst: np.ndarray,
    VolLst: np.ndarray,
    VolAtt: float,
    Rounded: str,
    Dur: int | float,
    Frs: int,
    Sab: int,
    NCh: int,
) -> np.ndarray:
    """
    Synthesize a multitone waveform.

    For each frequency f_k with phase φ_k and attenuation a_k (dB):

        ycd += 10^(a_k/20) · cos(2π · f_k · t + φ_k)

    After all frequencies are summed:
      1. Peak-normalize to full scale
      2. Apply overall peak attenuation (VolAtt dB)
      3. Quantize to the target bit depth

    Parameters
    ----------
    FrqLst : ndarray
        Array of frequencies (Hz).
    PhiLst : ndarray
        Array of phases (radians).
    VolLst : ndarray
        Per-frequency attenuation (dB).
    VolAtt : float
        Overall peak attenuation (dB).
    Rounded : str
        'RD' for round-to-nearest, 'NO' for truncate.
    Dur : int or float
        Duration in seconds.
    Frs : int
        Sampling frequency (Hz).
    Sab : int
        Bit depth: 16, 24, or 32.
    NCh : int
        Number of channels: 1 (mono) or 2 (stereo).

    Returns
    -------
    ycd : ndarray
        Quantized audio samples: shape (lenv, NCh).
        - 16-bit: int16
        - 24-bit: int32 (lower 8 bits zero-padded)
        - 32-bit: float64
    """
    # Validate sampling rate
    valid_frs = (44100, 48000, 88200, 96000, 176400, 192000)
    if Frs not in valid_frs:
        Frs = 44100

    # Validate bit depth
    if Sab not in (16, 24, 32):
        Sab = 24

    # Validate rounding mode
    if Rounded not in ("RD", "NO"):
        Rounded = "NO"

    lenv = Frs * int(Dur)
    twopi = 2.0 * np.pi

    # Initialize output buffer
    ycd = np.zeros((lenv, NCh), dtype=np.float64)

    # Time vector (MATLAB uses (i-1) for 1-indexed → 0-indexed in Python)
    t = np.arange(lenv, dtype=np.float64) / Frs

    # Accumulate cosines (vectorized — no inner loop over samples)
    for k in range(len(FrqLst)):
        f = FrqLst[k]
        phi = PhiLst[k]
        vs = 10.0 ** (VolLst[k] / 20.0)  # dB → linear amplitude

        y = vs * np.cos(twopi * f * t + phi)
        ycd += y[:, np.newaxis]  # broadcast to all channels

    # Apply peak attenuation after normalization
    vs = 10.0 ** (VolAtt / 20.0)

    if Sab in (16, 24):
        scale = 2**Sab
        scalediv2 = scale // 2 - 1  # e.g., 24-bit: 2^23 - 1 = 8388607
        ycdmax = np.max(np.abs(ycd))
        ycd = ycd / ycdmax * scalediv2 * vs
    else:
        # Sab == 32: no integer clipping, just scale
        ycdmax = np.max(np.abs(ycd))
        ycd = ycd / ycdmax * vs

    # Quantize to integer
    if Sab == 16:
        if Rounded == "RD":
            ycd = np.round(ycd).astype(np.int16)
        else:
            ycd = ycd.astype(np.int16)  # truncate toward zero

    elif Sab == 24:
        # 24-bit audio in int32 containers — lower 8 bits zero-padded
        if Rounded == "RD":
            ycd = (np.round(ycd) * 256).astype(np.int32)
        else:
            ycd = (ycd * 256).astype(np.int32)

    # Sab == 32: leave as float64 (MATLAB also does nothing special)

    return ycd


def crest_factor_dB(ycd: np.ndarray, Sab: int) -> np.ndarray:
    """
    Compute crest factor in dB for each channel.

    Matches the MATLAB formula:
        cfact = 20 * log10(peak2rms(ycd / 2^Sab))

    Parameters
    ----------
    ycd : ndarray
        Quantized audio samples, shape (lenv, NCh).
    Sab : int
        Bit depth used for normalization (16, 24, or 32).

    Returns
    -------
    cfact : ndarray
        Crest factor in dB per channel.
    """
    ycd_norm = ycd.astype(np.float64) / (2**Sab)
    peak = np.max(np.abs(ycd_norm), axis=0)
    rms = np.sqrt(np.mean(ycd_norm**2, axis=0))
    return 20.0 * np.log10(peak / rms)
