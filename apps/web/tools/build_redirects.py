#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate redirect artifacts from url-mapping.json (single source of truth).

Outputs (in apps/web/tools/):
- generated_redirects.htaccess  (RewriteRule lines for old -> pretty URLs)
- cloudflare_worker_complete.js (Workers mapping table for redirects)

Usage:
  python3 apps/web/tools/build_redirects.py
  python3 apps/web/tools/build_redirects.py --mapping ../public/url-mapping.json --pages ../public/pages --out-dir .
"""

import os
import json
import argparse
from typing import Dict, Tuple


def parse_args():
    parser = argparse.ArgumentParser()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument(
        "--mapping",
        default=os.path.join(base_dir, "..", "public", "url-mapping.json"),
        help="Path to url-mapping.json",
    )
    parser.add_argument(
        "--pages",
        default=os.path.join(base_dir, "..", "public", "pages"),
        help="Path to pages directory",
    )
    parser.add_argument(
        "--out-dir",
        default=base_dir,
        help="Output directory for generated files",
    )
    return parser.parse_args()


def filename_to_pretty_path(filename: str) -> Tuple[str, str]:
    """Convert 'branch-slug.html' -> (branch, 'branch/slug')."""
    if not filename.endswith(".html"):
        return "", ""
    name = filename[:-5]
    if name.startswith("songdo-"):
        return "songdo", name.replace("songdo-", "songdo/")
    if name.startswith("gimpo-"):
        return "gimpo", name.replace("gimpo-", "gimpo/")
    if name.startswith("spaceone-"):
        return "spaceone", name.replace("spaceone-", "spaceone/")
    return "", ""


def load_mapping(mapping_path: str) -> Dict[str, str]:
    with open(mapping_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_htaccess_redirects(mapping: Dict[str, str]) -> str:
    lines = [
        "# 2. 기존 pages/event-*.html 파일들을 새로운 구조로 리다이렉트 (301 리다이렉트)",
    ]
    for event_id, filename in sorted(mapping.items(), key=lambda x: x[0]):
        branch, pretty = filename_to_pretty_path(filename)
        if not branch:
            continue
        old = f"pages/event-{event_id}.html"
        new = f"/{pretty}"
        lines.append(f"RewriteRule ^{old}$ {new} [R=301,L]")
    lines.append("")
    return "\n".join(lines)


def build_worker(mapping: Dict[str, str]) -> str:
    body = [
        "// 클라우드플레어 Workers Script",
        "// URL 리다이렉트 처리 - 자동 생성됨",
        "",
        "addEventListener('fetch', event => {",
        "  event.respondWith(handleRequest(event.request))",
        "})",
        "",
        "async function handleRequest(request) {",
        "  const url = new URL(request.url)",
        "  const pathname = url.pathname",
        "  ",
        "  // 기존 이벤트 URL 패턴 확인",
        "  if (pathname.startsWith('/pages/event-') && pathname.endsWith('.html')) {",
        "    const newUrl = getNewUrl(pathname)",
        "    if (newUrl) {",
        "      // 301 영구 리다이렉트",
        "      return Response.redirect(newUrl, 301)",
        "    }",
        "  }",
        "  ",
        "  // 리다이렉트가 아닌 경우 원래 요청 처리",
        "  return fetch(request)",
        "}",
        "",
        "function getNewUrl(oldPath) {",
        "  // URL 매핑 테이블",
        "  const urlMappings = {",
    ]
    for event_id, filename in sorted(mapping.items(), key=lambda x: x[0]):
        branch, pretty = filename_to_pretty_path(filename)
        if not branch:
            continue
        old = f"/pages/event-{event_id}.html"
        new = f"/{pretty}"
        body.append(f"    '{old}': '{new}',")
    body += [
        "  }",
        "  return urlMappings[oldPath] || null",
        "}",
    ]
    return "\n".join(body)


def main():
    args = parse_args()
    mapping = load_mapping(args.mapping)

    # Generate htaccess redirect rules
    htaccess_rules = build_htaccess_redirects(mapping)
    ht_out = os.path.join(args.out_dir, "generated_redirects.htaccess")
    with open(ht_out, "w", encoding="utf-8") as f:
        f.write(htaccess_rules)

    # Generate Cloudflare worker
    worker_js = build_worker(mapping)
    wk_out = os.path.join(args.out_dir, "cloudflare_worker_complete.js")
    with open(wk_out, "w", encoding="utf-8") as f:
        f.write(worker_js)

    print(f"✅ wrote: {ht_out}")
    print(f"✅ wrote: {wk_out}")
    print(f"📊 entries: {len(mapping)}")


if __name__ == "__main__":
    main()

