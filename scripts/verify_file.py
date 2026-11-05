#!/usr/bin/env python3
import argparse
import hashlib
import os


def digest_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest(), os.path.getsize(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--size", required=True, type=int)
    args = parser.parse_args()
    actual_sha, actual_size = digest_file(args.path)
    if actual_sha != args.sha256:
        raise SystemExit(f"SHA-256 mismatch: expected {args.sha256}, got {actual_sha}")
    if actual_size != args.size:
        raise SystemExit(f"size mismatch: expected {args.size}, got {actual_size}")
    print(f"verified sha256={actual_sha} size={actual_size}")


if __name__ == "__main__":
    main()
