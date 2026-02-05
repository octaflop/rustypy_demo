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

    # -------------------------------------------------------------------------
    # Example 6: Parallel Computation
    # -------------------------------------------------------------------------
    print("\n📌 Example 6: Parallel Computation (rayon)")
    print("-" * 40)

    large_list = list(range(1, 10_000_001))

    # Parallel sum vs Python sum
    start = time.perf_counter()
    rust_par_sum = rust_demo.parallel_sum(large_list)
    rust_par_time = time.perf_counter() - start

    start = time.perf_counter()
    py_sum_result = sum(large_list)
    py_sum_time = time.perf_counter() - start

    print("Parallel sum of 10M integers:")
    print(f"  Rust (rayon): {rust_par_sum:>20,} in {rust_par_time * 1000:>8.3f}ms")
    print(f"  Python sum(): {py_sum_result:>20,} in {py_sum_time * 1000:>8.3f}ms")

    # Prime sieve
    prime_n = 1_000_000
    start = time.perf_counter()
    primes = rust_demo.prime_sieve(prime_n)
    rust_sieve_time = time.perf_counter() - start

    def py_prime_sieve(n):
        sieve = [True] * (n + 1)
        sieve[0] = sieve[1] = False
        for i in range(2, int(n**0.5) + 1):
            if sieve[i]:
                for j in range(i * i, n + 1, i):
                    sieve[j] = False
        return [i for i, is_p in enumerate(sieve) if is_p]

    start = time.perf_counter()
    py_primes = py_prime_sieve(prime_n)
    py_sieve_time = time.perf_counter() - start

    print(f"\nPrime sieve up to {prime_n:,}:")
    print(f"  Rust:   {len(primes):>8,} primes in {rust_sieve_time * 1000:>8.3f}ms")
    print(f"  Python: {len(py_primes):>8,} primes in {py_sieve_time * 1000:>8.3f}ms")
    print(f"  Rust is {py_sieve_time / rust_sieve_time:.1f}x faster!")

    # Boundary crossing cost lesson
    start = time.perf_counter()
    _primes_vec = rust_demo.prime_sieve(prime_n)
    sieve_vec_time = time.perf_counter() - start

    start = time.perf_counter()
    rust_demo.count_primes(prime_n)
    count_time = time.perf_counter() - start

    print(f"\nBoundary-crossing cost (primes up to {prime_n:,}):")
    print(
        f"  prime_sieve (returns {len(primes):,} items): {sieve_vec_time * 1000:>8.3f}ms"
    )
    print(f"  count_primes (returns 1 int):       {count_time * 1000:>8.3f}ms")
    print(f"  Returning the count is {sieve_vec_time / count_time:.1f}x faster!")

    # -------------------------------------------------------------------------
    # Example 7: Matrix Multiplication
    # -------------------------------------------------------------------------
    print("\n📌 Example 7: Matrix Multiplication")
    print("-" * 40)

    size = 200
    a = [random.random() for _ in range(size * size)]
    b = [random.random() for _ in range(size * size)]

    start = time.perf_counter()
    rust_result = rust_demo.matrix_multiply(a, b, size, size, size)
    rust_mat_time = time.perf_counter() - start

    def py_matrix_multiply(a, b, n):
        result = [0.0] * (n * n)
        for i in range(n):
            for k in range(n):
                a_ik = a[i * n + k]
                for j in range(n):
                    result[i * n + j] += a_ik * b[k * n + j]
        return result

    start = time.perf_counter()
    py_mat_result = py_matrix_multiply(a, b, size)
    py_mat_time = time.perf_counter() - start

    print(f"{size}x{size} matrix multiply:")
    print(f"  Rust:   {rust_mat_time * 1000:>10.3f}ms")
    print(f"  Python: {py_mat_time * 1000:>10.3f}ms")
    print(f"  Rust is {py_mat_time / rust_mat_time:.1f}x faster!")
    print(f"  Result[0] match: Rust={rust_result[0]:.6f} Python={py_mat_result[0]:.6f}")

    # -------------------------------------------------------------------------
    # Example 8: Text Processing
    # -------------------------------------------------------------------------
    print("\n📌 Example 8: Text Processing")
    print("-" * 40)

    test_titles = [
        "Hello, World! This is a Test.",
        "Rust + Python = 🎉 Awesome!!!",
        "  Leading/Trailing Spaces  ",
        "CamelCase meetup_SLC-2025",
    ]
    for title in test_titles:
        slug = rust_demo.slugify(title)
        print(f"  slugify({title!r})")
        print(f"    → {slug!r}")

    email_text = (
        "Contact us at hello@example.com or support@rust-lang.org. "
        "Also try user.name+tag@sub.domain.co.uk for fun. "
        "Not an email: @nobody or broken@"
    )
    emails = rust_demo.extract_emails(email_text)
    print("\nExtracted emails from text:")
    for email in emails:
        print(f"  → {email}")

    # -------------------------------------------------------------------------
    # Example 9: SortedSet
    # -------------------------------------------------------------------------
    print("\n📌 Example 9: SortedSet Class")
    print("-" * 40)

    ss = rust_demo.SortedSet()
    for val in [50, 20, 80, 10, 60, 30, 90, 40, 70]:
        inserted = ss.insert(val)
        print(f"  insert({val}): new={inserted}, len={len(ss)}")

    print(f"\n  Sorted: {ss.to_list()}")
    print(f"  contains(50): {ss.contains(50)}")
    print(f"  contains(55): {ss.contains(55)}")
    print(f"  range(25, 65): {ss.range(25, 65)}")

    # Remove and re-check
    removed = ss.remove(50)
    print(f"\n  remove(50): was_present={removed}")
    print(f"  After removal: {ss.to_list()}")
    print(f"  {ss}")

    # -------------------------------------------------------------------------
    # Example 10: SHA-256
    # -------------------------------------------------------------------------
    print("\n📌 Example 10: SHA-256 Hashing")
    print("-" * 40)

    import hashlib

    test_data = "Hello, Rust + Python!"
    rust_hash = rust_demo.sha256_hex(test_data)
    py_hash = hashlib.sha256(test_data.encode()).hexdigest()
    print(f"  Input: {test_data!r}")
    print(f"  Rust SHA-256:   {rust_hash}")
    print(f"  Python SHA-256: {py_hash}")
    print(f"  Match: {rust_hash == py_hash}")

    # Benchmark on larger data
    big_data = "x" * 10_000_000

    start = time.perf_counter()
    _rust_h = rust_demo.sha256_hex(big_data)
    rust_hash_time = time.perf_counter() - start

    start = time.perf_counter()
    _py_h = hashlib.sha256(big_data.encode()).hexdigest()
    py_hash_time = time.perf_counter() - start

    print("\n  SHA-256 of 10MB string:")
    print(f"  Rust:   {rust_hash_time * 1000:>8.3f}ms")
    print(f"  Python: {py_hash_time * 1000:>8.3f}ms")
    print("  (Both use compiled C/Rust — similar speed expected)")

    print("\n" + "=" * 60)
    print("✅ Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
