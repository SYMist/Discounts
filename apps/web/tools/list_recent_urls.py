#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
List recent pretty URLs based on file mtime under apps/web/public/pages and /events.
Usage:
  python3 apps/web/tools/list_recent_urls.py --days 7 --limit 100
"""

import os
import argparse
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # apps/web
PUBLIC = os.path.join(BASE, 'public')
PAGES = os.path.join(PUBLIC, 'pages')
EVENTS = os.path.join(PUBLIC, 'events')
DEFAULT_SITE_BASE = os.environ.get('SITE_BASE_URL', 'https://discounts.deluxo.co.kr')

def iter_pages(days: int):
    cutoff = datetime.now() - timedelta(days=days)
    if os.path.isdir(PAGES):
        for fn in os.listdir(PAGES):
            if not fn.endswith('.html'):
                continue
            name = fn[:-5]
            if name.startswith('songdo-'):
                url = '/songdo/' + name.replace('songdo-', '')
            elif name.startswith('gimpo-'):
                url = '/gimpo/' + name.replace('gimpo-', '')
            elif name.startswith('spaceone-'):
                url = '/spaceone/' + name.replace('spaceone-', '')
            else:
                continue
            fp = os.path.join(PAGES, fn)
            mtime = datetime.fromtimestamp(os.path.getmtime(fp))
            if mtime >= cutoff:
                yield (mtime, url)

    if os.path.isdir(EVENTS):
        for fn in os.listdir(EVENTS):
            if not fn.endswith('.html'):
                continue
            url = '/events/' + ('' if fn == 'index.html' else fn)
            fp = os.path.join(EVENTS, fn)
            mtime = datetime.fromtimestamp(os.path.getmtime(fp))
            if mtime >= cutoff:
                yield (mtime, url)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--days', type=int, default=7)
    ap.add_argument('--limit', type=int, default=100)
    ap.add_argument('--base', type=str, default=None, help='Base URL for absolute output (default: env SITE_BASE_URL or https://discounts.deluxo.co.kr)')
    args = ap.parse_args()

    items = sorted(iter_pages(args.days), key=lambda x: -x[0].timestamp())
    base = (args.base or DEFAULT_SITE_BASE).rstrip('/')
    for _, url in items[:args.limit]:
        print(f"{base}{url}")

if __name__ == '__main__':
    main()
