#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Copy legacy outlet-web public artifacts into apps/web/public for the new layout.

This is optional and safe to run multiple times.

Usage:
  python3 tools/sync_legacy_to_apps.py
"""

import os
import shutil

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LEGACY = os.path.join(REPO_ROOT, 'outlet-web')
TARGET_PUBLIC = os.path.join(REPO_ROOT, 'apps', 'web', 'public')

FILES = [
    'index.html', 'style.css', 'script.js', 'robots.txt', 'ads.txt', 'sitemap.xml', 'privacy.html', '.htaccess', 'url-mapping.json'
]

DIRS = [
    ('images', 'images'),
    ('pages', 'pages'),
]


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def copy_file(src: str, dst: str):
    ensure_dir(os.path.dirname(dst))
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"✅ copied: {src} -> {dst}")
    else:
        print(f"⚠️ missing (skip): {src}")


def copy_tree(src: str, dst: str):
    if not os.path.exists(src):
        print(f"⚠️ missing (skip): {src}")
        return
    ensure_dir(dst)
    for root, _, files in os.walk(src):
        rel = os.path.relpath(root, src)
        for f in files:
            s = os.path.join(root, f)
            d = os.path.join(dst, rel, f)
            ensure_dir(os.path.dirname(d))
            shutil.copy2(s, d)
    print(f"✅ copied tree: {src} -> {dst}")


def main():
    ensure_dir(TARGET_PUBLIC)
    # files
    for f in FILES:
        copy_file(os.path.join(LEGACY, f), os.path.join(TARGET_PUBLIC, f))
    # dirs
    for src_d, dst_d in DIRS:
        copy_tree(os.path.join(LEGACY, src_d), os.path.join(TARGET_PUBLIC, dst_d))


if __name__ == '__main__':
    main()

