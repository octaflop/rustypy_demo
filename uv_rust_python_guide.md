# UV, UVX, and Rust-Python Integration: A Comprehensive Guide

## Part 1: The Historical Context of Python Packaging

As a 20+ year Python veteran, you've lived through the chaos. Let's trace the evolution:

### The Dark Ages (1996-2004)
- **No packaging**: Files shared via email, FTP, mailing lists
- **1998**: `distutils` introduced — the first standardized build system
- **2000**: `distutils` included in Python 1.6 standard library
- You'd run `python setup.py install` and hope for the best. No dependency management.

### The setuptools Era (2004-2014)
- **2004**: Phillip Eby creates `setuptools` — extending distutils with:
  - `install_requires` for declaring dependencies
  - The `.egg` format (Python's answer to Java JARs)
  - `easy_install` for automatic downloading
- **2005**: PyPI starts accepting package uploads
- **2007**: Ian Bicking creates `virtualenv` — isolated environments
- **2008**: Ian Bicking creates `pip` — better UX than `easy_install`
- **2011**: Python Packaging Authority (PyPA) formed

### The Standardization Push (2014-2020)
- **2012**: Wheel format (`.whl`) introduced via PEP 427 — replacing eggs
- **2014**: `distutils` begins deprecation
- **2015-2017**: PEP 517/518 standardize build backends and `pyproject.toml`
- **2017**: Poetry emerges as an "opinionated" all-in-one tool
- **2020**: PEP 621 standardizes core metadata in `pyproject.toml`

### The Modern Era (2020-Present)
- **2022**: Python 3.12 removes `distutils` from stdlib
- **2023**: Armin Ronacher creates Rye (experimental unified tool)
- **2024**: Astral releases **uv** — everything changes

---

## Part 2: Understanding UV

### What is UV?

UV is an extremely fast Python package and project manager written in **Rust** by Astral (the company behind Ruff, the fast Python linter). Released in February 2024, it's designed as "Cargo for Python."

**Speed comparison**: 10-100x faster than pip for most operations.

### What UV Replaces

| Old Tool | UV Equivalent |
|----------|---------------|
| `pip` | `uv pip` |
| `pip-tools` | `uv pip compile` |
| `virtualenv` / `venv` | `uv venv` |
| `pyenv` | `uv python` |
| `pipx` | `uvx` / `uv tool` |
| `poetry` / `pdm` | `uv` (project management) |

### Core UV Commands

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a new project
uv init my-project
cd my-project

# Add dependencies
uv add requests numpy pandas

# Run your code (auto-creates venv, installs deps)
uv run python main.py

# Sync dependencies from lockfile
uv sync

# Install/manage Python versions
uv python install 3.12 3.13
uv python pin 3.12

# Create virtual environment explicitly
uv venv --python 3.12
source .venv/bin/activate

# pip-compatible interface (drop-in replacement)
uv pip install requests
uv pip compile requirements.in -o requirements.txt
uv pip sync requirements.txt
```

### Project Structure with UV

```
my-project/
├── .python-version      # Pinned Python version
├── .venv/               # Virtual environment
├── pyproject.toml       # Project config + dependencies
├── uv.lock              # Cross-platform lockfile (deterministic!)
├── src/
│   └── my_project/
│       └── __init__.py
└── tests/
```

---

## Part 3: Understanding UVX

`uvx` is an alias for `uv tool run` — it runs Python CLI tools in ephemeral, isolated environments without permanent installation.

```bash
# Run a tool without installing it
uvx ruff check .
uvx black --check .
uvx pytest

# Run a specific version
uvx 'ruff>=0.4.0' check .

# Install a tool permanently
uv tool install ruff
uv tool install httpie

# List installed tools
uv tool list
```

**Why this matters**: No more polluting your global Python or forgetting which virtualenv has which tool. Tools are cached and reused efficiently.

---

## Part 4: Integrating Rust into Python

Now the fun part for a Rustacean! There are two main approaches:

### Approach 1: PyO3 + Maturin (Recommended)

**PyO3** is a Rust crate providing bindings for Python — it lets you write native Python modules in Rust.

**Maturin** is a build tool (also written in Rust) that packages your PyO3 code into Python wheels.

### Setting Up a Rust Extension Project

**Method A: Using uv init with maturin backend**

```bash
# Create project with Rust extension support
uv init my-rust-ext --lib --build-backend maturin
cd my-rust-ext
```

**Method B: Using maturin directly**

```bash
# Install maturin as a tool
uv tool install maturin

# Create new project
maturin new my-rust-ext --bindings pyo3
cd my-rust-ext

# Or initialize in existing directory
mkdir my-rust-ext && cd my-rust-ext
maturin init --bindings pyo3
```

### Project Structure

```
my-rust-ext/
├── Cargo.toml           # Rust dependencies
├── pyproject.toml       # Python project config
├── src/
│   └── lib.rs           # Rust code
└── python/
    └── my_rust_ext/     # Optional: pure Python code
        └── __init__.py
```

---

## Part 5: Code Examples

### Example 1: Basic Function

**Cargo.toml**
```toml
[package]
name = "string_utils"
version = "0.1.0"
edition = "2021"

[lib]
name = "string_utils"
crate-type = ["cdylib"]

[dependencies.pyo3]
version = "0.23"
features = ["abi3-py39"]  # Compatible with Python 3.9+
```

**pyproject.toml**
```toml
[build-system]
requires = ["maturin>=1.5,<2.0"]
build-backend = "maturin"

[project]
name = "string_utils"
version = "0.1.0"
requires-python = ">=3.9"

[tool.maturin]
features = ["pyo3/extension-module"]
```

**src/lib.rs**
```rust
use pyo3::prelude::*;

/// Reverse a string (much faster for large strings!)
#[pyfunction]
fn reverse_string(s: &str) -> String {
    s.chars().rev().collect()
}

/// Count occurrences of a character
#[pyfunction]
fn count_char(s: &str, c: char) -> usize {
    s.chars().filter(|&ch| ch == c).count()
}

/// A Python module implemented in Rust
#[pymodule]
fn string_utils(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(reverse_string, m)?)?;
    m.add_function(wrap_pyfunction!(count_char, m)?)?;
    Ok(())
}
```

**Build and use:**
```bash
# Development mode (fast iteration)
maturin develop

# Or with uv
uv run maturin develop

# Then in Python:
python -c "import string_utils; print(string_utils.reverse_string('hello'))"
# Output: olleh
```

---

### Example 2: Exposing a Rust Struct as a Python Class

**src/lib.rs**
```rust
use pyo3::prelude::*;
use std::collections::HashMap;

/// A high-performance counter implemented in Rust
#[pyclass]
struct Counter {
    counts: HashMap<String, u64>,
}

#[pymethods]
impl Counter {
    #[new]
    fn new() -> Self {
        Counter {
            counts: HashMap::new(),
        }
    }

    /// Increment the count for a key
    fn increment(&mut self, key: String) {
        *self.counts.entry(key).or_insert(0) += 1;
    }

    /// Get the count for a key
    fn get(&self, key: &str) -> u64 {
        *self.counts.get(key).unwrap_or(&0)
    }

    /// Get all counts as a Python dict
    fn to_dict(&self) -> HashMap<String, u64> {
        self.counts.clone()
    }

    /// Get the most common items
    fn most_common(&self, n: usize) -> Vec<(String, u64)> {
        let mut items: Vec<_> = self.counts.iter()
            .map(|(k, v)| (k.clone(), *v))
            .collect();
        items.sort_by(|a, b| b.1.cmp(&a.1));
        items.truncate(n);
        items
    }
}

#[pymodule]
fn fast_counter(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Counter>()?;
    Ok(())
}
```

**Usage in Python:**
```python
from fast_counter import Counter

c = Counter()
for word in ["apple", "banana", "apple", "cherry", "apple", "banana"]:
    c.increment(word)

print(c.get("apple"))      # 3
print(c.most_common(2))    # [("apple", 3), ("banana", 2)]
print(c.to_dict())         # {"apple": 3, "banana": 2, "cherry": 1}
```

---

### Example 3: NumPy Integration with Parallelism

**Cargo.toml** (add these dependencies)
```toml
[dependencies]
pyo3 = { version = "0.23", features = ["abi3-py39"] }
numpy = "0.23"
rayon = "1.10"
```

**src/lib.rs**
```rust
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;
use rayon::prelude::*;

/// Parallel sum of squares (much faster for large arrays)
#[pyfunction]
fn parallel_sum_of_squares(arr: PyReadonlyArray1<f64>) -> f64 {
    let slice = arr.as_slice().unwrap();
    slice.par_iter().map(|x| x * x).sum()
}

/// Element-wise operation with parallelism
#[pyfunction]
fn parallel_transform<'py>(
    py: Python<'py>,
    arr: PyReadonlyArray1<'py, f64>,
) -> Bound<'py, PyArray1<f64>> {
    let slice = arr.as_slice().unwrap();
    
    // Parallel computation
    let result: Vec<f64> = slice
        .par_iter()
        .map(|x| x.sin() + x.cos() * x.exp())
        .collect();
    
    PyArray1::from_vec(py, result)
}

#[pymodule]
fn fast_numpy(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parallel_sum_of_squares, m)?)?;
    m.add_function(wrap_pyfunction!(parallel_transform, m)?)?;
    Ok(())
}
```

**Usage:**
```python
import numpy as np
from fast_numpy import parallel_sum_of_squares, parallel_transform

# Create a large array
arr = np.random.randn(10_000_000)

# This runs in parallel across all CPU cores!
result = parallel_sum_of_squares(arr)
transformed = parallel_transform(arr)
```

---

### Example 4: Mixed Python/Rust Project

For a project that's mostly Python with performance-critical Rust parts:

**Project structure:**
```
mixed_project/
├── Cargo.toml
├── pyproject.toml
├── src/
│   └── lib.rs              # Rust extension
├── python/
│   └── mixed_project/
│       ├── __init__.py     # Pure Python
│       ├── utils.py        # Pure Python helpers
│       └── _rust.pyi       # Type stubs for Rust module
└── tests/
    └── test_all.py
```

**pyproject.toml**
```toml
[build-system]
requires = ["maturin>=1.5,<2.0"]
build-backend = "maturin"

[project]
name = "mixed_project"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = ["numpy>=1.20"]

[project.optional-dependencies]
dev = ["pytest", "hypothesis"]

[tool.maturin]
features = ["pyo3/extension-module"]
python-source = "python"
module-name = "mixed_project._rust"

[tool.uv]
# Rebuild when Rust source changes
cache-keys = [
    { file = "pyproject.toml" },
    { file = "Cargo.toml" },
    { file = "**/*.rs" }
]
```

**python/mixed_project/__init__.py**
```python
"""Mixed Python/Rust package."""
from mixed_project._rust import fast_function, FastClass
from mixed_project.utils import helper_function

__all__ = ["fast_function", "FastClass", "helper_function"]
```

---

## Part 6: Development Workflow

### Option A: uv handles everything

```bash
# pyproject.toml has cache-keys configured
# uv automatically rebuilds when Rust changes
uv run python -c "import my_ext; print(my_ext.hello())"
uv run pytest
```

### Option B: maturin develop for fast iteration

```bash
# Create venv with uv
uv venv
source .venv/bin/activate

# Fast debug builds during development
maturin develop

# Release builds for benchmarking
maturin develop --release

# Run tests
uv run pytest
```

### Option C: Maturin import hook (auto-rebuild on import)

```python
# Install the hook
# pip install maturin

# In your test file or REPL:
import maturin
maturin.import_hook.install()

# Now any import will trigger rebuild if source changed
import my_rust_ext  # Rebuilds automatically!
```

---

## Part 7: Publishing Your Package

```bash
# Build wheels for current platform
maturin build --release

# Build for multiple platforms (in CI)
# Use maturin-action on GitHub Actions

# Publish to PyPI
maturin publish
# Or with uv:
uv publish
```

---

## Part 8: Real-World Examples

These popular packages use PyO3/Maturin:

| Package | Description |
|---------|-------------|
| **Ruff** | Fast Python linter (the one Astral makes!) |
| **Polars** | Fast DataFrame library |
| **tokenizers** | Hugging Face's fast tokenization |
| **orjson** | Fast JSON library |
| **pydantic-core** | Pydantic v2's Rust core |
| **cryptography** | Cryptographic recipes |

---

## Quick Reference Card

```bash
# === UV BASICS ===
uv init project              # New project
uv add package               # Add dependency
uv remove package            # Remove dependency
uv sync                      # Sync from lockfile
uv run script.py             # Run with auto-setup
uv lock                      # Update lockfile

# === UV PYTHON MANAGEMENT ===
uv python install 3.12       # Install Python
uv python list               # List available
uv python pin 3.12           # Pin for project

# === UVX (TOOL RUNNER) ===
uvx ruff check .             # Run tool ephemerally
uv tool install ruff         # Install permanently
uv tool list                 # List installed tools

# === MATURIN (RUST EXTENSIONS) ===
maturin init                 # Initialize in directory
maturin new project          # Create new project
maturin develop              # Build + install (debug)
maturin develop --release    # Build + install (release)
maturin build --release      # Build wheel
maturin publish              # Publish to PyPI

# === COMBINED WORKFLOW ===
uv init my-ext --lib --build-backend maturin
cd my-ext
uv run maturin develop
uv run pytest
```

---

## Summary

As someone with your experience, you'll appreciate that:

1. **UV** finally brings Cargo-like ergonomics to Python — fast, deterministic, unified
2. **UVX** solves the "which virtualenv has my linter" problem elegantly
3. **PyO3 + Maturin** make Rust-Python integration nearly as smooth as writing native Python
4. The whole stack is **Rust all the way down** — uv, maturin, pyo3 — eating our own dog food

The ecosystem has matured to the point where your 20 years of Python knowledge combines beautifully with your 1 year of Rust. Write your algorithms in Rust, expose them with `#[pyfunction]`, build with maturin, manage with uv — and your Python colleagues can `pip install` your package without knowing Rust exists.

Welcome to the future of Python packaging! 🦀🐍
