use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use rayon::prelude::*;
use sha2::{Digest, Sha256};
use std::collections::HashMap;

// ============================================================================
// EXAMPLE 1: Simple Functions
// ============================================================================

/// Compute the nth Fibonacci number iteratively
/// Much faster than Python's recursive implementation!
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

/// Count unique words in a string (case-insensitive)
#[pyfunction]
fn count_unique_words(text: &str) -> usize {
    text.split_whitespace()
        .map(|w| w.to_lowercase())
        .collect::<std::collections::HashSet<_>>()
        .len()
}

/// Check if a string is a palindrome (ignoring spaces and case)
#[pyfunction]
fn is_palindrome(s: &str) -> bool {
    let cleaned: String = s
        .chars()
        .filter(|c| c.is_alphanumeric())
        .map(|c| c.to_ascii_lowercase())
        .collect();

    let reversed: String = cleaned.chars().rev().collect();
    cleaned == reversed
}

// ============================================================================
// EXAMPLE 2: Error Handling
// ============================================================================

/// Parse a string as an integer with proper error handling
#[pyfunction]
fn safe_parse_int(s: &str) -> PyResult<i64> {
    s.trim()
        .parse::<i64>()
        .map_err(|e| PyValueError::new_err(format!("Cannot parse '{}': {}", s, e)))
}

/// Divide two numbers, raising Python exception on division by zero
#[pyfunction]
fn safe_divide(a: f64, b: f64) -> PyResult<f64> {
    if b == 0.0 {
        Err(PyValueError::new_err("Division by zero"))
    } else {
        Ok(a / b)
    }
}

// ============================================================================
// EXAMPLE 3: Working with Collections
// ============================================================================

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

/// Create a frequency map from a list of strings
#[pyfunction]
fn word_frequencies(words: Vec<String>) -> HashMap<String, u64> {
    let mut freq = HashMap::new();
    for word in words {
        *freq.entry(word.to_lowercase()).or_insert(0) += 1;
    }
    freq
}

// ============================================================================
// EXAMPLE 4: A Python Class Implemented in Rust
// ============================================================================

/// A simple moving average calculator
/// Demonstrates how to create stateful Python objects in Rust
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

        // Keep only the last `window_size` values
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

// ============================================================================
// EXAMPLE 5: A More Complex Class - Ring Buffer
// ============================================================================

/// A fixed-size ring buffer (circular buffer)
/// Useful for streaming data processing
#[pyclass]
struct RingBuffer {
    buffer: Vec<f64>,
    capacity: usize,
    head: usize,
    len: usize,
}

#[pymethods]
impl RingBuffer {
    #[new]
    fn new(capacity: usize) -> PyResult<Self> {
        if capacity == 0 {
            return Err(PyValueError::new_err("Capacity must be positive"));
        }
        Ok(RingBuffer {
            buffer: vec![0.0; capacity],
            capacity,
            head: 0,
            len: 0,
        })
    }

    /// Push a value into the buffer
    fn push(&mut self, value: f64) {
        self.buffer[self.head] = value;
        self.head = (self.head + 1) % self.capacity;
        if self.len < self.capacity {
            self.len += 1;
        }
    }

    /// Get all values as a list (in insertion order)
    fn to_list(&self) -> Vec<f64> {
        if self.len < self.capacity {
            self.buffer[..self.len].to_vec()
        } else {
            let mut result = Vec::with_capacity(self.capacity);
            for i in 0..self.capacity {
                let idx = (self.head + i) % self.capacity;
                result.push(self.buffer[idx]);
            }
            result
        }
    }

    /// Get the most recent value
    fn latest(&self) -> Option<f64> {
        if self.len == 0 {
            None
        } else {
            let idx = if self.head == 0 {
                self.capacity - 1
            } else {
                self.head - 1
            };
            Some(self.buffer[idx])
        }
    }

    /// Check if buffer is full
    fn is_full(&self) -> bool {
        self.len == self.capacity
    }

    fn __len__(&self) -> usize {
        self.len
    }

    fn __repr__(&self) -> String {
        format!("RingBuffer(capacity={}, len={})", self.capacity, self.len)
    }
}

// ============================================================================
// EXAMPLE 6: Parallel Computation (rayon)
// ============================================================================

/// Sum a list of integers using rayon parallel iterators with GIL released
#[pyfunction]
fn parallel_sum(py: Python<'_>, items: Vec<i64>) -> i64 {
    py.allow_threads(|| items.par_iter().sum())
}

/// Sieve of Eratosthenes — returns all primes up to n
#[pyfunction]
fn prime_sieve(py: Python<'_>, n: usize) -> Vec<usize> {
    py.allow_threads(|| {
        if n < 2 {
            return vec![];
        }
        let mut is_prime = vec![true; n + 1];
        is_prime[0] = false;
        is_prime[1] = false;
        let limit = (n as f64).sqrt() as usize;
        for i in 2..=limit {
            if is_prime[i] {
                let mut j = i * i;
                while j <= n {
                    is_prime[j] = false;
                    j += i;
                }
            }
        }
        is_prime
            .iter()
            .enumerate()
            .filter_map(|(i, &prime)| if prime { Some(i) } else { None })
            .collect()
    })
}

/// Count primes up to n (same sieve, but returns only the count)
/// Demonstrates boundary-crossing cost: returning a count is much cheaper
/// than returning 1M items across the Rust→Python boundary.
#[pyfunction]
fn count_primes(py: Python<'_>, n: usize) -> usize {
    py.allow_threads(|| {
        if n < 2 {
            return 0;
        }
        let mut is_prime = vec![true; n + 1];
        is_prime[0] = false;
        is_prime[1] = false;
        let limit = (n as f64).sqrt() as usize;
        for i in 2..=limit {
            if is_prime[i] {
                let mut j = i * i;
                while j <= n {
                    is_prime[j] = false;
                    j += i;
                }
            }
        }
        is_prime.iter().filter(|&&p| p).count()
    })
}

// ============================================================================
// EXAMPLE 7: Matrix Multiplication
// ============================================================================

/// Multiply two matrices stored as flat vectors (row-major order).
/// Uses cache-friendly i-k-j loop ordering.
#[pyfunction]
fn matrix_multiply(
    py: Python<'_>,
    a: Vec<f64>,
    b: Vec<f64>,
    rows_a: usize,
    cols_a: usize,
    cols_b: usize,
) -> PyResult<Vec<f64>> {
    if a.len() != rows_a * cols_a {
        return Err(PyValueError::new_err(format!(
            "Matrix A size mismatch: expected {} elements, got {}",
            rows_a * cols_a,
            a.len()
        )));
    }
    if b.len() != cols_a * cols_b {
        return Err(PyValueError::new_err(format!(
            "Matrix B size mismatch: expected {} elements, got {}",
            cols_a * cols_b,
            b.len()
        )));
    }

    Ok(py.allow_threads(|| {
        let mut result = vec![0.0; rows_a * cols_b];
        // Cache-friendly i-k-j ordering
        for i in 0..rows_a {
            for k in 0..cols_a {
                let a_ik = a[i * cols_a + k];
                for j in 0..cols_b {
                    result[i * cols_b + j] += a_ik * b[k * cols_b + j];
                }
            }
        }
        result
    }))
}

// ============================================================================
// EXAMPLE 8: Text Processing
// ============================================================================

/// Convert arbitrary text to a URL-friendly slug
#[pyfunction]
fn slugify(text: &str) -> String {
    let mut slug = String::with_capacity(text.len());
    let mut last_was_dash = true; // prevent leading dash

    for ch in text.chars() {
        if ch.is_ascii_alphanumeric() {
            slug.push(ch.to_ascii_lowercase());
            last_was_dash = false;
        } else if !last_was_dash {
            slug.push('-');
            last_was_dash = true;
        }
    }

    // Remove trailing dash
    if slug.ends_with('-') {
        slug.pop();
    }
    slug
}

/// Extract email-like patterns from text via manual character scanning
#[pyfunction]
fn extract_emails(text: &str) -> Vec<String> {
    let mut emails = Vec::new();
    let chars: Vec<char> = text.chars().collect();
    let len = chars.len();

    for i in 0..len {
        if chars[i] == '@' && i > 0 && i < len - 1 {
            // Scan backwards for local part
            let mut start = i;
            while start > 0 {
                let ch = chars[start - 1];
                if ch.is_ascii_alphanumeric() || ch == '.' || ch == '_' || ch == '-' || ch == '+' {
                    start -= 1;
                } else {
                    break;
                }
            }

            // Scan forwards for domain part
            let mut end = i + 1;
            let mut has_dot = false;
            while end < len {
                let ch = chars[end];
                if ch.is_ascii_alphanumeric() || ch == '.' || ch == '-' {
                    if ch == '.' {
                        has_dot = true;
                    }
                    end += 1;
                } else {
                    break;
                }
            }

            // Validate: must have local part, domain, and at least one dot in domain
            if start < i && end > i + 1 && has_dot {
                let email: String = chars[start..end].iter().collect();
                // Trim trailing dots
                let email = email.trim_end_matches('.').to_string();
                if !emails.contains(&email) {
                    emails.push(email);
                }
            }
        }
    }
    emails
}

// ============================================================================
// EXAMPLE 9: SortedSet Class
// ============================================================================

/// A sorted set backed by a Vec with binary search.
/// Python has no built-in sorted set — this shows advanced #[pymethods].
#[pyclass]
struct SortedSet {
    data: Vec<i64>,
}

#[pymethods]
impl SortedSet {
    #[new]
    fn new() -> Self {
        SortedSet { data: Vec::new() }
    }

    /// Insert a value. Returns true if it was newly inserted.
    fn insert(&mut self, value: i64) -> bool {
        match self.data.binary_search(&value) {
            Ok(_) => false, // already present
            Err(pos) => {
                self.data.insert(pos, value);
                true
            }
        }
    }

    /// Check if value is in the set.
    fn contains(&self, value: i64) -> bool {
        self.data.binary_search(&value).is_ok()
    }

    /// Remove a value. Returns true if it was present.
    fn remove(&mut self, value: i64) -> bool {
        match self.data.binary_search(&value) {
            Ok(pos) => {
                self.data.remove(pos);
                true
            }
            Err(_) => false,
        }
    }

    /// Return all elements as a sorted list.
    fn to_list(&self) -> Vec<i64> {
        self.data.clone()
    }

    /// Return elements in [low, high] inclusive.
    fn range(&self, low: i64, high: i64) -> Vec<i64> {
        let start = match self.data.binary_search(&low) {
            Ok(pos) => pos,
            Err(pos) => pos,
        };
        let end = match self.data.binary_search(&high) {
            Ok(pos) => pos + 1,
            Err(pos) => pos,
        };
        self.data[start..end].to_vec()
    }

    fn __len__(&self) -> usize {
        self.data.len()
    }

    fn __contains__(&self, value: i64) -> bool {
        self.contains(value)
    }

    fn __repr__(&self) -> String {
        if self.data.len() <= 10 {
            format!("SortedSet({:?})", self.data)
        } else {
            format!(
                "SortedSet([{}, ... {} items])",
                self.data[0],
                self.data.len()
            )
        }
    }
}

// ============================================================================
// EXAMPLE 10: Byte Operations (sha2)
// ============================================================================

/// Compute the SHA-256 hex digest of a string
#[pyfunction]
fn sha256_hex(data: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data.as_bytes());
    format!("{:x}", hasher.finalize())
}

// ============================================================================
// MODULE DEFINITION
// ============================================================================

/// A Python module demonstrating Rust-Python integration with PyO3
#[pymodule]
fn rust_demo(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Add functions
    m.add_function(wrap_pyfunction!(fibonacci, m)?)?;
    m.add_function(wrap_pyfunction!(count_unique_words, m)?)?;
    m.add_function(wrap_pyfunction!(is_palindrome, m)?)?;
    m.add_function(wrap_pyfunction!(safe_parse_int, m)?)?;
    m.add_function(wrap_pyfunction!(safe_divide, m)?)?;
    m.add_function(wrap_pyfunction!(sum_list, m)?)?;
    m.add_function(wrap_pyfunction!(filter_positive, m)?)?;
    m.add_function(wrap_pyfunction!(word_frequencies, m)?)?;

    m.add_function(wrap_pyfunction!(parallel_sum, m)?)?;
    m.add_function(wrap_pyfunction!(prime_sieve, m)?)?;
    m.add_function(wrap_pyfunction!(count_primes, m)?)?;
    m.add_function(wrap_pyfunction!(matrix_multiply, m)?)?;
    m.add_function(wrap_pyfunction!(slugify, m)?)?;
    m.add_function(wrap_pyfunction!(extract_emails, m)?)?;
    m.add_function(wrap_pyfunction!(sha256_hex, m)?)?;

    // Add classes
    m.add_class::<MovingAverage>()?;
    m.add_class::<RingBuffer>()?;
    m.add_class::<SortedSet>()?;

    Ok(())
}
