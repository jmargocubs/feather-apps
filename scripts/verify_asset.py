#!/usr/bin/env python3
import argparse
import hashlib
import sys
import time
import urllib.request


def fetch_and_verify(url, expected_sha, expected_size, attempts, interval, timeout):
    last_error = None
    for attempt in range(1, attempts + 1):
        digest = hashlib.sha256()
        size = 0
        try:
            request = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP status {response.status}")
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    size += len(chunk)
            actual_sha = digest.hexdigest()
            if actual_sha != expected_sha:
                raise ValueError(f"SHA-256 mismatch: {actual_sha}")
            if size != expected_size:
                raise ValueError(f"size mismatch: {size}")
            print(f"public asset verified: sha256={actual_sha} size={size}")
            return
        except Exception as error:
            last_error = error
            print(f"attempt {attempt}/{attempts} failed: {error}", file=sys.stderr)
            if attempt < attempts:
                time.sleep(interval)
    raise RuntimeError(f"public asset verification failed after {attempts} attempts: {last_error}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--size", required=True, type=int)
    parser.add_argument("--attempts", type=int, default=12)
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()
    fetch_and_verify(
        args.url, args.sha256, args.size, args.attempts, args.interval, args.timeout
    )


if __name__ == "__main__":
    main()
