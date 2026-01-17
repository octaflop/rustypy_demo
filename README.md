# Rust-Python Demo Project

A minimal example demonstrating Rust-Python integration using **PyO3**, **Maturin**, and **uv**.

## Prerequisites

- [Rust](https://rustup.rs/) (1.74+)
- [uv](https://github.com/astral-sh/uv) (or pip/maturin directly)

## Quick Start

### Option 1: Using uv (Recommended)

```bash
# uv handles everything: venv, dependencies, building
uv run python demo.py
```

### Option 2: Using maturin directly

```bash
# Install maturin
uv tool install maturin
# or: pip install maturin

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Build and install the extension (debug mode for fast iteration)
maturin develop

# Run the demo
python demo.py
```

### Option 3: Release build (optimized)

```bash
maturin develop --release
python demo.py
```

## Project Structure

```
rust_python_demo/
├── Cargo.toml          # Rust package manifest
├── pyproject.toml      # Python project config (PEP 517/518)
├── src/
│   └── lib.rs          # Rust source code with PyO3 bindings
├── demo.py             # Python demo script
└── README.md
```

## What's Demonstrated

### Functions
- `fibonacci(n)` - Compute nth Fibonacci number
- `count_unique_words(text)` - Count unique words (case-insensitive)
- `is_palindrome(s)` - Check if string is a palindrome
- `safe_parse_int(s)` - Parse int with Python exception on error
- `safe_divide(a, b)` - Division with zero-check
- `sum_list(items)` - Sum a list of integers
- `filter_positive(items)` - Filter to positive numbers only
- `word_frequencies(words)` - Count word occurrences

### Classes
- `MovingAverage(window_size)` - Rolling average calculator
- `RingBuffer(capacity)` - Fixed-size circular buffer

## Key Files Explained

### Cargo.toml
```toml
[lib]
crate-type = ["cdylib"]  # Creates a C-compatible dynamic library

[dependencies.pyo3]
version = "0.23"
features = ["extension-module", "abi3-py39"]  # Stable ABI for Python 3.9+
```

### pyproject.toml
```toml
[build-system]
requires = ["maturin>=1.5,<2.0"]
build-backend = "maturin"

[tool.uv]
cache-keys = [{ file = "**/*.rs" }]  # Rebuild when Rust changes
```

## Tips

- Use `maturin develop` for fast debug builds during development
- Use `maturin develop --release` for performance testing
- The `abi3-py39` feature creates wheels compatible with Python 3.9+
- Add `#[pyo3(name = "python_name")]` to rename functions/classes in Python

## Learn More

- [PyO3 User Guide](https://pyo3.rs/)
- [Maturin User Guide](https://www.maturin.rs/)
- [uv Documentation](https://docs.astral.sh/uv/)
