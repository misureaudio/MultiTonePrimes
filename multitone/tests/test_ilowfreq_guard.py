"""Regression tests for the --ilowfreq range guard.

These tests exercise ONLY the validation helper (validate_ilowfreq) — a pure
range check with no signal math. They deliberately do not import or exercise
the synthesis / crest-factor code paths, so the audio math stays untouched.
"""

import pytest

from multitone.optimizer import validate_ilowfreq


@pytest.mark.parametrize("bad", [0, -1, -100, 122, 10_000])
def test_out_of_range_exits(bad):
    with pytest.raises(SystemExit) as exc:
        validate_ilowfreq(bad, n_freqs=121, fraction=12, fsam=96000)
    assert exc.value.code == 1


@pytest.mark.parametrize("good", [1, 4, 60, 121])
def test_in_range_passes(good):
    # Single tone (ilowfreq == n_freqs) is intentionally accepted.
    validate_ilowfreq(good, n_freqs=121, fraction=12, fsam=96000)  # no exception
