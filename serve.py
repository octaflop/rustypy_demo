#!/usr/bin/env python3
"""
Self-Referential Web Presentation for Rust-Python Demo

This presentation serves itself while explaining how it works.
Run with: uv run python serve.py
"""

import argparse
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import rust_demo

# ============================================================================
# Session Management
# ============================================================================

SESSION_TIMEOUT = 600  # 10 minutes


class SessionManager:
    """Manages stateful objects (MovingAverage, RingBuffer) per session."""

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        with self._lock:
            self._sessions[session_id] = {
                "created": time.time(),
                "last_access": time.time(),
                "moving_avg": rust_demo.MovingAverage(5),
                "ring_buffer": rust_demo.RingBuffer(8),
                "sorted_set": rust_demo.SortedSet(),
            }
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session["last_access"] = time.time()
            return session

    def _cleanup_loop(self):
        while True:
            time.sleep(60)
            now = time.time()
            with self._lock:
                expired = [
                    sid
                    for sid, sess in self._sessions.items()
                    if now - sess["last_access"] > SESSION_TIMEOUT
                ]
                for sid in expired:
                    del self._sessions[sid]


# ============================================================================
# Server Stats
# ============================================================================


class ServerStats:
    """Tracks server statistics for the meta demo."""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.api_calls = 0
        self._lock = threading.Lock()

    def record_request(self, is_api: bool = False):
        with self._lock:
            self.request_count += 1
            if is_api:
                self.api_calls += 1

    def get_stats(self) -> dict:
        uptime = time.time() - self.start_time
        return {
            "uptime_seconds": round(uptime, 1),
            "uptime_human": self._format_uptime(uptime),
            "total_requests": self.request_count,
            "api_calls": self.api_calls,
        }

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"


# ============================================================================
# Python Comparison Functions (for timing)
# ============================================================================


def py_fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def py_sum_list(items: list[int]) -> int:
    return sum(items)


def py_prime_sieve(n: int) -> list[int]:
    if n < 2:
        return []
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
# Request Handler
# ============================================================================


class DemoHandler(BaseHTTPRequestHandler):
    sessions = SessionManager()
    stats = ServerStats()
    lib_rs_content = ""

    @classmethod
    def load_lib_rs(cls):
        lib_path = Path(__file__).parent / "lib.rs"
        if lib_path.exists():
            cls.lib_rs_content = lib_path.read_text()

    def log_message(self, format, *args):
        # Quieter logging
        pass

    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        body = self.rfile.read(length)
        return json.loads(body)

    def do_GET(self):
        self.stats.record_request()
        path = urlparse(self.path).path

        if path == "/":
            self.send_html(HTML_PAGE)
        elif path == "/api/stats":
            self.stats.record_request(is_api=True)
            self.send_json(self.stats.get_stats())
        elif path == "/api/lib.rs":
            self.stats.record_request(is_api=True)
            self.send_json({"content": self.lib_rs_content})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        self.stats.record_request(is_api=True)
        path = urlparse(self.path).path

        handlers = {
            "/api/session": self.handle_session,
            "/api/fibonacci": self.handle_fibonacci,
            "/api/palindrome": self.handle_palindrome,
            "/api/unique_words": self.handle_unique_words,
            "/api/parse_int": self.handle_parse_int,
            "/api/divide": self.handle_divide,
            "/api/sum_list": self.handle_sum_list,
            "/api/filter_positive": self.handle_filter_positive,
            "/api/word_freq": self.handle_word_freq,
            "/api/moving_avg": self.handle_moving_avg,
            "/api/ring_buffer": self.handle_ring_buffer,
            "/api/parallel_sum": self.handle_parallel_sum,
            "/api/prime_sieve": self.handle_prime_sieve,
            "/api/matrix_multiply": self.handle_matrix_multiply,
            "/api/slugify": self.handle_slugify,
            "/api/extract_emails": self.handle_extract_emails,
            "/api/sorted_set": self.handle_sorted_set,
            "/api/sha256": self.handle_sha256,
        }

        handler = handlers.get(path)
        if handler:
            try:
                handler()
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)
        else:
            self.send_response(404)
            self.end_headers()

    # -------------------------------------------------------------------------
    # API Handlers
    # -------------------------------------------------------------------------

    def handle_session(self):
        session_id = self.sessions.create_session()
        self.send_json({"session_id": session_id})

    def handle_fibonacci(self):
        data = self.read_body()
        n = int(data.get("n", 10))
        n = min(n, 90)  # Prevent overflow

        # Rust timing
        start = time.perf_counter()
        rust_result = rust_demo.fibonacci(n)
        rust_ms = (time.perf_counter() - start) * 1000

        # Python timing
        start = time.perf_counter()
        _py_result = py_fibonacci(n)
        py_ms = (time.perf_counter() - start) * 1000

        self.send_json(
            {
                "n": n,
                "result": rust_result,
                "rust_ms": round(rust_ms, 4),
                "python_ms": round(py_ms, 4),
                "speedup": round(py_ms / rust_ms, 1) if rust_ms > 0 else 0,
            }
        )

    def handle_palindrome(self):
        data = self.read_body()
        text = data.get("text", "")
        result = rust_demo.is_palindrome(text)
        self.send_json({"text": text, "is_palindrome": result})

    def handle_unique_words(self):
        data = self.read_body()
        text = data.get("text", "")
        count = rust_demo.count_unique_words(text)
        self.send_json({"text": text, "count": count})

    def handle_parse_int(self):
        data = self.read_body()
        text = data.get("text", "")
        try:
            result = rust_demo.safe_parse_int(text)
            self.send_json({"text": text, "result": result, "error": None})
        except ValueError as e:
            self.send_json({"text": text, "result": None, "error": str(e)})

    def handle_divide(self):
        data = self.read_body()
        a = float(data.get("a", 0))
        b = float(data.get("b", 1))
        try:
            result = rust_demo.safe_divide(a, b)
            self.send_json({"a": a, "b": b, "result": result, "error": None})
        except ValueError as e:
            self.send_json({"a": a, "b": b, "result": None, "error": str(e)})

    def handle_sum_list(self):
        data = self.read_body()
        numbers = [int(x) for x in data.get("numbers", [])]

        # Rust timing
        start = time.perf_counter()
        rust_result = rust_demo.sum_list(numbers)
        rust_ms = (time.perf_counter() - start) * 1000

        # Python timing
        start = time.perf_counter()
        _py_result = py_sum_list(numbers)
        py_ms = (time.perf_counter() - start) * 1000

        self.send_json(
            {
                "result": rust_result,
                "count": len(numbers),
                "rust_ms": round(rust_ms, 4),
                "python_ms": round(py_ms, 4),
            }
        )

    def handle_filter_positive(self):
        data = self.read_body()
        numbers = [int(x) for x in data.get("numbers", [])]
        result = rust_demo.filter_positive(numbers)
        self.send_json({"input": numbers, "result": result})

    def handle_word_freq(self):
        data = self.read_body()
        words = data.get("words", [])
        freq = rust_demo.word_frequencies(words)
        self.send_json({"words": words, "frequencies": freq})

    def handle_moving_avg(self):
        data = self.read_body()
        session_id = data.get("session_id", "")
        action = data.get("action", "")
        value = data.get("value", 0)

        session = self.sessions.get_session(session_id)
        if not session:
            self.send_json({"error": "Invalid session"}, status=400)
            return

        ma = session["moving_avg"]

        if action == "add":
            avg = ma.add(float(value))
            self.send_json(
                {
                    "action": "add",
                    "value": value,
                    "average": round(avg, 2),
                    "count": ma.count(),
                }
            )
        elif action == "clear":
            ma.clear()
            self.send_json({"action": "clear", "average": 0, "count": 0})
        elif action == "status":
            self.send_json(
                {
                    "action": "status",
                    "average": round(ma.average(), 2),
                    "count": ma.count(),
                }
            )
        else:
            self.send_json({"error": "Unknown action"}, status=400)

    def handle_ring_buffer(self):
        data = self.read_body()
        session_id = data.get("session_id", "")
        action = data.get("action", "")
        value = data.get("value", 0)

        session = self.sessions.get_session(session_id)
        if not session:
            self.send_json({"error": "Invalid session"}, status=400)
            return

        rb = session["ring_buffer"]

        if action == "push":
            rb.push(float(value))
            self.send_json(
                {
                    "action": "push",
                    "value": value,
                    "values": rb.to_list(),
                    "latest": rb.latest(),
                    "is_full": rb.is_full(),
                    "length": len(rb),
                }
            )
        elif action == "status":
            self.send_json(
                {
                    "action": "status",
                    "values": rb.to_list(),
                    "latest": rb.latest(),
                    "is_full": rb.is_full(),
                    "length": len(rb),
                }
            )
        else:
            self.send_json({"error": "Unknown action"}, status=400)

    def handle_parallel_sum(self):
        data = self.read_body()
        size = min(int(data.get("size", 1_000_000)), 50_000_000)
        items = list(range(1, size + 1))

        start = time.perf_counter()
        rust_result = rust_demo.parallel_sum(items)
        rust_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        py_result = sum(items)
        py_ms = (time.perf_counter() - start) * 1000

        self.send_json(
            {
                "size": size,
                "result": rust_result,
                "rust_ms": round(rust_ms, 4),
                "python_ms": round(py_ms, 4),
                "speedup": round(py_ms / rust_ms, 1) if rust_ms > 0 else 0,
                "match": rust_result == py_result,
            }
        )

    def handle_prime_sieve(self):
        data = self.read_body()
        n = min(int(data.get("n", 100_000)), 10_000_000)
        mode = data.get("mode", "count")

        start = time.perf_counter()
        if mode == "list":
            primes = rust_demo.prime_sieve(n)
            rust_ms = (time.perf_counter() - start) * 1000
            count = len(primes)
        else:
            count = rust_demo.count_primes(n)
            rust_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        py_prime_sieve(n)
        py_ms = (time.perf_counter() - start) * 1000

        self.send_json(
            {
                "n": n,
                "count": count,
                "mode": mode,
                "rust_ms": round(rust_ms, 4),
                "python_ms": round(py_ms, 4),
                "speedup": round(py_ms / rust_ms, 1) if rust_ms > 0 else 0,
            }
        )

    def handle_matrix_multiply(self):
        import random

        data = self.read_body()
        size = min(int(data.get("size", 100)), 500)

        a = [random.random() for _ in range(size * size)]
        b = [random.random() for _ in range(size * size)]

        start = time.perf_counter()
        _rust_result = rust_demo.matrix_multiply(a, b, size, size, size)
        rust_ms = (time.perf_counter() - start) * 1000

        py_ms = None
        if size <= 150:
            start = time.perf_counter()
            _py_result = py_matrix_multiply(a, b, size)
            py_ms = round((time.perf_counter() - start) * 1000, 4)

        self.send_json(
            {
                "size": size,
                "rust_ms": round(rust_ms, 4),
                "python_ms": py_ms,
                "speedup": round(py_ms / rust_ms, 1) if py_ms and rust_ms > 0 else None,
            }
        )

    def handle_slugify(self):
        data = self.read_body()
        text = data.get("text", "")
        result = rust_demo.slugify(text)
        self.send_json({"text": text, "slug": result})

    def handle_extract_emails(self):
        data = self.read_body()
        text = data.get("text", "")
        emails = rust_demo.extract_emails(text)
        self.send_json({"text": text, "emails": emails, "count": len(emails)})

    def handle_sorted_set(self):
        data = self.read_body()
        session_id = data.get("session_id", "")
        action = data.get("action", "")
        value = data.get("value", 0)

        session = self.sessions.get_session(session_id)
        if not session:
            self.send_json({"error": "Invalid session"}, status=400)
            return

        ss = session["sorted_set"]

        if action == "insert":
            inserted = ss.insert(int(value))
            self.send_json(
                {
                    "action": "insert",
                    "value": int(value),
                    "inserted": inserted,
                    "items": ss.to_list(),
                    "length": len(ss),
                }
            )
        elif action == "remove":
            removed = ss.remove(int(value))
            self.send_json(
                {
                    "action": "remove",
                    "value": int(value),
                    "removed": removed,
                    "items": ss.to_list(),
                    "length": len(ss),
                }
            )
        elif action == "contains":
            found = ss.contains(int(value))
            self.send_json({"action": "contains", "value": int(value), "found": found})
        elif action == "range":
            low = int(data.get("low", 0))
            high = int(data.get("high", 100))
            items = ss.range(low, high)
            self.send_json(
                {"action": "range", "low": low, "high": high, "items": items}
            )
        elif action == "status":
            self.send_json(
                {"action": "status", "items": ss.to_list(), "length": len(ss)}
            )
        else:
            self.send_json({"error": "Unknown action"}, status=400)

    def handle_sha256(self):
        data = self.read_body()
        text = data.get("text", "")
        import hashlib

        start = time.perf_counter()
        rust_hash = rust_demo.sha256_hex(text)
        rust_ms = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        py_hash = hashlib.sha256(text.encode()).hexdigest()
        py_ms = (time.perf_counter() - start) * 1000

        self.send_json(
            {
                "text_length": len(text),
                "hash": rust_hash,
                "match": rust_hash == py_hash,
                "rust_ms": round(rust_ms, 4),
                "python_ms": round(py_ms, 4),
            }
        )


# ============================================================================
# Embedded HTML/CSS/JS
# ============================================================================

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rust + Python: A Self-Serving Demo</title>
    <style>
        :root {
            --rust-orange: #f74c00;
            --python-blue: #3776ab;
            --python-yellow: #ffd43b;
            --bg-dark: #1a1a2e;
            --bg-card: #16213e;
            --text-primary: #eee;
            --text-muted: #888;
            --success: #4ade80;
            --error: #f87171;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }

        h1, h2, h3 { font-weight: 600; }
        h1 { font-size: 2rem; margin-bottom: 0.5rem; }
        h2 { font-size: 1.4rem; margin: 2rem 0 1rem; color: var(--rust-orange); }
        h3 { font-size: 1.1rem; margin: 1rem 0 0.5rem; }

        .hero {
            text-align: center;
            padding: 3rem 0;
            border-bottom: 1px solid #333;
            margin-bottom: 2rem;
        }

        .hero h1 {
            background: linear-gradient(135deg, var(--rust-orange), var(--python-yellow));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .meta-stats {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1.5rem;
            font-size: 0.9rem;
        }

        .stat {
            text-align: center;
        }

        .stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--python-blue);
        }

        .stat-label {
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        .card {
            background: var(--bg-card);
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1rem 0;
            border: 1px solid #333;
        }

        .stack-diagram {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.5rem;
            padding: 1rem;
        }

        .stack-item {
            padding: 0.75rem 2rem;
            border-radius: 4px;
            text-align: center;
            width: 200px;
        }

        .stack-browser { background: #333; }
        .stack-python { background: var(--python-blue); }
        .stack-rust { background: var(--rust-orange); }
        .stack-arrow { color: var(--text-muted); font-size: 1.2rem; }

        input, button, textarea {
            font-family: inherit;
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            border: 1px solid #444;
            background: #222;
            color: var(--text-primary);
        }

        input:focus, textarea:focus {
            outline: none;
            border-color: var(--python-blue);
        }

        button {
            background: var(--rust-orange);
            border: none;
            cursor: pointer;
            transition: opacity 0.2s;
        }

        button:hover { opacity: 0.9; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }

        .demo-row {
            display: flex;
            gap: 0.5rem;
            align-items: center;
            margin: 0.5rem 0;
            flex-wrap: wrap;
        }

        .result {
            padding: 0.75rem;
            background: #111;
            border-radius: 4px;
            margin-top: 0.5rem;
            font-size: 0.85rem;
            white-space: pre-wrap;
        }

        .result.success { border-left: 3px solid var(--success); }
        .result.error { border-left: 3px solid var(--error); }

        .timing {
            display: flex;
            gap: 1rem;
            margin-top: 0.5rem;
            font-size: 0.8rem;
        }

        .timing-rust { color: var(--rust-orange); }
        .timing-python { color: var(--python-blue); }
        .timing-speedup { color: var(--success); }

        .code-block {
            background: #0d1117;
            border-radius: 6px;
            padding: 1rem;
            overflow-x: auto;
            font-size: 0.8rem;
            line-height: 1.5;
            margin: 1rem 0;
            max-height: 400px;
            overflow-y: auto;
        }

        .code-block code {
            color: #c9d1d9;
        }

        .keyword { color: #ff7b72; }
        .function { color: #d2a8ff; }
        .string { color: #a5d6ff; }
        .comment { color: #8b949e; }
        .type { color: #79c0ff; }

        .viz-container {
            display: flex;
            gap: 1rem;
            align-items: flex-start;
            flex-wrap: wrap;
        }

        .viz-controls { flex: 1; min-width: 200px; }
        .viz-display { flex: 1; min-width: 250px; }

        canvas {
            background: #111;
            border-radius: 4px;
            width: 100%;
            height: 150px;
        }

        .ring-viz {
            display: flex;
            gap: 4px;
            flex-wrap: wrap;
            padding: 1rem;
            background: #111;
            border-radius: 4px;
        }

        .ring-slot {
            width: 40px;
            height: 40px;
            border: 2px solid #444;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            transition: all 0.2s;
        }

        .ring-slot.filled {
            border-color: var(--rust-orange);
            background: rgba(247, 76, 0, 0.2);
        }

        .ring-slot.latest {
            border-color: var(--success);
            box-shadow: 0 0 8px var(--success);
        }

        .resources {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .resources a {
            color: var(--python-blue);
            text-decoration: none;
            padding: 0.5rem 1rem;
            background: #222;
            border-radius: 4px;
            transition: background 0.2s;
        }

        .resources a:hover { background: #333; }

        footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.8rem;
            border-top: 1px solid #333;
            margin-top: 3rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Hero -->
        <section class="hero">
            <h1>Rust + Python</h1>
            <p style="color: var(--text-muted);">A Self-Serving Demonstration</p>
            <p style="margin-top: 1rem; font-size: 0.9rem;">
                This page is served by Python calling Rust functions you can try below.
            </p>
            <div class="meta-stats">
                <div class="stat">
                    <div class="stat-value" id="uptime">0s</div>
                    <div class="stat-label">uptime</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="requests">0</div>
                    <div class="stat-label">requests</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="api-calls">0</div>
                    <div class="stat-label">API calls</div>
                </div>
            </div>
        </section>

        <!-- The Stack -->
        <section>
            <h2>The Stack</h2>
            <div class="card">
                <div class="stack-diagram">
                    <div class="stack-item stack-browser">Browser (You)</div>
                    <div class="stack-arrow">↓ HTTP</div>
                    <div class="stack-item stack-python">Python http.server</div>
                    <div class="stack-arrow">↓ PyO3</div>
                    <div class="stack-item stack-rust">rust_demo (Rust)</div>
                    <div class="stack-arrow">↓ Response</div>
                    <div class="stack-item stack-browser">Results + Timing</div>
                </div>
            </div>
        </section>

        <!-- Pure Functions -->
        <section>
            <h2>Try It: Pure Functions</h2>

            <div class="card">
                <h3>Fibonacci</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Compare Rust vs Python performance
                </p>
                <div class="demo-row">
                    <label>n =</label>
                    <input type="number" id="fib-n" value="40" min="0" max="90" style="width: 80px;">
                    <button onclick="runFibonacci()">Calculate</button>
                </div>
                <div id="fib-result" class="result" style="display: none;"></div>
            </div>

            <div class="card">
                <h3>Palindrome Checker</h3>
                <div class="demo-row">
                    <input type="text" id="palindrome-text" value="A man a plan a canal Panama" style="flex: 1;">
                    <button onclick="runPalindrome()">Check</button>
                </div>
                <div id="palindrome-result" class="result" style="display: none;"></div>
            </div>

            <div class="card">
                <h3>Unique Word Counter</h3>
                <div class="demo-row">
                    <input type="text" id="unique-text" value="The quick brown fox jumps over the lazy dog the fox" style="flex: 1;">
                    <button onclick="runUniqueWords()">Count</button>
                </div>
                <div id="unique-result" class="result" style="display: none;"></div>
            </div>
        </section>

        <!-- Error Handling -->
        <section>
            <h2>Try It: Error Handling</h2>

            <div class="card">
                <h3>Safe Parse Int</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Try valid integers, or trigger errors with "hello"
                </p>
                <div class="demo-row">
                    <input type="text" id="parse-text" value="42" style="width: 150px;">
                    <button onclick="runParseInt()">Parse</button>
                </div>
                <div id="parse-result" class="result" style="display: none;"></div>
            </div>

            <div class="card">
                <h3>Safe Divide</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Try dividing by zero to see error handling
                </p>
                <div class="demo-row">
                    <input type="number" id="divide-a" value="10" style="width: 80px;">
                    <span>/</span>
                    <input type="number" id="divide-b" value="3" style="width: 80px;">
                    <button onclick="runDivide()">Divide</button>
                </div>
                <div id="divide-result" class="result" style="display: none;"></div>
            </div>
        </section>

        <!-- Collections -->
        <section>
            <h2>Try It: Collections</h2>

            <div class="card">
                <h3>Sum List</h3>
                <div class="demo-row">
                    <input type="text" id="sum-numbers" value="1, 2, 3, 4, 5, -10, 20" style="flex: 1;">
                    <button onclick="runSumList()">Sum</button>
                </div>
                <div id="sum-result" class="result" style="display: none;"></div>
            </div>

            <div class="card">
                <h3>Filter Positive</h3>
                <div class="demo-row">
                    <input type="text" id="filter-numbers" value="1, -2, 3, -4, 5, -6, 7" style="flex: 1;">
                    <button onclick="runFilterPositive()">Filter</button>
                </div>
                <div id="filter-result" class="result" style="display: none;"></div>
            </div>

            <div class="card">
                <h3>Word Frequencies</h3>
                <div class="demo-row">
                    <input type="text" id="freq-words" value="apple, Banana, APPLE, cherry, banana, Apple" style="flex: 1;">
                    <button onclick="runWordFreq()">Count</button>
                </div>
                <div id="freq-result" class="result" style="display: none;"></div>
            </div>
        </section>

        <!-- Stateful Objects -->
        <section>
            <h2>Try It: Stateful Objects</h2>

            <div class="card">
                <h3>Moving Average (window=5)</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Rust object maintaining state across calls
                </p>
                <div class="viz-container">
                    <div class="viz-controls">
                        <div class="demo-row">
                            <input type="number" id="ma-value" value="10" style="width: 80px;">
                            <button onclick="addToMovingAvg()">Add</button>
                            <button onclick="clearMovingAvg()" style="background: #444;">Clear</button>
                        </div>
                        <div id="ma-result" class="result" style="margin-top: 0.5rem;">
                            Average: 0.00 | Count: 0
                        </div>
                    </div>
                    <div class="viz-display">
                        <canvas id="ma-chart"></canvas>
                    </div>
                </div>
            </div>

            <div class="card">
                <h3>Ring Buffer (capacity=8)</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Circular buffer that overwrites oldest values
                </p>
                <div class="viz-container">
                    <div class="viz-controls">
                        <div class="demo-row">
                            <input type="number" id="rb-value" value="1" style="width: 80px;">
                            <button onclick="pushToRingBuffer()">Push</button>
                        </div>
                        <div id="rb-result" class="result" style="margin-top: 0.5rem;">
                            Length: 0 | Full: No
                        </div>
                    </div>
                    <div class="viz-display">
                        <div id="rb-viz" class="ring-viz">
                            <div class="ring-slot"></div>
                            <div class="ring-slot"></div>
                            <div class="ring-slot"></div>
                            <div class="ring-slot"></div>
                            <div class="ring-slot"></div>
                            <div class="ring-slot"></div>
                            <div class="ring-slot"></div>
                            <div class="ring-slot"></div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Parallel Computation -->
        <section>
            <h2>Try It: Parallel Computation</h2>

            <div class="card">
                <h3>Parallel Sum (rayon)</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Rust releases the GIL and uses all CPU cores via rayon
                </p>
                <div class="demo-row">
                    <label>Size:</label>
                    <select id="par-size">
                        <option value="1000000">1M</option>
                        <option value="5000000">5M</option>
                        <option value="10000000" selected>10M</option>
                        <option value="25000000">25M</option>
                    </select>
                    <button onclick="runParallelSum()">Sum</button>
                </div>
                <div id="par-result" class="result" style="display: none;"></div>
            </div>

            <div class="card">
                <h3>Prime Sieve</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Sieve of Eratosthenes — compare count_primes (returns int) vs prime_sieve (returns list)
                </p>
                <div class="demo-row">
                    <label>Up to:</label>
                    <select id="prime-n">
                        <option value="100000">100K</option>
                        <option value="500000">500K</option>
                        <option value="1000000" selected>1M</option>
                        <option value="5000000">5M</option>
                    </select>
                    <select id="prime-mode">
                        <option value="count">Count only (fast)</option>
                        <option value="list">Return list (slower)</option>
                    </select>
                    <button onclick="runPrimeSieve()">Find Primes</button>
                </div>
                <div id="prime-result" class="result" style="display: none;"></div>
            </div>
        </section>

        <!-- Matrix Multiply -->
        <section>
            <h2>Try It: Matrix Multiplication</h2>
            <div class="card">
                <h3>NxN Matrix Multiply</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    O(n³) tight loop with cache-friendly i-k-j ordering. Python comparison skipped for sizes > 150.
                </p>
                <div class="demo-row">
                    <label>Size:</label>
                    <select id="mat-size">
                        <option value="50">50x50</option>
                        <option value="100" selected>100x100</option>
                        <option value="150">150x150</option>
                        <option value="200">200x200</option>
                        <option value="300">300x300</option>
                    </select>
                    <button onclick="runMatMul()">Multiply</button>
                </div>
                <div id="mat-result" class="result" style="display: none;"></div>
            </div>
        </section>

        <!-- Text Processing -->
        <section>
            <h2>Try It: Text Processing</h2>

            <div class="card">
                <h3>Slugify</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Convert arbitrary text to a URL-friendly slug
                </p>
                <div class="demo-row">
                    <input type="text" id="slug-text" value="Hello, World! This is a Test." style="flex: 1;">
                    <button onclick="runSlugify()">Slugify</button>
                </div>
                <div id="slug-result" class="result" style="display: none;"></div>
            </div>

            <div class="card">
                <h3>Extract Emails</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Find email-like patterns via manual character scanning in Rust
                </p>
                <div class="demo-row">
                    <input type="text" id="email-text" value="Contact hello@example.com or support@rust-lang.org. Not: @nobody or broken@" style="flex: 1;">
                    <button onclick="runExtractEmails()">Extract</button>
                </div>
                <div id="email-result" class="result" style="display: none;"></div>
            </div>
        </section>

        <!-- SortedSet -->
        <section>
            <h2>Try It: Sorted Set</h2>
            <div class="card">
                <h3>SortedSet (binary search backed)</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Python has no built-in sorted set. This Rust class maintains sorted order with O(log n) lookups.
                </p>
                <div class="demo-row">
                    <input type="number" id="ss-value" value="42" style="width: 80px;">
                    <button onclick="ssAction('insert')">Insert</button>
                    <button onclick="ssAction('remove')" style="background: #444;">Remove</button>
                    <button onclick="ssAction('contains')" style="background: var(--python-blue);">Contains?</button>
                </div>
                <div class="demo-row">
                    <label>Range:</label>
                    <input type="number" id="ss-low" value="10" style="width: 60px;">
                    <span>to</span>
                    <input type="number" id="ss-high" value="50" style="width: 60px;">
                    <button onclick="ssRange()" style="background: var(--python-blue);">Query</button>
                </div>
                <div id="ss-result" class="result" style="margin-top: 0.5rem;">
                    Items: [] | Length: 0
                </div>
            </div>
        </section>

        <!-- SHA-256 -->
        <section>
            <h2>Try It: SHA-256</h2>
            <div class="card">
                <h3>SHA-256 Hash</h3>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Rust sha2 crate vs Python hashlib — both use compiled native code
                </p>
                <div class="demo-row">
                    <input type="text" id="sha-text" value="Hello, Rust + Python!" style="flex: 1;">
                    <button onclick="runSha256()">Hash</button>
                </div>
                <div id="sha-result" class="result" style="display: none;"></div>
            </div>
        </section>

        <!-- The Code -->
        <section>
            <h2>The Code</h2>
            <div class="card">
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-bottom: 0.5rem;">
                    Actual Rust source from lib.rs
                </p>
                <div class="code-block">
                    <code id="rust-code">Loading...</code>
                </div>
            </div>
        </section>

        <!-- Resources -->
        <section>
            <h2>Resources</h2>
            <div class="resources">
                <a href="https://pyo3.rs" target="_blank">PyO3 Documentation</a>
                <a href="https://www.maturin.rs" target="_blank">Maturin Build Tool</a>
                <a href="https://docs.astral.sh/uv/" target="_blank">uv Package Manager</a>
                <a href="https://doc.rust-lang.org" target="_blank">Rust Docs</a>
            </div>
        </section>

        <footer>
            Powered by rust_demo | PyO3 + Maturin + uv
        </footer>
    </div>

    <script>
        let sessionId = null;
        const maHistory = [];
        const MA_CHART_MAX = 20;

        // Initialize session and start stats polling
        async function init() {
            // Create session for stateful demos
            const resp = await fetch('/api/session', { method: 'POST' });
            const data = await resp.json();
            sessionId = data.session_id;

            // Load lib.rs
            loadRustCode();

            // Start stats polling
            updateStats();
            setInterval(updateStats, 1000);
        }

        async function updateStats() {
            try {
                const resp = await fetch('/api/stats');
                const data = await resp.json();
                document.getElementById('uptime').textContent = data.uptime_human;
                document.getElementById('requests').textContent = data.total_requests;
                document.getElementById('api-calls').textContent = data.api_calls;
            } catch (e) {}
        }

        async function loadRustCode() {
            try {
                const resp = await fetch('/api/lib.rs');
                const data = await resp.json();
                const highlighted = highlightRust(data.content);
                document.getElementById('rust-code').innerHTML = highlighted;
            } catch (e) {
                document.getElementById('rust-code').textContent = 'Failed to load';
            }
        }

        function highlightRust(code) {
            return code
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/(\/\/.*)/g, '<span class="comment">$1</span>')
                .replace(/\\b(fn|let|mut|if|else|match|for|in|use|pub|struct|impl|return|self|Ok|Err|Some|None)\\b/g, '<span class="keyword">$1</span>')
                .replace(/\\b(u64|usize|f64|i64|bool|String|Vec|HashMap|Option|PyResult)\\b/g, '<span class="type">$1</span>')
                .replace(/"([^"]*)"/g, '<span class="string">"$1"</span>')
                .replace(/#\\[([^\\]]*)\\]/g, '<span class="function">#[$1]</span>');
        }

        function showResult(id, content, isError = false) {
            const el = document.getElementById(id);
            el.style.display = 'block';
            el.textContent = content;
            el.className = 'result ' + (isError ? 'error' : 'success');
        }

        // API Calls
        async function runFibonacci() {
            const n = document.getElementById('fib-n').value;
            const resp = await fetch('/api/fibonacci', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ n: parseInt(n) })
            });
            const data = await resp.json();
            const result = `fibonacci(${data.n}) = ${data.result}

Rust:   ${data.rust_ms.toFixed(4)}ms
Python: ${data.python_ms.toFixed(4)}ms
Speedup: ${data.speedup}x`;
            showResult('fib-result', result);
        }

        async function runPalindrome() {
            const text = document.getElementById('palindrome-text').value;
            const resp = await fetch('/api/palindrome', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await resp.json();
            showResult('palindrome-result', `"${data.text}" is ${data.is_palindrome ? '' : 'NOT '}a palindrome`);
        }

        async function runUniqueWords() {
            const text = document.getElementById('unique-text').value;
            const resp = await fetch('/api/unique_words', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await resp.json();
            showResult('unique-result', `Unique words: ${data.count}`);
        }

        async function runParseInt() {
            const text = document.getElementById('parse-text').value;
            const resp = await fetch('/api/parse_int', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await resp.json();
            if (data.error) {
                showResult('parse-result', `Error: ${data.error}`, true);
            } else {
                showResult('parse-result', `Parsed: ${data.result}`);
            }
        }

        async function runDivide() {
            const a = document.getElementById('divide-a').value;
            const b = document.getElementById('divide-b').value;
            const resp = await fetch('/api/divide', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ a: parseFloat(a), b: parseFloat(b) })
            });
            const data = await resp.json();
            if (data.error) {
                showResult('divide-result', `Error: ${data.error}`, true);
            } else {
                showResult('divide-result', `${data.a} / ${data.b} = ${data.result.toFixed(6)}`);
            }
        }

        async function runSumList() {
            const text = document.getElementById('sum-numbers').value;
            const numbers = text.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
            const resp = await fetch('/api/sum_list', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ numbers })
            });
            const data = await resp.json();
            showResult('sum-result', `Sum of ${data.count} numbers = ${data.result}

Rust:   ${data.rust_ms.toFixed(4)}ms
Python: ${data.python_ms.toFixed(4)}ms`);
        }

        async function runFilterPositive() {
            const text = document.getElementById('filter-numbers').value;
            const numbers = text.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
            const resp = await fetch('/api/filter_positive', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ numbers })
            });
            const data = await resp.json();
            showResult('filter-result', `Input: [${data.input.join(', ')}]
Positive: [${data.result.join(', ')}]`);
        }

        async function runWordFreq() {
            const text = document.getElementById('freq-words').value;
            const words = text.split(',').map(s => s.trim()).filter(s => s);
            const resp = await fetch('/api/word_freq', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ words })
            });
            const data = await resp.json();
            const freqStr = Object.entries(data.frequencies)
                .map(([word, count]) => `  "${word}": ${count}`)
                .join('\\n');
            showResult('freq-result', `Frequencies:\\n${freqStr}`);
        }

        // Stateful demos
        async function addToMovingAvg() {
            const value = parseFloat(document.getElementById('ma-value').value);
            const resp = await fetch('/api/moving_avg', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, action: 'add', value })
            });
            const data = await resp.json();
            document.getElementById('ma-result').textContent =
                `Average: ${data.average.toFixed(2)} | Count: ${data.count}`;

            maHistory.push(data.average);
            if (maHistory.length > MA_CHART_MAX) maHistory.shift();
            drawMAChart();
        }

        async function clearMovingAvg() {
            await fetch('/api/moving_avg', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, action: 'clear' })
            });
            document.getElementById('ma-result').textContent = 'Average: 0.00 | Count: 0';
            maHistory.length = 0;
            drawMAChart();
        }

        function drawMAChart() {
            const canvas = document.getElementById('ma-chart');
            const ctx = canvas.getContext('2d');
            const w = canvas.width = canvas.offsetWidth * 2;
            const h = canvas.height = canvas.offsetHeight * 2;
            ctx.scale(2, 2);

            ctx.fillStyle = '#111';
            ctx.fillRect(0, 0, w/2, h/2);

            if (maHistory.length < 2) return;

            const max = Math.max(...maHistory) * 1.1 || 1;
            const min = Math.min(...maHistory) * 0.9 || 0;
            const range = max - min || 1;

            ctx.strokeStyle = '#f74c00';
            ctx.lineWidth = 2;
            ctx.beginPath();

            maHistory.forEach((v, i) => {
                const x = (i / (MA_CHART_MAX - 1)) * (w/2 - 20) + 10;
                const y = h/2 - 10 - ((v - min) / range) * (h/2 - 20);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();
        }

        async function pushToRingBuffer() {
            const value = parseFloat(document.getElementById('rb-value').value);
            const resp = await fetch('/api/ring_buffer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, action: 'push', value })
            });
            const data = await resp.json();
            document.getElementById('rb-result').textContent =
                `Length: ${data.length} | Full: ${data.is_full ? 'Yes' : 'No'}`;

            // Update visualization
            const slots = document.querySelectorAll('#rb-viz .ring-slot');
            slots.forEach((slot, i) => {
                slot.className = 'ring-slot';
                if (i < data.values.length) {
                    slot.textContent = data.values[i];
                    slot.classList.add('filled');
                    if (data.values[i] === data.latest) {
                        slot.classList.add('latest');
                    }
                } else {
                    slot.textContent = '';
                }
            });

            // Increment input for next push
            document.getElementById('rb-value').value = value + 1;
        }

        // New API calls
        async function runParallelSum() {
            const size = parseInt(document.getElementById('par-size').value);
            showResult('par-result', 'Computing...');
            const resp = await fetch('/api/parallel_sum', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ size })
            });
            const data = await resp.json();
            showResult('par-result', `Parallel sum of ${data.size.toLocaleString()} integers = ${data.result.toLocaleString()}

Rust (rayon): ${data.rust_ms.toFixed(4)}ms
Python sum(): ${data.python_ms.toFixed(4)}ms
Speedup: ${data.speedup}x`);
        }

        async function runPrimeSieve() {
            const n = parseInt(document.getElementById('prime-n').value);
            const mode = document.getElementById('prime-mode').value;
            showResult('prime-result', 'Computing...');
            const resp = await fetch('/api/prime_sieve', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ n, mode })
            });
            const data = await resp.json();
            showResult('prime-result', `Primes up to ${data.n.toLocaleString()}: ${data.count.toLocaleString()} found (mode: ${data.mode})

Rust:   ${data.rust_ms.toFixed(4)}ms
Python: ${data.python_ms.toFixed(4)}ms
Speedup: ${data.speedup}x`);
        }

        async function runMatMul() {
            const size = parseInt(document.getElementById('mat-size').value);
            showResult('mat-result', `Computing ${size}x${size} matrix multiply...`);
            const resp = await fetch('/api/matrix_multiply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ size })
            });
            const data = await resp.json();
            let result = `${data.size}x${data.size} matrix multiply:

Rust: ${data.rust_ms.toFixed(4)}ms`;
            if (data.python_ms !== null) {
                result += `
Python: ${data.python_ms.toFixed(4)}ms
Speedup: ${data.speedup}x`;
            } else {
                result += `
Python: skipped (too slow for size > 150)`;
            }
            showResult('mat-result', result);
        }

        async function runSlugify() {
            const text = document.getElementById('slug-text').value;
            const resp = await fetch('/api/slugify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await resp.json();
            showResult('slug-result', `Input: "${data.text}"
Slug:  "${data.slug}"`);
        }

        async function runExtractEmails() {
            const text = document.getElementById('email-text').value;
            const resp = await fetch('/api/extract_emails', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await resp.json();
            const emailList = data.emails.length > 0
                ? data.emails.map(e => `  → ${e}`).join('\\n')
                : '  (none found)';
            showResult('email-result', `Found ${data.count} email(s):
${emailList}`);
        }

        async function ssAction(action) {
            const value = parseInt(document.getElementById('ss-value').value);
            const resp = await fetch('/api/sorted_set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, action, value })
            });
            const data = await resp.json();
            if (data.error) {
                document.getElementById('ss-result').textContent = `Error: ${data.error}`;
                return;
            }
            if (action === 'contains') {
                document.getElementById('ss-result').textContent =
                    `contains(${data.value}): ${data.found}`;
            } else {
                const verb = action === 'insert' ? (data.inserted ? 'Inserted' : 'Already present') : (data.removed ? 'Removed' : 'Not found');
                document.getElementById('ss-result').textContent =
                    `${verb}: ${data.value} | Items: [${data.items.join(', ')}] | Length: ${data.length}`;
            }
        }

        async function ssRange() {
            const low = parseInt(document.getElementById('ss-low').value);
            const high = parseInt(document.getElementById('ss-high').value);
            const resp = await fetch('/api/sorted_set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId, action: 'range', low, high })
            });
            const data = await resp.json();
            document.getElementById('ss-result').textContent =
                `range(${data.low}, ${data.high}): [${data.items.join(', ')}]`;
        }

        async function runSha256() {
            const text = document.getElementById('sha-text').value;
            const resp = await fetch('/api/sha256', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await resp.json();
            showResult('sha-result', `Input: ${data.text_length} chars
SHA-256: ${data.hash}
Match (Rust == Python hashlib): ${data.match}

Rust: ${data.rust_ms.toFixed(4)}ms
Python: ${data.python_ms.toFixed(4)}ms`);
        }

        // Initialize
        init();
    </script>
</body>
</html>
"""


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Self-referential Rust-Python demo server"
    )
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    args = parser.parse_args()

    # Load lib.rs for code display
    DemoHandler.load_lib_rs()

    server = HTTPServer((args.host, args.port), DemoHandler)
    print(f"Serving at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
