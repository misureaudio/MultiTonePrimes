"""Read a multitone .flac/.wav (stream metadata + PCM, channel by channel),
plot the waveform, and estimate the time spent on each 8-bit quantization
level. Sample rate / bit depth / channel count come from the stream header,
never from the filename.

Usage:
    env -u PYTHONPATH .venv/Scripts/python -m multitone.analyze_multitone [path]
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

SUPPORTED_SUBTYPES = {"PCM_16": 16, "PCM_24": 24}
VALID_FS = (44100, 48000, 88200, 96000, 176400, 192000, 352800, 384000)


@dataclass(frozen=True)
class AudioSignal:
    path: Path
    samplerate: int
    channels: int
    frames: int
    duration: float
    subtype: str
    bits: int                        # true bit depth from the stream (16 or 24)
    raw: np.ndarray                  # int64, shape (frames, channels)

    def channel(self, c: int) -> np.ndarray:
        return self.raw[:, c]


def load_audio(path) -> AudioSignal:
    path = Path(path)
    if path.suffix.lower() not in (".flac", ".wav"):
        raise ValueError(
            f"unsupported extension {path.suffix!r} (need .flac or .wav)")
    info = sf.info(str(path))
    if info.subtype not in SUPPORTED_SUBTYPES:
        raise ValueError(
            f"unsupported subtype {info.subtype!r} (need PCM_16 or PCM_24)")
    if info.samplerate not in VALID_FS:
        raise ValueError(
            f"unsupported sample rate {info.samplerate} Hz "
            f"(need one of {VALID_FS})")
    bits = SUPPORTED_SUBTYPES[info.subtype]
    x, _ = sf.read(str(path), dtype="int32", always_2d=True)
    raw = (x >> (32 - bits)).astype(np.int64)   # left-justified s32 -> true value
    return AudioSignal(path=path, samplerate=info.samplerate,
                       channels=info.channels, frames=info.frames,
                       duration=float(info.duration), subtype=info.subtype,
                       bits=bits, raw=raw)


def quantize_8bit(m: np.ndarray, sab: int = 24) -> np.ndarray:
    """Map two's-complement samples to 8-bit mid-tread levels [-128, 127].

    q = round_even(m / 2^(sab-8)), computed in the integer domain (exact,
    round-half-to-even — matches the generator's np.round / IEEE 754),
    clipped to the 8-bit range (defensive).
    """
    if sab not in (16, 24):
        raise ValueError(f"unsupported bit depth: {sab}")
    m = np.ascontiguousarray(m, dtype=np.int64)
    d = 1 << (sab - 8)                 # step in sample units: 256 / 65536
    k = m // d                         # floor division (m may be negative)
    r = m - k * d                      # 0 <= r < d
    adj = (2 * r > d) | ((2 * r == d) & (k % 2 != 0))   # ties -> even level
    return np.clip(k + adj, -128, 127).astype(np.int8)


def level_occupancy(q: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """counts[k] = number of samples on level k-128; (int64[256], int8[256])."""
    counts = np.bincount(q.astype(np.int64) + 128, minlength=256)
    return counts, np.arange(-128, 128, dtype=np.int8)


def dwell_times(counts: np.ndarray, samplerate: int) -> np.ndarray:
    """t_k = N_k / F_s : estimated seconds spent on each level."""
    return counts.astype(np.float64) / float(samplerate)


def quant_error_stats(m: np.ndarray, q: np.ndarray, sab: int = 24) -> dict:
    scale = float(1 << (sab - 1))
    x = m.astype(np.float64) / scale               # exact (power-of-two scaling)
    e = x - q.astype(np.float64) / 128.0           # level * D, D = 2^-7
    return {
        "max_abs_err": float(np.abs(e).max()),
        "half_step": 1.0 / 256.0,                  # D/2, D = 2^-7
        "sqnr_db": float(10.0 * np.log10(np.sum(x * x) / np.sum(e * e))),
    }


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def plot_waveform(sig: AudioSignal, q_by_channel: dict, out_dir) -> Path:
    plt = _plt()
    t = np.arange(sig.frames) / sig.samplerate
    scale = 2.0 ** (sig.bits - 1)
    D = 2.0 / 256.0
    nzm = min(384, sig.frames)                    # zoom window (4 ms @ 96 kHz)
    zoom_ms = nzm / sig.samplerate * 1e3
    fig, axes = plt.subplots(2 * sig.channels, 1,
                             figsize=(11, 2.2 * sig.channels), sharex=True)
    axes = np.atleast_1d(axes)
    for c in range(sig.channels):
        full = sig.channel(c) / scale
        axes[2 * c].plot(t, full, lw=0.3, color="navy")
        axes[2 * c].set_ylabel(f"ch{c} full")
        axes[2 * c].set_ylim(-1.05, 1.05)
        axes[2 * c + 1].plot(t[:nzm], full[:nzm], lw=0.4,
                             color="navy", label="original")
        axes[2 * c + 1].step(t[:nzm], q_by_channel[c][:nzm] * D,
                             where="mid", lw=0.9, color="crimson",
                             label="8-bit quantized")
        axes[2 * c + 1].set_ylabel(f"ch{c} {zoom_ms:.1f} ms zoom")
        axes[2 * c + 1].legend(loc="upper right", fontsize=8)
    axes[-1].set_xlabel("time (s)")
    fig.suptitle(f"{sig.path.name} — {sig.samplerate} Hz, "
                 f"{sig.frames} fr, {sig.channels} ch, {sig.bits}-bit")
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    out = Path(out_dir) / "waveform.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def plot_occupancy(counts: np.ndarray, levels: np.ndarray, samplerate: int,
                   channel: int, out_dir) -> Path:
    plt = _plt()
    t = dwell_times(counts, samplerate)
    p = counts / counts.sum()
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.bar(levels, t, width=1.0, color="steelblue")
    ax.set_xlabel("8-bit level $k$")
    ax.set_ylabel("time $t_k$ (s)")
    ax.set_title(f"Level occupancy, ch{channel}: {int(counts.sum())} samples, "
                 f"{int(np.count_nonzero(counts))}/256 levels occupied")
    ax2 = ax.twinx()
    ax2.plot(levels, p * 128.0, "r.", ms=3,
             label=r"$\hat p_k / D$ (pdf estimate)")
    ax2.set_ylabel(r"$\hat p_k / D$ (pdf estimate)")
    ax2.legend(loc="upper right", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = Path(out_dir) / f"occupancy_ch{channel}.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


DEFAULT_PATH = Path(__file__).resolve().parent / "audio" / (
    "PrimeToneNewPhi[Nch 1][Frac 03][LFL 043][00020-43200]"
    "[Nfr 031]-[96000-24]-[1s]-[-0.25dB]-[057923]-[ 8.7282]-[RD].flac")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="FLAC/WAV 8-bit level-occupancy analyzer "
                    "(Fs/bits/channels from stream metadata)")
    ap.add_argument("path", nargs="?", default=str(DEFAULT_PATH))
    ap.add_argument("--out",
                    default=str(Path(__file__).resolve().parent / "analysis_out"))
    ap.add_argument("--no-plot", action="store_true")
    a = ap.parse_args(argv)

    sig = load_audio(Path(a.path))
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"file: {sig.path.name}")
    print(f"  {sig.samplerate} Hz, {sig.frames} frames, {sig.channels} ch, "
          f"{sig.subtype}, {sig.duration:.6f} s")

    q_all = {}
    for c in range(sig.channels):
        m = sig.channel(c)
        q = quantize_8bit(m, sig.bits)
        q_all[c] = q
        counts, levels = level_occupancy(q)
        st = quant_error_stats(m, q, sig.bits)
        scale = float(2.0 ** (sig.bits - 1))
        peak = m.max() / scale
        rms = float(np.sqrt(np.mean((m / scale) ** 2)))
        occ = np.nonzero(counts)[0]
        print(f"channel {c}: peak {20*np.log10(peak):+.3f} dBFS, "
              f"rms {20*np.log10(rms):+.2f} dBFS, "
              f"levels {occ.size}/256 [{int(levels[occ[0]])}, "
              f"{int(levels[occ[-1]])}], SQNR {st['sqnr_db']:.2f} dB, "
              f"max|e| {st['max_abs_err']:.9f} (<= {st['half_step']:.9f})")
        top = sorted(np.argsort(counts)[::-1][:10])
        print("  top-10 levels (level, samples, ms, %):")
        for k in top:
            print(f"    {int(levels[k]):+4d}  {counts[k]:6d}  "
                  f"{dwell_times(counts, sig.samplerate)[k]*1e3:8.3f}  "
                  f"{counts[k]/m.size*100:6.3f}")
        np.savetxt(out_dir / f"occupancy_ch{c}.csv",
                   np.column_stack([levels, counts,
                                    dwell_times(counts, sig.samplerate)]),
                   delimiter=",", header="level,samples,seconds", comments="",
                   fmt=["%d", "%d", "%.10f"])
    if not a.no_plot:
        print(f"plot: {plot_waveform(sig, q_all, out_dir)}")
        for c in range(sig.channels):
            counts, levels = level_occupancy(q_all[c])
            print(f"plot: {plot_occupancy(counts, levels, sig.samplerate, c, out_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
