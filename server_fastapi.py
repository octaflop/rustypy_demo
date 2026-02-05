#!/usr/bin/env python3
"""
FastAPI variant of the Rust-Python demo server.

Shows the "production" pattern: Rust for compute, Python for web framework.
Exposes all functions as typed endpoints with Pydantic models and auto-generated
OpenAPI docs.

Run with:
    uv pip install -e ".[web]"
    uv run python server_fastapi.py

Then visit http://localhost:8000/docs for the interactive API docs.
"""

import hashlib
import random
import time

import rust_demo
from fastapi import FastAPI
from pydantic import BaseModel, Field
from uvicorn import run as uvicorn_run

app = FastAPI(
    title="Rust-Python Demo API",
    description="Rust extension functions exposed via FastAPI with typed endpoints",
    version="0.1.0",
)


# ============================================================================
# Request/Response Models
# ============================================================================


class FibonacciRequest(BaseModel):
    n: int = Field(
        ge=0, le=90, default=40, description="Which Fibonacci number to compute"
    )


class FibonacciResponse(BaseModel):
    n: int
    result: int
    rust_ms: float
    python_ms: float
    speedup: float


class PalindromeRequest(BaseModel):
    text: str = "A man a plan a canal Panama"


class PalindromeResponse(BaseModel):
    text: str
    is_palindrome: bool


class UniqueWordsRequest(BaseModel):
    text: str = "The quick brown fox jumps over the lazy dog the fox"


class UniqueWordsResponse(BaseModel):
    text: str
    count: int


class ParseIntRequest(BaseModel):
    text: str = "42"


class ParseIntResponse(BaseModel):
    text: str
    result: int | None
    error: str | None


class DivideRequest(BaseModel):
    a: float = 10.0
    b: float = 3.0


class DivideResponse(BaseModel):
    a: float
    b: float
    result: float | None
    error: str | None


class SumListRequest(BaseModel):
    numbers: list[int] = [1, -2, 3, -4, 5, -6, 7, -8, 9, -10]


class SumListResponse(BaseModel):
    result: int
    count: int
    rust_ms: float
    python_ms: float


class FilterPositiveRequest(BaseModel):
    numbers: list[int] = [1, -2, 3, -4, 5, -6, 7]


class FilterPositiveResponse(BaseModel):
    input: list[int]
    result: list[int]


class WordFreqRequest(BaseModel):
    words: list[str] = ["apple", "Banana", "APPLE", "cherry", "banana", "Apple"]


class WordFreqResponse(BaseModel):
    words: list[str]
    frequencies: dict[str, int]


class ParallelSumRequest(BaseModel):
    size: int = Field(default=10_000_000, ge=1, le=50_000_000)


class ParallelSumResponse(BaseModel):
    size: int
    result: int
    rust_ms: float
    python_ms: float
    speedup: float


class PrimeSieveRequest(BaseModel):
    n: int = Field(default=1_000_000, ge=2, le=10_000_000)
    mode: str = Field(default="count", pattern="^(count|list)$")


class PrimeSieveResponse(BaseModel):
    n: int
    count: int
    mode: str
    rust_ms: float
    python_ms: float
    speedup: float


class MatrixMultiplyRequest(BaseModel):
    size: int = Field(default=100, ge=2, le=500)


class MatrixMultiplyResponse(BaseModel):
    size: int
    rust_ms: float
    python_ms: float | None
    speedup: float | None


class SlugifyRequest(BaseModel):
    text: str = "Hello, World! This is a Test."


class SlugifyResponse(BaseModel):
    text: str
    slug: str


class ExtractEmailsRequest(BaseModel):
    text: str = "Contact hello@example.com or support@rust-lang.org"


class ExtractEmailsResponse(BaseModel):
    text: str
    emails: list[str]
    count: int


class Sha256Request(BaseModel):
    text: str = "Hello, Rust + Python!"


class Sha256Response(BaseModel):
    text_length: int
    hash: str
    match_: bool = Field(alias="match")
    rust_ms: float
    python_ms: float

    model_config = {"populate_by_name": True}


# ============================================================================
# Python comparison functions
# ============================================================================


def py_fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def py_prime_sieve(n: int) -> list[int]:
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i, is_p in enumerate(sieve) if is_p]


def py_matrix_multiply(a: list[float], b: list[float], n: int) -> list[float]:
    result = [0.0] * (n * n)
    for i in range(n):
        for k in range(n):
            a_ik = a[i * n + k]
            for j in range(n):
                result[i * n + j] += a_ik * b[k * n + j]
    return result


# ============================================================================
# Endpoints
# ============================================================================


@app.post("/fibonacci", response_model=FibonacciResponse)
def fibonacci(req: FibonacciRequest):
    start = time.perf_counter()
    result = rust_demo.fibonacci(req.n)
    rust_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    py_fibonacci(req.n)
    python_ms = (time.perf_counter() - start) * 1000

    return FibonacciResponse(
        n=req.n,
        result=result,
        rust_ms=round(rust_ms, 4),
        python_ms=round(python_ms, 4),
        speedup=round(python_ms / rust_ms, 1) if rust_ms > 0 else 0,
    )


@app.post("/palindrome", response_model=PalindromeResponse)
def palindrome(req: PalindromeRequest):
    return PalindromeResponse(
        text=req.text, is_palindrome=rust_demo.is_palindrome(req.text)
    )


@app.post("/unique_words", response_model=UniqueWordsResponse)
def unique_words(req: UniqueWordsRequest):
    return UniqueWordsResponse(
        text=req.text, count=rust_demo.count_unique_words(req.text)
    )


@app.post("/parse_int", response_model=ParseIntResponse)
def parse_int(req: ParseIntRequest):
    try:
        result = rust_demo.safe_parse_int(req.text)
        return ParseIntResponse(text=req.text, result=result, error=None)
    except ValueError as e:
        return ParseIntResponse(text=req.text, result=None, error=str(e))


@app.post("/divide", response_model=DivideResponse)
def divide(req: DivideRequest):
    try:
        result = rust_demo.safe_divide(req.a, req.b)
        return DivideResponse(a=req.a, b=req.b, result=result, error=None)
    except ValueError as e:
        return DivideResponse(a=req.a, b=req.b, result=None, error=str(e))


@app.post("/sum_list", response_model=SumListResponse)
def sum_list(req: SumListRequest):
    start = time.perf_counter()
    result = rust_demo.sum_list(req.numbers)
    rust_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    sum(req.numbers)
    python_ms = (time.perf_counter() - start) * 1000

    return SumListResponse(
        result=result,
        count=len(req.numbers),
        rust_ms=round(rust_ms, 4),
        python_ms=round(python_ms, 4),
    )


@app.post("/filter_positive", response_model=FilterPositiveResponse)
def filter_positive(req: FilterPositiveRequest):
    return FilterPositiveResponse(
        input=req.numbers, result=rust_demo.filter_positive(req.numbers)
    )


@app.post("/word_freq", response_model=WordFreqResponse)
def word_freq(req: WordFreqRequest):
    return WordFreqResponse(
        words=req.words, frequencies=rust_demo.word_frequencies(req.words)
    )


@app.post("/parallel_sum", response_model=ParallelSumResponse)
def parallel_sum(req: ParallelSumRequest):
    items = list(range(1, req.size + 1))

    start = time.perf_counter()
    result = rust_demo.parallel_sum(items)
    rust_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    sum(items)
    python_ms = (time.perf_counter() - start) * 1000

    return ParallelSumResponse(
        size=req.size,
        result=result,
        rust_ms=round(rust_ms, 4),
        python_ms=round(python_ms, 4),
        speedup=round(python_ms / rust_ms, 1) if rust_ms > 0 else 0,
    )


@app.post("/prime_sieve", response_model=PrimeSieveResponse)
def prime_sieve(req: PrimeSieveRequest):
    start = time.perf_counter()
    if req.mode == "list":
        primes = rust_demo.prime_sieve(req.n)
        rust_ms = (time.perf_counter() - start) * 1000
        count = len(primes)
    else:
        count = rust_demo.count_primes(req.n)
        rust_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    py_prime_sieve(req.n)
    python_ms = (time.perf_counter() - start) * 1000

    return PrimeSieveResponse(
        n=req.n,
        count=count,
        mode=req.mode,
        rust_ms=round(rust_ms, 4),
        python_ms=round(python_ms, 4),
        speedup=round(python_ms / rust_ms, 1) if rust_ms > 0 else 0,
    )


@app.post("/matrix_multiply", response_model=MatrixMultiplyResponse)
def matrix_multiply(req: MatrixMultiplyRequest):
    a = [random.random() for _ in range(req.size * req.size)]
    b = [random.random() for _ in range(req.size * req.size)]

    start = time.perf_counter()
    rust_demo.matrix_multiply(a, b, req.size, req.size, req.size)
    rust_ms = (time.perf_counter() - start) * 1000

    python_ms = None
    speedup = None
    if req.size <= 150:
        start = time.perf_counter()
        py_matrix_multiply(a, b, req.size)
        python_ms = round((time.perf_counter() - start) * 1000, 4)
        speedup = round(python_ms / rust_ms, 1) if rust_ms > 0 else None

    return MatrixMultiplyResponse(
        size=req.size,
        rust_ms=round(rust_ms, 4),
        python_ms=python_ms,
        speedup=speedup,
    )


@app.post("/slugify", response_model=SlugifyResponse)
def slugify(req: SlugifyRequest):
    return SlugifyResponse(text=req.text, slug=rust_demo.slugify(req.text))


@app.post("/extract_emails", response_model=ExtractEmailsResponse)
def extract_emails(req: ExtractEmailsRequest):
    emails = rust_demo.extract_emails(req.text)
    return ExtractEmailsResponse(text=req.text, emails=emails, count=len(emails))


@app.post("/sha256", response_model=Sha256Response)
def sha256(req: Sha256Request):
    start = time.perf_counter()
    rust_hash = rust_demo.sha256_hex(req.text)
    rust_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    py_hash = hashlib.sha256(req.text.encode()).hexdigest()
    python_ms = (time.perf_counter() - start) * 1000

    return Sha256Response(
        text_length=len(req.text),
        hash=rust_hash,
        match_=rust_hash == py_hash,
        rust_ms=round(rust_ms, 4),
        python_ms=round(python_ms, 4),
    )


if __name__ == "__main__":
    print("Starting FastAPI server...")
    print("Visit http://localhost:8000/docs for interactive API docs")
    uvicorn_run(app, host="localhost", port=8000)
