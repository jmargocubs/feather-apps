#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def cache_busted(url, expected, attempt):
    marker = hashlib.sha256(
        json.dumps(expected, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]
    separator = "&" if urllib.parse.urlsplit(url).query else "?"
    return f"{url}{separator}verify={marker}-{attempt}"


def verify(expected, url, attempts, interval, timeout, sleep=time.sleep):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            request = urllib.request.Request(
                cache_busted(url, expected, attempt),
                headers={"Cache-Control": "no-cache", "Pragma": "no-cache"},
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                live = json.load(response)
            if live != expected:
                raise ValueError("HTTP succeeded, but live JSON is still stale")
            print(f"live source matches committed source on attempt {attempt}")
            return
        except Exception as error:
            last_error = error
            print(f"attempt {attempt}/{attempts} failed: {error}", file=sys.stderr)
            if attempt < attempts:
                sleep(interval)
    raise RuntimeError(f"live source did not converge after {attempts} attempts: {last_error}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-source", default="source.json")
    parser.add_argument("--url", default="https://jmargocubs.github.io/feather-apps/source.json")
    parser.add_argument("--attempts", type=int, default=30)
    parser.add_argument("--interval", type=float, default=10)
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args()
    if args.attempts < 1 or args.interval < 0 or args.timeout <= 0:
        parser.error("attempts must be positive, interval non-negative, and timeout positive")
    verify(load_json(args.expected_source), args.url, args.attempts, args.interval, args.timeout)


if __name__ == "__main__":
    main()
