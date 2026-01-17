use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
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

    // Add classes
    m.add_class::<MovingAverage>()?;
    m.add_class::<RingBuffer>()?;

    Ok(())
}
