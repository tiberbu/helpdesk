#!/usr/bin/env python3
"""Chat message latency benchmark (Story 3.4, AC #1, #7).

Measures the round-trip latency for chat messages via the Frappe REST API:
  send_message → API response time (proxy for message delivery latency)

Usage:
  python scripts/benchmark_chat_latency.py [--url http://helpdesk.localhost:8004] [--n 100]

Requirements:
  pip install requests

The benchmark:
  1. Creates a chat session via create_session API
  2. Sends N messages via send_message and records response times
  3. Prints p50 / p95 / p99 statistics
  4. Exits 0 if p95 < 200ms, else exits 1 (CI assertion)

Note: This measures HTTP round-trip time (server processing + network).
      The Socket.IO broadcast adds minimal overhead (~1-5ms local).
      To measure true end-to-end latency including Socket.IO delivery,
      run against a dev server with a Socket.IO listener on the other side.

NFR-P-03: Live chat message delivery < 200ms end-to-end (95th percentile).
"""

import argparse
import statistics
import sys
import time

try:
    import requests
except ImportError:
    print("ERROR: 'requests' package is required. Install with: pip install requests")
    sys.exit(2)

DEFAULT_URL = "http://helpdesk.localhost:8004"
DEFAULT_N = 100
P95_THRESHOLD_MS = 200


def api(base_url: str, method: str, params: dict | None = None, json: dict | None = None):
    """Call a Frappe whitelisted API endpoint."""
    url = f"{base_url}/api/method/{method}"
    if json:
        resp = requests.post(url, json=json, timeout=10)
    else:
        resp = requests.get(url, params=params or {}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("message", data)


def create_session(base_url: str) -> tuple[str, str]:
    """Create a chat session and return (session_id, token)."""
    result = api(
        base_url,
        "helpdesk.helpdesk.api.chat.create_session",
        json={
            "email": "benchmark@example.com",
            "name": "Benchmark User",
            "subject": "Latency Test",
        },
    )
    return result["session_id"], result["token"]


def send_message(base_url: str, session_id: str, token: str, content: str) -> dict:
    """Send a message and return the API response."""
    return api(
        base_url,
        "helpdesk.helpdesk.api.chat.send_message",
        json={"session_id": session_id, "content": content, "token": token},
    )


def benchmark(base_url: str, n: int) -> list[float]:
    """Run N send_message calls and return latency in milliseconds."""
    print(f"Creating chat session at {base_url}...")
    try:
        session_id, token = create_session(base_url)
    except Exception as exc:
        print(f"ERROR: Could not create session — {exc}")
        print("Ensure the Frappe dev server is running and chat_enabled=1 in HD Settings.")
        sys.exit(2)

    print(f"Session: {session_id} — sending {n} messages...")
    latencies = []

    for i in range(n):
        start = time.perf_counter()
        try:
            send_message(base_url, session_id, token, f"Benchmark message {i + 1}")
        except Exception as exc:
            print(f"WARNING: message {i + 1} failed — {exc}")
            continue
        elapsed_ms = (time.perf_counter() - start) * 1000
        latencies.append(elapsed_ms)

        if (i + 1) % 20 == 0:
            print(f"  {i + 1}/{n} complete, last: {elapsed_ms:.1f}ms")

    return latencies


def print_stats(latencies: list[float]) -> float:
    """Print latency statistics and return p95."""
    if not latencies:
        print("No latency data collected.")
        return float("inf")

    latencies_sorted = sorted(latencies)
    p50 = statistics.median(latencies)
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]
    p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)]
    mean = statistics.mean(latencies)

    print("\n── Latency Results ─────────────────────────────────")
    print(f"  Samples : {len(latencies)}")
    print(f"  Mean    : {mean:.1f} ms")
    print(f"  p50     : {p50:.1f} ms")
    print(f"  p95     : {p95:.1f} ms  (threshold: {P95_THRESHOLD_MS}ms)")
    print(f"  p99     : {p99:.1f} ms")
    print(f"  Min     : {min(latencies):.1f} ms")
    print(f"  Max     : {max(latencies):.1f} ms")
    print("────────────────────────────────────────────────────")
    return p95


def main():
    parser = argparse.ArgumentParser(description="Chat message latency benchmark")
    parser.add_argument("--url", default=DEFAULT_URL, help="Frappe site base URL")
    parser.add_argument("--n", type=int, default=DEFAULT_N, help="Number of messages to send")
    args = parser.parse_args()

    latencies = benchmark(args.url, args.n)
    p95 = print_stats(latencies)

    if p95 <= P95_THRESHOLD_MS:
        print(f"\nPASS: p95 = {p95:.1f}ms ≤ {P95_THRESHOLD_MS}ms (NFR-P-03)")
        sys.exit(0)
    else:
        print(f"\nFAIL: p95 = {p95:.1f}ms > {P95_THRESHOLD_MS}ms (NFR-P-03 violated)")
        sys.exit(1)


if __name__ == "__main__":
    main()
