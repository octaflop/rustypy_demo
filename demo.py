#!/usr/bin/env python3
"""
Demo script showing how to use the Rust extension.

Run with: uv run python demo.py
Or after `maturin develop`: python demo.py
"""

import time


def main():
    # Import our Rust module
    import rust_demo

    print("=" * 60)
    print("🦀 Rust-Python Integration Demo 🐍")
    print("=" * 60)

    # -------------------------------------------------------------------------
    # Example 1: Simple Functions
    # -------------------------------------------------------------------------
    print("\n📌 Example 1: Simple Functions")
    print("-" * 40)

    # Fibonacci
    n = 40
    start = time.perf_counter()
    result = rust_demo.fibonacci(n)
    elapsed = time.perf_counter() - start
    print(f"fibonacci({n}) = {result} (took {elapsed * 1000:.3f}ms)")

    # Compare with Python implementation
    def py_fibonacci(n):
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(2, n + 1):
            a, b = b, a + b
        return b

    start = time.perf_counter()
    py_result = py_fibonacci(n)
    py_elapsed = time.perf_counter() - start
    print(f"Python fibonacci({n}) = {py_result} (took {py_elapsed * 1000:.3f}ms)")
    print(f"Rust is {py_elapsed / elapsed:.1f}x faster!")

    # Unique words
    text = "The quick brown fox jumps over the lazy dog the fox was quick"
    unique = rust_demo.count_unique_words(text)
    print(f"\nUnique words in text: {unique}")

    # Palindrome check
    test_strings = ["A man a plan a canal Panama", "hello", "racecar", "Python"]
    for s in test_strings:
        result = rust_demo.is_palindrome(s)
        print(f"is_palindrome('{s}'): {result}")

    # -------------------------------------------------------------------------
    # Example 2: Error Handling
    # -------------------------------------------------------------------------
    print("\n📌 Example 2: Error Handling")
    print("-" * 40)

    # Safe parsing
    print(f"safe_parse_int('42') = {rust_demo.safe_parse_int('42')}")
    print(f"safe_parse_int('  -123  ') = {rust_demo.safe_parse_int('  -123  ')}")

    try:
        rust_demo.safe_parse_int("not a number")
    except ValueError as e:
        print(f"safe_parse_int('not a number') raised: {e}")

    # Safe division
    print(f"\nsafe_divide(10, 3) = {rust_demo.safe_divide(10, 3):.4f}")

    try:
        rust_demo.safe_divide(10, 0)
    except ValueError as e:
        print(f"safe_divide(10, 0) raised: {e}")

    # -------------------------------------------------------------------------
    # Example 3: Working with Collections
    # -------------------------------------------------------------------------
    print("\n📌 Example 3: Working with Collections")
    print("-" * 40)

    numbers = [1, -2, 3, -4, 5, -6, 7, -8, 9, -10]
    print(f"Original: {numbers}")
    print(f"sum_list: {rust_demo.sum_list(numbers)}")
    print(f"filter_positive: {rust_demo.filter_positive(numbers)}")

    words = ["apple", "Banana", "APPLE", "cherry", "banana", "Apple"]
    print(f"\nWords: {words}")
    print(f"word_frequencies: {rust_demo.word_frequencies(words)}")

    # -------------------------------------------------------------------------
    # Example 4: MovingAverage Class
    # -------------------------------------------------------------------------
    print("\n📌 Example 4: MovingAverage Class")
    print("-" * 40)

    ma = rust_demo.MovingAverage(3)
    print(f"Created: {ma}")

    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    for v in values:
        avg = ma.add(v)
        print(f"Added {v:.1f}, moving average: {avg:.2f}, count: {ma.count()}")

    print(f"\nFinal state: {ma}")

    # -------------------------------------------------------------------------
    # Example 5: RingBuffer Class
    # -------------------------------------------------------------------------
    print("\n📌 Example 5: RingBuffer Class")
    print("-" * 40)

    rb = rust_demo.RingBuffer(5)
    print(f"Created: {rb}")

    for i in range(1, 8):
        rb.push(float(i))
        print(f"Pushed {i}: {rb.to_list()} (len={len(rb)}, full={rb.is_full()})")

    print(f"\nLatest value: {rb.latest()}")
    print(f"Final state: {rb}")

    # -------------------------------------------------------------------------
    # Performance Comparison
    # -------------------------------------------------------------------------
    print("\n📌 Performance Comparison: Large List Sum")
    print("-" * 40)

    import random

    large_list = [random.randint(-1000, 1000) for _ in range(1_000_000)]

    # Rust
    start = time.perf_counter()
    rust_sum = rust_demo.sum_list(large_list)
    rust_time = time.perf_counter() - start

    # Python built-in
    start = time.perf_counter()
    py_sum = sum(large_list)
    py_time = time.perf_counter() - start

    print("Summing 1,000,000 integers:")
    print(f"  Rust:   {rust_sum:>15,} in {rust_time * 1000:>8.3f}ms")
    print(f"  Python: {py_sum:>15,} in {py_time * 1000:>8.3f}ms")
    print("  (Python's sum() is C-implemented, so this is a fair fight!)")

    print("\n" + "=" * 60)
    print("✅ Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
