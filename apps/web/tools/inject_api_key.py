#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Inject Google API key into apps/web/public/script.js by replacing the
placeholder string '{{GOOGLE_API_KEY}}'.

Usage:
  export GOOGLE_API_KEY=your_key
  python3 apps/web/tools/inject_api_key.py

Or:
  python3 apps/web/tools/inject_api_key.py --key your_key
"""

import os
import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--key', default=os.environ.get('GOOGLE_API_KEY', ''))
    parser.add_argument('--file', default=os.path.join(os.path.dirname(__file__), '..', 'public', 'script.js'))
    args = parser.parse_args()

    if not args.key or '{{' in args.key:
        raise SystemExit('GOOGLE_API_KEY not provided or invalid. Set env GOOGLE_API_KEY or pass --key.')

    path = os.path.abspath(args.file)
    if not os.path.exists(path):
        raise SystemExit(f'script.js not found: {path}')

    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()

    replaced = src.replace("{{GOOGLE_API_KEY}}", args.key)
    if replaced == src:
        print('No placeholder replaced (already set or missing).')
    else:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(replaced)
        print(f'✅ Injected API key into: {path}')


if __name__ == '__main__':
    main()

