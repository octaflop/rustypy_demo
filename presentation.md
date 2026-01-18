# Rust for Pythonistas: Building Native Extensions with PyO3

*A hands-on guide to Rust-Python integration for the SLCPython meetup*

---

## Introduction

Python is fantastic for productivity, but sometimes you need raw performance. While NumPy, pandas, and other libraries handle many computationally intensive tasks, there are times when you need custom high-performance code. That's where Rust comes in.

### Why Rust for Python Extensions?

**CPU-bound workloads**: Rust compiles to native machine code with zero-cost abstractions. For tight loops and numerical computation, Rust can be 10-100x faster than pure Python.

**Memory safety guarantees**: Rust's ownership system eliminates entire classes of bugs—no null pointer dereferences, no use-after-free, no data races. This is especially valuable in extensions where bugs can crash your Python interpreter.

**True parallelism**: Rust code doesn't hold the GIL (Global Interpreter Lock). Your Rust extension can use all CPU cores without the threading limitations Python has.

**Growing ecosystem**: Major Python tools are already built with Rust and PyO3:
- **polars** — DataFrame library that outperforms pandas
- **pydantic-core** — The validation engine behind pydantic v2
- **ruff** — Python linter that's 100x faster than flake8
- **cryptography** — Cryptographic primitives

### What We'll Build

In this workshop, we'll explore a complete Rust extension module with:
- Pure functions with automatic type conversion
- Error handling that raises Python exceptions
- Collection operations (lists, dicts)
- Stateful Python classes implemented in Rust

---

## The Toolchain

Two tools make Rust-Python integration seamless:

### PyO3 — Rust Bindings for Python

PyO3 is a Rust library that provides:

- **Procedural macros** that generate Python bindings automatically
- **Type conversions** between Rust and Python types
- **Exception handling** across the Rust-Python boundary
- **Stable ABI support** (one compiled binary works across Python versions)

### Maturin — Build Tool for Rust+Python Projects

Maturin handles the complexity of building Rust code into Python wheels:

- `maturin develop` — Build and install locally for fast iteration
- `maturin build` — Create distributable wheel files
- PEP 517/518 compliant — Works with pip, uv, and other standard tools

### uv — Modern Python Package Manager (Optional)

uv is a fast, modern Python package manager that integrates well with maturin:
- Automatic rebuild detection when Rust files change
- Fast, deterministic dependency resolution

---

## Project Structure

Our demo project has a simple layout:

```
rustypy_demo/
├── lib.rs           # Rust source code with PyO3 bindings
├── Cargo.toml       # Rust package configuration
├── pyproject.toml   # Python project configuration
└── demo.py          # Python code using the extension
```

### lib.rs — The Rust Code

This is where all your Rust code lives. PyO3 macros transform regular Rust functions and structs into Python-callable objects.

### Cargo.toml — Rust Configuration

```toml
[package]
name = "rust_demo"
version = "0.1.0"
edition = "2021"

[lib]
name = "rust_demo"
path = "lib.rs"
crate-type = ["cdylib"]

[dependencies.pyo3]
version = "0.23"
features = ["extension-module", "abi3-py39"]
```

Key settings:
- `crate-type = ["cdylib"]` — Creates a C-compatible dynamic library that Python can load
- `abi3-py39` — Uses Python's stable ABI, so one build works for Python 3.9+

### pyproject.toml — Python Configuration

```toml
[build-system]
requires = ["maturin>=1.5,<2.0"]
build-backend = "maturin"

[project]
name = "rust_demo"
version = "0.1.0"
requires-python = ">=3.9"

[tool.maturin]
features = ["pyo3/extension-module"]

# Tell uv to rebuild when Rust source changes
[tool.uv]
cache-keys = [
    { file = "pyproject.toml" },
    { file = "Cargo.toml" },
    { file = "**/*.rs" }
]
```

The `build-backend = "maturin"` tells pip/uv how to build this project, and the `cache-keys` ensure uv rebuilds when Rust files change.

---

## Rust Crash Course for Pythonistas

Before diving into PyO3 code, let's cover the Rust syntax you'll encounter.

### Variables and Types

```rust
let x = 42;              // Immutable by default (like Python, sort of)
let mut y = 0;           // Mutable - can be changed
let z: i64 = 100;        // Explicit type annotation
```

Rust has explicit integer types: `i32`, `i64`, `u64` (unsigned), `f64` (float), etc.

### Functions

```rust
fn add(a: i64, b: i64) -> i64 {
    a + b  // No semicolon = return value (like expression bodies)
}
```

The `->` indicates the return type. The last expression without a semicolon is returned.

### Structs (Like Python Dataclasses)

```rust
struct Point {
    x: f64,
    y: f64,
}
```

### impl Blocks (Methods)

```rust
impl Point {
    fn distance(&self) -> f64 {
        (self.x.powi(2) + self.y.powi(2)).sqrt()
    }
}
```

`&self` is like Python's `self` parameter, but the `&` means "borrow" (read-only reference).

### Result and Option (Explicit Error Handling)

```rust
// Result: either success (Ok) or error (Err)
fn divide(a: f64, b: f64) -> Result<f64, String> {
    if b == 0.0 {
        Err("Division by zero".to_string())
    } else {
        Ok(a / b)
    }
}

// Option: either Some(value) or None
fn first_element(list: &[i64]) -> Option<i64> {
    if list.is_empty() {
        None
    } else {
        Some(list[0])
    }
}
```

This is Rust's approach to null/error handling—no exceptions that can surprise you.

### The Key Difference: Ownership

Rust's killer feature is its ownership system. Every value has exactly one owner, and when that owner goes out of scope, the value is dropped:

```rust
let s1 = String::from("hello");
let s2 = s1;      // s1 is "moved" to s2
// println!("{}", s1);  // ERROR: s1 no longer valid

let s3 = s2.clone();  // Explicit copy if you need both
```

For PyO3, you'll mostly see `&str` (borrowed string slice) and `&self`/`&mut self` (borrowed references to self). The `&` means "I'm borrowing this, not taking ownership."

---

## Building Your First Function

Let's look at a simple function from our demo:

```rust
use pyo3::prelude::*;

/// Compute the nth Fibonacci number iteratively
#[pyfunction]
fn fibonacci(n: u64) -> u64 {
    match n {
        0 => 0,
        1 => 1,
        _ => {
            let mut a = 0u64;
            let mut b = 1u64;
            for _ in 2..=n {
                let temp = a + b;
                a = b;
                b = temp;
            }
            b
        }
    }
}
```

### Key Elements

**`#[pyfunction]`** — This attribute macro tells PyO3 to generate a Python wrapper for this function.

**`n: u64`** — The parameter type. PyO3 automatically converts Python `int` to Rust `u64`.

**`-> u64`** — The return type. PyO3 converts it back to Python `int`.

**`match`** — Rust's powerful pattern matching (like a switch statement on steroids).

### Registering in the Module

Every function needs to be registered in the module:

```rust
#[pymodule]
fn rust_demo(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fibonacci, m)?)?;
    // ... more functions
    Ok(())
}
```

The `wrap_pyfunction!` macro creates the necessary wrapper code.

---

## Type Conversions Deep Dive

PyO3 handles type conversion automatically. Here's the mapping:

| Rust Type | Python Type | Notes |
|-----------|-------------|-------|
| `i64`, `u64` | `int` | Various integer sizes available |
| `f64` | `float` | Also `f32` |
| `bool` | `bool` | |
| `&str` | `str` | Borrowed string (efficient) |
| `String` | `str` | Owned string |
| `Vec<T>` | `list` | Any convertible element type |
| `HashMap<K,V>` | `dict` | Keys must be hashable |
| `Option<T>` | `T` or `None` | Rust's null-safety |

### Example: Working with Lists

```rust
/// Sum all elements in a list
#[pyfunction]
fn sum_list(items: Vec<i64>) -> i64 {
    items.iter().sum()
}

/// Filter a list to only positive numbers
#[pyfunction]
fn filter_positive(items: Vec<i64>) -> Vec<i64> {
    items.into_iter().filter(|&x| x > 0).collect()
}
```

PyO3 converts the Python list to a Rust `Vec`, your code processes it, and the result converts back automatically.

### Example: Working with Dicts

```rust
use std::collections::HashMap;

/// Create a frequency map from a list of strings
#[pyfunction]
fn word_frequencies(words: Vec<String>) -> HashMap<String, u64> {
    let mut freq = HashMap::new();
    for word in words {
        *freq.entry(word.to_lowercase()).or_insert(0) += 1;
    }
    freq
}
```

Python usage:
```python
>>> rust_demo.word_frequencies(["apple", "Banana", "APPLE", "banana"])
{'apple': 2, 'banana': 2}
```

---

## Error Handling: Rust Errors → Python Exceptions

For production code, you need to handle errors gracefully. PyO3 makes this straightforward:

```rust
use pyo3::exceptions::PyValueError;

/// Divide two numbers, raising Python exception on division by zero
#[pyfunction]
fn safe_divide(a: f64, b: f64) -> PyResult<f64> {
    if b == 0.0 {
        Err(PyValueError::new_err("Division by zero"))
    } else {
        Ok(a / b)
    }
}
```

### Key Elements

**`PyResult<f64>`** — Return type that can be either `Ok(value)` or `Err(exception)`.

**`PyValueError::new_err("message")`** — Creates a Python `ValueError` with the given message.

PyO3 provides exception types for all Python built-in exceptions:
- `PyValueError`
- `PyTypeError`
- `PyKeyError`
- `PyIndexError`
- `PyRuntimeError`
- And many more...

### Python Usage

```python
>>> rust_demo.safe_divide(10, 3)
3.3333333333333335

>>> rust_demo.safe_divide(10, 0)
Traceback (most recent call last):
  ...
ValueError: Division by zero
```

### Another Example: Parsing

```rust
/// Parse a string as an integer with proper error handling
#[pyfunction]
fn safe_parse_int(s: &str) -> PyResult<i64> {
    s.trim()
        .parse::<i64>()
        .map_err(|e| PyValueError::new_err(format!("Cannot parse '{}': {}", s, e)))
}
```

The `.map_err()` converts Rust's parse error into a Python exception.

---

## Creating Python Classes in Rust

Now for the powerful stuff—stateful Python objects implemented in Rust:

```rust
/// A simple moving average calculator
#[pyclass]
struct MovingAverage {
    window_size: usize,
    values: Vec<f64>,
}

#[pymethods]
impl MovingAverage {
    /// Create a new MovingAverage with specified window size
    #[new]
    fn new(window_size: usize) -> PyResult<Self> {
        if window_size == 0 {
            return Err(PyValueError::new_err("Window size must be positive"));
        }
        Ok(MovingAverage {
            window_size,
            values: Vec::new(),
        })
    }

    /// Add a value and return the current moving average
    fn add(&mut self, value: f64) -> f64 {
        self.values.push(value);
        if self.values.len() > self.window_size {
            self.values.remove(0);
        }
        self.average()
    }

    /// Get the current moving average
    fn average(&self) -> f64 {
        if self.values.is_empty() {
            0.0
        } else {
            self.values.iter().sum::<f64>() / self.values.len() as f64
        }
    }

    /// Get the number of values currently stored
    fn count(&self) -> usize {
        self.values.len()
    }

    /// Clear all values
    fn clear(&mut self) {
        self.values.clear();
    }

    /// Python representation
    fn __repr__(&self) -> String {
        format!(
            "MovingAverage(window_size={}, count={}, avg={:.2})",
            self.window_size,
            self.values.len(),
            self.average()
        )
    }
}
```

### Key Elements

**`#[pyclass]`** — Marks this struct as a Python class.

**`#[pymethods]`** — Marks the impl block as containing Python methods.

**`#[new]`** — The constructor, equivalent to `__init__` in Python.

**`&self`** vs **`&mut self`**:
- `&self` — Read-only access (like a property getter)
- `&mut self` — Mutable access (methods that change state)

**Magic methods**: `__repr__`, `__len__`, `__str__`, etc. work as expected.

### Python Usage

```python
>>> ma = rust_demo.MovingAverage(3)
>>> ma.add(10.0)
10.0
>>> ma.add(20.0)
15.0
>>> ma.add(30.0)
20.0
>>> ma.add(40.0)  # Window slides, drops 10.0
30.0
>>> ma
MovingAverage(window_size=3, count=3, avg=30.00)
```

### Registering Classes

```rust
#[pymodule]
fn rust_demo(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // ... functions ...
    m.add_class::<MovingAverage>()?;
    m.add_class::<RingBuffer>()?;
    Ok(())
}
```

---

## Running the Demo

### Prerequisites

- Rust toolchain (install from https://rustup.rs)
- Python 3.9+
- maturin (`pip install maturin` or `uv add maturin`)

### Build and Run

```bash
# Clone or navigate to the project
cd rustypy_demo

# Install dependencies (if using uv)
uv sync

# Build the Rust extension and install it locally
maturin develop

# Run the demo
python demo.py
```

### Expected Output

```
============================================================
🦀 Rust-Python Integration Demo 🐍
============================================================

📌 Example 1: Simple Functions
----------------------------------------
fibonacci(40) = 102334155 (took 0.001ms)
Python fibonacci(40) = 102334155 (took 0.003ms)

Unique words in text: 9
is_palindrome('A man a plan a canal Panama'): True
is_palindrome('hello'): False
...

📌 Example 4: MovingAverage Class
----------------------------------------
Created: MovingAverage(window_size=3, count=0, avg=0.00)
Added 10.0, moving average: 10.00, count: 1
Added 20.0, moving average: 15.00, count: 2
Added 30.0, moving average: 20.00, count: 3
Added 40.0, moving average: 30.00, count: 3
...
```

---

## Workshop Exercises

Now it's your turn! Try these exercises to reinforce what you've learned.

### Exercise 1: Add a Factorial Function (Beginner)

Create a function that computes `n!` (factorial).

**Steps:**
1. Add to `lib.rs`:
```rust
#[pyfunction]
fn factorial(n: u64) -> u64 {
    // Your implementation here
    // Hint: (1..=n).product() works, or use a loop
}
```

2. Register it in the module:
```rust
m.add_function(wrap_pyfunction!(factorial, m)?)?;
```

3. Rebuild and test:
```bash
maturin develop
python -c "import rust_demo; print(rust_demo.factorial(10))"
# Should print: 3628800
```

---

### Exercise 2: Add Error Handling (Beginner)

Modify your factorial to handle invalid input gracefully.

**Requirements:**
- Return `PyResult<u64>` instead of `u64`
- Return an error for inputs > 20 (to avoid overflow)
- Test that it raises `ValueError` in Python

```rust
#[pyfunction]
fn factorial(n: u64) -> PyResult<u64> {
    if n > 20 {
        return Err(PyValueError::new_err("Input too large (max 20)"));
    }
    Ok((1..=n).product())
}
```

Test in Python:
```python
>>> rust_demo.factorial(21)
Traceback (most recent call last):
  ...
ValueError: Input too large (max 20)
```

---

### Exercise 3: Create a Counter Class (Intermediate)

Build a simple counter class with the following API:

```python
>>> c = rust_demo.Counter()
>>> c.increment()
>>> c.increment()
>>> c.value()
2
>>> c.decrement()
>>> c.value()
1
>>> c.reset()
>>> c.value()
0
>>> c
Counter(value=0)
```

**Starter code:**
```rust
#[pyclass]
struct Counter {
    count: i64,
}

#[pymethods]
impl Counter {
    #[new]
    fn new() -> Self {
        // Initialize to 0
    }

    fn increment(&mut self) {
        // Add 1
    }

    fn decrement(&mut self) {
        // Subtract 1
    }

    fn value(&self) -> i64 {
        // Return current count
    }

    fn reset(&mut self) {
        // Reset to 0
    }

    fn __repr__(&self) -> String {
        // Nice string representation
    }
}
```

Don't forget to register it: `m.add_class::<Counter>()?;`

---

### Exercise 4: Performance Experiment (Intermediate)

Compare Rust vs Python performance for a compute-intensive task.

**Task:** Find all prime numbers up to N using the Sieve of Eratosthenes.

1. Implement in Rust:
```rust
#[pyfunction]
fn sieve_of_eratosthenes(n: usize) -> Vec<usize> {
    if n < 2 {
        return vec![];
    }
    let mut is_prime = vec![true; n + 1];
    is_prime[0] = false;
    is_prime[1] = false;

    let mut p = 2;
    while p * p <= n {
        if is_prime[p] {
            for i in (p * p..=n).step_by(p) {
                is_prime[i] = false;
            }
        }
        p += 1;
    }

    (2..=n).filter(|&i| is_prime[i]).collect()
}
```

2. Implement the same in Python
3. Time both with `N = 1_000_000`
4. How much faster is Rust?

---

## Build Configuration Explained

### Cargo.toml Deep Dive

```toml
[lib]
crate-type = ["cdylib"]
```

**`cdylib`** creates a C-compatible dynamic library. This is what Python's import machinery expects—a `.so` file (Linux/Mac) or `.pyd` file (Windows) that exposes C-style symbols.

```toml
[dependencies.pyo3]
features = ["extension-module", "abi3-py39"]
```

**`extension-module`** — Required for building Python extensions. Handles platform-specific linking.

**`abi3-py39`** — Uses Python's stable ABI (Application Binary Interface). Benefits:
- One compiled binary works with Python 3.9, 3.10, 3.11, 3.12, etc.
- No need to rebuild for each Python version
- Trade-off: Some advanced features unavailable

### pyproject.toml Deep Dive

```toml
[build-system]
requires = ["maturin>=1.5,<2.0"]
build-backend = "maturin"
```

This tells pip/uv: "To build this package, use maturin." When someone runs `pip install .` or `uv sync`, the build system:
1. Installs maturin in an isolated environment
2. Runs maturin to compile the Rust code
3. Creates a wheel with the compiled extension

```toml
[tool.uv]
cache-keys = [
    { file = "pyproject.toml" },
    { file = "Cargo.toml" },
    { file = "**/*.rs" }
]
```

This tells uv to check if any Rust files have changed before running commands. If they have, uv automatically rebuilds. Without this, you'd need to manually run `maturin develop` after every Rust change.

---

## Real-World PyO3 Projects

These production projects demonstrate PyO3 at scale:

### polars
High-performance DataFrame library. Benchmarks show it outperforming pandas on many operations, especially with large datasets.
- https://pola.rs
- https://github.com/pola-rs/polars

### pydantic-core
The validation engine powering pydantic v2. The Rust rewrite made pydantic v2 up to 50x faster than v1 for some operations.
- https://github.com/pydantic/pydantic-core

### ruff
Python linter and formatter. Consistently 10-100x faster than existing Python-based tools like flake8, pylint, and black.
- https://github.com/astral-sh/ruff

### cryptography
Python's go-to library for cryptographic primitives. The core implementation uses Rust for memory-safe cryptographic operations.
- https://github.com/pyca/cryptography

---

## When to Use Rust Extensions

Rust extensions shine for:

**Good candidates:**
- CPU-bound numerical computation
- Parsing and data transformation
- Algorithms with tight loops
- Memory-intensive data structures
- Anything that benefits from true parallelism

**Probably not worth it:**
- I/O-bound code (network, disk)
- Simple CRUD operations
- Code that's already fast enough
- Prototyping and rapid iteration

**The overhead consideration:**
There's always some overhead crossing the Python-Rust boundary. For tiny operations called millions of times, this overhead can dominate. Batch your operations when possible—pass a list of 1000 items rather than calling a function 1000 times.

---

## Resources

### Official Documentation
- **PyO3 User Guide**: https://pyo3.rs
- **Maturin Documentation**: https://maturin.rs
- **uv Documentation**: https://docs.astral.sh/uv

### Learning Rust
- **The Rust Book**: https://doc.rust-lang.org/book/ (free, comprehensive)
- **Rust by Example**: https://doc.rust-lang.org/rust-by-example/
- **Rustlings**: https://github.com/rust-lang/rustlings (interactive exercises)

### This Demo
- Repository: [your-repo-link-here]
- Contains all code shown in this presentation
- MIT licensed—use it as a starting point for your own projects

---

## Summary

You've learned:

1. **Why Rust** — Performance, safety, and no GIL
2. **The toolchain** — PyO3 for bindings, Maturin for building
3. **Rust basics** — Variables, functions, structs, Result/Option
4. **Functions** — `#[pyfunction]` with automatic type conversion
5. **Error handling** — `PyResult<T>` and Python exceptions
6. **Classes** — `#[pyclass]` and `#[pymethods]` for stateful objects
7. **Build configuration** — Cargo.toml and pyproject.toml setup

The path forward:
1. Start with a performance-critical function in your codebase
2. Rewrite it in Rust with PyO3
3. Benchmark to verify the improvement
4. Gradually expand as you learn more Rust

Happy coding! 🦀🐍
