#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a single smoke HTML page using crawler's template to verify
that outputs land in apps/web/public/pages and pretty path is formed.

Usage:
  python3 apps/crawler/tools/smoke_generate_page.py
"""

import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'apps', 'crawler'))

os.environ.setdefault('OUTLET_SITE_BASE_URL', 'https://discounts.deluxo.co.kr')
os.environ.setdefault('OUTLET_PAGES_DIR', os.path.join(REPO, 'apps', 'web', 'public', 'pages'))

from crawler_organized import generate_html  # type: ignore


def main():
    detail_data = {
        'id': 'smoke-event-2025',
        '제목': '[송도] 스모크 테스트 페이지',
        '기간': '10.01 ~ 10.31',
        '상세 제목': '스모크 테스트 상세 제목',
        '상세 기간': '10.01 ~ 10.31',
        '시작일': '2025-10-01',
        '종료일': '2025-10-31',
        '지점명': '송도',
        '썸네일': 'https://via.placeholder.com/800',
        '상세 링크': 'https://example.com',
        '혜택 설명': '이 페이지는 출력 경로 검증용 더미입니다.',
        '상품 리스트': [
            {'브랜드': '테스트브랜드', '제품명': '테스트 상품', '가격': '₩9,999', '이미지': 'https://via.placeholder.com/400'}
        ]
    }

    url_path = generate_html(detail_data, detail_data['id'])
    print('✅ Generated:', url_path)


if __name__ == '__main__':
    main()
