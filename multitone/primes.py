"""
Port of MuTPrimes.m and FrqOctFraction.m

Generates prime-based multitone frequency lists for audio test signals.
Frequencies are derived by:
  1. Linearly subdividing each octave (octave 4 through 18) into `fraction` parts
  2. For each subdivision, taking the largest prime ≤ that frequency
  3. Deduplicating and filtering to the desired frequency range
"""

from __future__ import annotations

import numpy as np
from sympy import primerange


def frq_oct_fraction(oct0: int, oct1: int, fraction: int) -> tuple[np.ndarray, int]:
    """
    Generate linearly-subdivided frequencies within octave bands.

    For each octave i (where 2^i Hz is the octave floor) and subdivision j
    out of `fraction`:

        f = 2^i + (2^(i+1) - 2^i) / fraction × (j - 1)

    Parameters
    ----------
    oct0 : int
        Starting octave (e.g. 4 → 16 Hz).
    oct1 : int
        Ending octave (e.g. 18 → 262144 Hz).
    fraction : int
        Number of subdivisions per octave (3, 6, or 12).

    Returns
    -------
    frq_lst : ndarray
        Array of rounded frequencies (length = (oct1 - oct0 + 1) * fraction).
    frq_len : int
        Length of the array.
    """
    frq_len = (oct1 - oct0 + 1) * fraction
    frq_lst = np.empty(frq_len, dtype=np.int32)
    k = 0
    for i in range(oct0, oct1 + 1):
        oct_low = 2.0 ** i
        oct_high = 2.0 ** (i + 1)
        step = (oct_high - oct_low) / fraction
        for j in range(fraction):
            f = oct_low + step * j
            frq_lst[k] = int(round(f))
            k += 1
    return frq_lst, frq_len


def mut_primes(
    fraction: int, frq_lim_low: float, frq_lim_high: float
) -> tuple[np.ndarray, int]:
    """
    Generate prime-based multitone frequency list.

    For each frequency from FrqOctFraction, takes the largest prime ≤ that
    frequency, deduplicates, and filters to [frq_lim_low, frq_lim_high).

    Parameters
    ----------
    fraction : int
        Octave subdivisions (3, 6, or 12).
    frq_lim_low : float
        Lower frequency limit (Hz).
    frq_lim_high : float
        Upper frequency limit (Hz).

    Returns
    -------
    frq_pri_lim : ndarray
        Filtered list of distinct prime frequencies.
    frq_pri_len : int
        Length of the filtered list.
    """
    frq_lst, frq_len = frq_oct_fraction(4, 18, fraction)

    # For each raw frequency, find the largest prime ≤ that frequency
    frq_pri = np.empty(frq_len, dtype=np.int32)
    for i in range(frq_len):
        # max(primes(frq_lst[i])) → largest prime ≤ frq_lst[i]
        frq_pri[i] = int(max(primerange(2, int(frq_lst[i]) + 1)))

    # Deduplicate and filter to frequency range
    frq_pri_unique = np.unique(frq_pri)
    frq_pri_lim = frq_pri_unique[
        (frq_pri_unique > frq_lim_low) & (frq_pri_unique < frq_lim_high)
    ]

    return frq_pri_lim, len(frq_pri_lim)
