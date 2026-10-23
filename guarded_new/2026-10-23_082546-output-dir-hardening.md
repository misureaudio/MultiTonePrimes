# `--output-dir` Hardening Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Make `--output-dir` fail fast with a clear error (or be auto-created) *before* the optimization loop, so bad output paths never cause mid-run tracebacks or lost best results — including MSYS-style path mistakes on Windows.

**Architecture:** One shared `resolve_output_dir()` helper in `multitone/optimizer.py` (the module both GPU scripts already import), called once at the top of each `optimize*()` function, adjacent to the existing `validate_ilowfreq` guard. The helper normalizes the path (`expanduser`/`expandvars`/`abspath`), auto-creates the directory, rejects unusable paths with `stderr` + `sys.exit(1)`, and on Windows **unconditionally** rejects drive-less absolute (MSYS/git-bash-style) paths.

**Tech Stack:** Python 3 stdlib (`os`) only — no new dependencies. pytest (9.1.1, already in the venv) for regression tests.

---

## Context / assumptions

- **Observed root cause (verified 2026-10-23):** passing `--output-dir /tmp/multitone_guard_probes` (MSYS style) from git-bash made native Python resolve it against the **CWD's drive** (`D:\tmp\...` — confirmed via `os.path.abspath`). The dir doesn't exist there, so `sio.savemat` raised a raw `FileNotFoundError` **mid-run, inside the "new best" branch** — the run died and the best phase set was lost.
- Current usage sites (`os.path.join(output_dir, ...)` → `savemat`/`sf.write`):
  - `multitone/optimizer.py:296, 327`
  - `multitone/optimizer_gpu.py:157, 176`
  - `multitone/optimizer_gpu_Cl1_Gv2.py:183, 202`
- Existing guard convention to follow: `validate_ilowfreq` (helper + `ERROR:` to stderr + `sys.exit(1)`, called at the top of each `optimize*()`).
- Current line anchors (post-ilowfreq-guard state):
  - `optimizer.py`: `validate_ilowfreq` def at line 95; `optimize()` at 166; `output_dir` docstring at 211; guard call at 224; `--output-dir` arg at 378.
  - `optimizer_gpu.py` / `optimizer_gpu_Cl1_Gv2.py`: import block ends line 23 (`validate_ilowfreq`); `optimize_gpu()` at 27; guard call at 68; `--output-dir` arg at 208 / 234.
- `D:\Source\hermes-dir` is **not a git repository** → no commit steps.
- Interpreter for all verification: `D:\Source\hermes-dir\.venv\Scripts\python.exe` (workspace venv, standing rule), run from `D:\Source\hermes-dir`.
- `multitone/tests/` exists with `test_ilowfreq_guard.py` (9 passing) — the new test file lives alongside it.
- **The signal math stays untouched** (`synthesize.py`, `producer.py`, `primes.py`, and the synthesis/crest-factor code in the optimizers). This change is validation/plumbing only.
- **No code path or test may require drive-root write permission** (user requirement, 2026-10-23) — this is why the MSYS rejection is unconditional; see design decisions.

## Design decisions (recorded for review)

- **Fail fast at startup** — the core win: a bad path costs milliseconds + exit 1 instead of a full run + traceback + lost result.
- **Auto-create missing dirs** (`os.makedirs(exist_ok=True)`) rather than requiring existence. Tradeoff: a typo'd path (`resutls`) now creates a junk dir instead of erroring. Chosen for convenience (matches common CLI-tool behavior); switching to require-exists later is a one-line deletion.
- **MSYS-style paths: reject unconditionally, do NOT auto-translate.** Auto-translation (`/d/foo` → `D:/foo`, `/tmp` → git-bash temp) is fragile — a real `C:\tmp` could exist, and the script is a plain Windows program that shouldn't assume its launcher. Rule: on Windows, a path starting with `/` (but not `//` = UNC) is **always** rejected with an actionable message. An earlier draft had an "honor if the resolved dir exists" exception; it is dropped because (1) it made behavior **CWD-dependent** — the same command resolves to `C:\tmp\...` or `D:\tmp\...` depending on the CWD's drive, (2) a user typing `/tmp/foo` almost always means the git-bash path even if `D:\tmp` exists, and (3) **testing that exception required creating a directory at a drive root**, which standard users can't do (violates the no-drive-root-access requirement). A user who genuinely has `C:\tmp` simply writes it natively as `C:/tmp` — the error message says so.
- **Writability via `os.access`** (not a probe file) — catches the common read-only case; ACL edge cases accepted.
- **Empty/whitespace input rejected** instead of silently meaning CWD.

---

### Task 1: Add `resolve_output_dir` helper to `multitone/optimizer.py`

**Objective:** Single source of truth for output-dir validation/normalization.

**Files:**
- Modify: `D:\Source\hermes-dir\multitone\optimizer.py` — insert after the `validate_ilowfreq` function (which ends at line 110), before the `# File name formatting` section

**Step 1: Add the helper**

```python
def resolve_output_dir(output_dir: str) -> str:
    """
    Validate and normalize the output directory; fail fast if unusable.

    - rejects empty/whitespace input
    - expands ~ and %ENV% variables, normalizes to an absolute path
    - on Windows, unconditionally rejects drive-less absolute paths
      (e.g. '/tmp/foo', MSYS/git-bash style) — they would otherwise
      silently resolve against the CWD's drive
    - creates the directory (and parents) if missing
    - exits 1 with a clear message if the path is a file, uncreatable,
      or not writable

    Returns the normalized absolute path.
    """
    raw = output_dir
    if not raw.strip():
        print("ERROR: --output-dir must not be empty", file=sys.stderr)
        sys.exit(1)

    path = os.path.abspath(os.path.expanduser(os.path.expandvars(raw)))

    # Windows: a leading '/' (not '//' = UNC) is MSYS/git-bash style
    # (/tmp/foo, /d/Source/out) — never a well-formed native Windows path.
    # Reject unconditionally: auto-translation is fragile, and an
    # "honor if it exists" exception would make behavior depend on the
    # CWD's drive (and its test would need drive-root write permission).
    # A real C:\tmp is written natively as 'C:/tmp'.
    if os.name == "nt" and raw.startswith("/") and not raw.startswith("//"):
        print(
            f"ERROR: --output-dir '{raw}' is not a valid Windows path: it "
            f"must start with a drive letter (e.g. 'D:/Source/out') or be "
            f"relative to the current directory. MSYS/git-bash paths like "
            f"'/tmp/...' are not translated (if you meant the git-bash temp "
            f"dir, that is "
            f"'C:/Users/{os.environ.get('USERNAME', '?')}/AppData/Local/Temp').",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        os.makedirs(path, exist_ok=True)
    except FileExistsError:
        print(f"ERROR: output path exists and is not a directory: {raw}",
              file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"ERROR: cannot create output directory {raw}: {e}",
              file=sys.stderr)
        sys.exit(1)

    if not os.access(path, os.W_OK):
        print(f"ERROR: output directory is not writable: {path}",
              file=sys.stderr)
        sys.exit(1)

    return path
```

**Step 2: Verify import surface**

Run (from `D:\Source\hermes-dir`): `./.venv/Scripts/python.exe -c "from multitone.optimizer import resolve_output_dir; print('ok')"`
Expected: `ok`

---

### Task 2: Wire guard into `optimizer.py::optimize()`

**Objective:** CPU optimizer validates/creates the output dir before the loop.

**Files:**
- Modify: `D:\Source\hermes-dir\multitone\optimizer.py:211` (docstring) and `:224` (call site)

**Step 1: Insert the call** — immediately after the existing `validate_ilowfreq` call (line 224):

```python
    validate_ilowfreq(ilowfreq, len(FrqPriLst_full), fraction, fsam)
    output_dir = resolve_output_dir(output_dir)
```

**Step 2: Update the parameter docstring** (line 211):

```python
    output_dir : str
        Directory for output files; created if missing (see resolve_output_dir).
```

**Step 3: Probe — bad paths fail fast, good paths work**

```bash
cd /d/Source/hermes-dir
PY=./.venv/Scripts/python.exe
SCR="C:/Users/MATTIA/AppData/Local/hermes/cache/scratch/odh_probe"
rm -rf "$SCR" && mkdir -p "$SCR"

# missing nested native dir → auto-created, run completes
$PY -m multitone.optimizer --maxiter 1 --output-dir "$SCR/run1/nested"; echo "exit=$?"
ls "$SCR/run1/nested" | grep -c "PhiLstMuTNewMin"

# MSYS-style → exit 1, clear message, no traceback
$PY -m multitone.optimizer --maxiter 1 --output-dir /tmp/odh_probe 2>&1; echo "exit=$?"

# file as directory → exit 1
touch "$SCR/notadir.txt"
$PY -m multitone.optimizer --maxiter 1 --output-dir "$SCR/notadir.txt" 2>&1; echo "exit=$?"

# empty string → exit 1
$PY -m multitone.optimizer --maxiter 1 --output-dir "" 2>&1; echo "exit=$?"
```

Expected: probe 1 → `exit=0`, dir `run1/nested` exists, ≥1 `PhiLstMuTNewMin[...].mat` written. Probe 2 → `exit=1` with `ERROR: --output-dir '/tmp/odh_probe' is not a valid Windows path: it must start with a drive letter ...`, no `Traceback`. Probes 3–4 → `exit=1` with the respective `ERROR:` lines, no traceback.

---

### Task 3: Wire guard into `optimizer_gpu.py::optimize_gpu()`

**Objective:** GPU optimizer (and its CPU fallback) validates the output dir before the loop.

**Files:**
- Modify: `D:\Source\hermes-dir\multitone\optimizer_gpu.py:18-24` (import list) and `:68` (call site)

**Step 1: Extend the import**

```python
from multitone.optimizer import (
    load_attenuation,
    format_phase_filename,
    format_audio_filename,
    optimize as optimize_cpu,
    validate_ilowfreq,
    resolve_output_dir
)
```

**Step 2: Insert the call** — immediately after the existing `validate_ilowfreq` call (line 68):

```python
    validate_ilowfreq(ilowfreq, len(FrqPriLst_full), fraction, fsam)
    output_dir = resolve_output_dir(output_dir)
```

Note: if CuPy is unavailable, the early fallback calls `optimize_cpu(...)`, which resolves the dir itself — the function is idempotent (`makedirs(exist_ok=True)`), so exactly one effective resolution happens per run either way.

**Step 3: Probe**

```bash
$PY -m multitone.optimizer_gpu --maxiter 1 --output-dir /tmp/odh_probe 2>&1; echo "exit=$?"
$PY -m multitone.optimizer_gpu --maxiter 1 --output-dir "$SCR/run2"; echo "exit=$?"
```

Expected: first → `exit=1` with the MSYS message; second → `exit=0`, `run2` created.

---

### Task 4: Wire guard into `optimizer_gpu_Cl1_Gv2.py::optimize_gpu()`

**Objective:** Same guard in the float64-precompute GPU variant.

**Files:**
- Modify: `D:\Source\hermes-dir\multitone\optimizer_gpu_Cl1_Gv2.py:18-24` (import list) and `:68` (call site)

**Step 1–2:** Identical edits to Task 3 Step 1–2 (import `resolve_output_dir`; insert call after line 68).

**Step 3: Probe**

```bash
$PY -m multitone.optimizer_gpu_Cl1_Gv2 --maxiter 1 --output-dir /tmp/odh_probe 2>&1; echo "exit=$?"
$PY -m multitone.optimizer_gpu_Cl1_Gv2 --maxiter 1 --output-dir "$SCR/run3"; echo "exit=$?"
```

Expected: first → `exit=1`; second → `exit=0`, `run3` created.

---

### Task 5: Update `--output-dir` help text in all three CLIs

**Objective:** Document native-path requirement and auto-creation in `--help`.

**Files:**
- Modify: `D:\Source\hermes-dir\multitone\optimizer.py:378-379`
- Modify: `D:\Source\hermes-dir\multitone\optimizer_gpu.py:208`
- Modify: `D:\Source\hermes-dir\multitone\optimizer_gpu_Cl1_Gv2.py:234`

**Step 1: Replace the argument definition in each `main()`**

`optimizer.py` (currently has a short help string):
```python
    parser.add_argument("--output-dir", type=str, default=".",
                        help="Directory for output files; created if missing. "
                             "Must be a native Windows path (e.g. D:/Source/out); "
                             "MSYS-style paths like /tmp/... are rejected")
```

Both GPU files (currently no help at all): same definition.

**Step 2: Verify**

```bash
$PY -m multitone.optimizer --help | grep -A2 "output-dir"
```
Expected: the new help text renders.

---

### Task 6: Regression tests (new file, math untouched)

**Objective:** Keep the guard covered by tests that only exercise the validation helper — never the signal math.

**Files:**
- Create: `D:\Source\hermes-dir\multitone\tests\test_output_dir_guard.py`

**Step 1: Write the test file**

```python
"""Regression tests for the --output-dir guard (resolve_output_dir).

Exercises ONLY the validation/normalization helper — no signal math.
"""

import os

import pytest

from multitone.optimizer import resolve_output_dir


def test_missing_nested_dir_is_created(tmp_path):
    target = tmp_path / "a" / "b" / "c"
    result = resolve_output_dir(str(target))
    assert os.path.isdir(result)
    assert os.path.isabs(result)
    assert os.path.normpath(result) == os.path.normpath(str(target))


def test_existing_dir_is_returned(tmp_path):
    result = resolve_output_dir(str(tmp_path))
    assert os.path.normpath(result) == os.path.normpath(str(tmp_path))


def test_relative_path_resolved(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = resolve_output_dir("sub")
    assert os.path.normpath(result) == os.path.normpath(str(tmp_path / "sub"))
    assert os.path.isdir(result)


def test_path_that_is_a_file_exits(tmp_path):
    f = tmp_path / "afile.txt"
    f.write_text("x")
    with pytest.raises(SystemExit) as exc:
        resolve_output_dir(str(f))
    assert exc.value.code == 1


def test_parent_is_a_file_exits(tmp_path):
    f = tmp_path / "afile.txt"
    f.write_text("x")
    with pytest.raises(SystemExit) as exc:
        resolve_output_dir(str(f / "child"))
    assert exc.value.code == 1


@pytest.mark.parametrize("empty", ["", "   "])
def test_empty_string_exits(empty):
    with pytest.raises(SystemExit) as exc:
        resolve_output_dir(empty)
    assert exc.value.code == 1


def test_tilde_expanded(tmp_path, monkeypatch):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    result = resolve_output_dir("~/sub")
    assert os.path.normpath(result) == os.path.normpath(str(tmp_path / "sub"))
    assert os.path.isdir(result)


@pytest.mark.skipif(os.name != "nt", reason="Windows-specific MSYS path check")
@pytest.mark.parametrize("raw", ["/tmp/foo", "/d/Source/out", "/tmp/xyzzy/deep"])
def test_msys_style_path_rejected_unconditionally(raw):
    # Rejection is by path shape, before any filesystem mutation — no
    # drive-root access needed, and it holds whether or not the resolved
    # directory happens to exist.
    with pytest.raises(SystemExit) as exc:
        resolve_output_dir(raw)
    assert exc.value.code == 1
```

**Step 2: Run**

```bash
cd /d/Source/hermes-dir && ./.venv/Scripts/python.exe -m pytest multitone/tests/ -v
```
Expected: **20 passed** (9 from `test_ilowfreq_guard.py` + 11 new). If any of the new tests fails, fix the helper (not the test) unless the test itself misstates the spec.

---

### Task 7: End-to-end verification and math-untouched check

**Objective:** Prove default behavior is unchanged and no math file was modified.

**Step 1: Default invocation from a scratch CWD** (default `--output-dir .` must behave exactly as before):

```bash
cd /d/Source/hermes-dir
SCR="C:/Users/MATTIA/AppData/Local/hermes/cache/scratch/odh_probe"
cd "$SCR"
PYTHONPATH='D:/Source/hermes-dir' D:/Source/hermes-dir/.venv/Scripts/python.exe -m multitone.optimizer --maxiter 1
echo "exit=$?"
ls | grep -c "PhiLstMuTNewMin"
```
Expected: `exit=0`, artifacts written into `$SCR` (the CWD), same output format as before.

**Step 2: Confirm the full probe matrix** — re-run Task 2 Step 3, Task 3 Step 3, Task 4 Step 3 probes; all must match expectations.

**Step 3: Math-untouched check**

```bash
cd /d/Source/hermes-dir/multitone && ls -la --time-style=+%Y-%m-%d_%H:%M *.py
```
Expected: only `optimizer.py`, `optimizer_gpu.py`, `optimizer_gpu_Cl1_Gv2.py` (and `tests/`) show today's edit time; `synthesize.py`, `producer.py`, `primes.py`, `analyze_multitone_v0.py`, `__init__.py` keep their pre-existing timestamps.

**Step 4: Clean up probe artifacts**

```bash
rm -rf "C:/Users/MATTIA/AppData/Local/hermes/cache/scratch/odh_probe"
```

---

## Files likely to change

| File | Change |
|---|---|
| `D:\Source\hermes-dir\multitone\optimizer.py` | +`resolve_output_dir` helper; call in `optimize()`; `output_dir` docstring; `--help` text |
| `D:\Source\hermes-dir\multitone\optimizer_gpu.py` | import + call in `optimize_gpu()`; `--help` text |
| `D:\Source\hermes-dir\multitone\optimizer_gpu_Cl1_Gv2.py` | import + call in `optimize_gpu()`; `--help` text |
| `D:\Source\hermes-dir\multitone\tests\test_output_dir_guard.py` | new regression test file (11 cases) |
| `synthesize.py`, `producer.py`, `primes.py`, `analyze_multitone_v0.py`, `__init__.py` | **no changes** |

## Verification summary

1. Missing nested native dir → auto-created, run completes, artifacts land there (all 3 scripts).
2. MSYS-style `/tmp/...` → exit 1 **unconditionally** (even if the resolved dir exists), `ERROR: ... not a valid Windows path ...` message, no traceback (all 3 scripts).
3. File-as-directory, empty string → exit 1 with clean messages.
4. Default invocation (`--output-dir .`) byte-identical behavior to before.
5. `pytest multitone/tests/` → 20 passed.
6. Math files untouched (mtime check).
7. No code path or test requires drive-root write permission.

## Risks, tradeoffs, open questions

- **Typo'd dirs are now auto-created** (`--output-dir resutls` creates `resutls` instead of failing). Accepted for convenience; switch to require-exists by deleting the `os.makedirs` try/except block (one-line decision, flagged in the design section).
- **MSYS rejection is unconditional** (the "honor if it exists" exception was dropped at the user's request — no drive-root dependency) — no code path or test needs drive-root write permission; the rejection is tested by path shape alone (3 parametrized cases). A user with a real `C:\tmp` must write it natively (`C:/tmp`) — trivial, and the error message says so.
- **Missing UNC paths** (`//server/share`) pass the MSYS check (the `//` prefix is exempt) and fail at `makedirs` with the clear `ERROR: cannot create output directory ...` message. Accepted.
- **`os.access` is not ACL-perfect** (admin/UAC edge cases). Accepted; probe-file alternative noted in the design section.
- **MAX_PATH (260 chars)** not addressed: generated filenames are ~110 chars, so a very deep `--output-dir` can still overflow. Docstring-level note only (YAGNI).
- **`producer.py` out of scope** — it writes to CWD with no `--output-dir`; the same helper could be applied there later if the flag is ever added.
- **Behavior change (intended):** bad output dirs fail in milliseconds with exit 1 instead of mid-run traceback + lost best result; missing dirs are auto-created instead of crashing.
- **No git repository** in `D:\Source\hermes-dir` → no commits; the diff above is the complete change set.
