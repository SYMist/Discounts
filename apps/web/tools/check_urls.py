#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple URL checker for status/redirect chains.

Usage examples:
  # From a file
  python3 apps/web/tools/check_urls.py urls.txt

  # Pipe from recent-urls
  python3 apps/web/tools/list_recent_urls.py --days 3 --limit 50 --encode \
    | python3 apps/web/tools/check_urls.py -F

Options:
  -F/--follow     Follow redirects (report final status)
  -t/--timeout    Timeout seconds per request (default 10)
  -H/--head       Use HEAD (default); add --no-head to force GET
"""

import sys
import argparse
import requests

def read_urls(path: str | None):
    if path:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                u = line.strip()
                if u:
                    yield u
    else:
        for line in sys.stdin:
            u = line.strip()
            if u:
                yield u

def check(url: str, follow: bool, timeout: float, method: str):
    try:
        s = requests.Session()
        s.max_redirects = 10
        allow = follow
        if method == 'HEAD':
            resp = s.head(url, allow_redirects=allow, timeout=timeout)
        else:
            resp = s.get(url, allow_redirects=allow, timeout=timeout)
        chain = [h.url for h in resp.history] + [resp.url]
        return resp.status_code, chain
    except Exception as e:
        return None, [f"ERROR: {e}"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('file', nargs='?', default=None, help='Input file (one URL per line); default stdin')
    ap.add_argument('-F', '--follow', action='store_true', help='Follow redirects')
    ap.add_argument('-t', '--timeout', type=float, default=10.0)
    ap.add_argument('--no-head', action='store_true', help='Use GET instead of HEAD')
    args = ap.parse_args()

    method = 'GET' if args.no_head else 'HEAD'
    any_bad = False
    for url in read_urls(args.file):
        code, chain = check(url, args.follow, args.timeout, method)
        if code is None:
            print(f"[ERR] {url} -> {' -> '.join(chain)}")
            any_bad = True
            continue
        if len(chain) > 1:
            print(f"[RD{len(chain)-1}] {url} -> {chain[-1]} ({code})")
        else:
            print(f"[OK ] {url} ({code})")
        if not (200 <= code < 400):
            any_bad = True
    sys.exit(1 if any_bad else 0)

if __name__ == '__main__':
    main()

