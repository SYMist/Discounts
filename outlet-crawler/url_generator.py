import re
import unicodedata
from urllib.parse import quote

def generate_seo_url(title, branch):
    """
    SEO 친화적인 URL을 생성합니다.
    예: discounts.deluxo.co.kr/songdo/contemporary-ss-season-off-sale
    
    Args:
        title (str): 이벤트 제목
        branch (str): 지점명 (송도, 김포, 스페이스원)
    
    Returns:
        str: SEO 친화적인 URL 경로
    """
    
    # 지점명을 영문으로 매핑
    branch_mapping = {
        "송도": "songdo",
        "김포": "gimpo", 
        "스페이스원": "spaceone"
    }
    
    # 지점명 변환
    branch_en = branch_mapping.get(branch, "unknown")
    
    # 제목을 URL 친화적으로 변환
    def slugify(text):
        # 한글을 유지하면서 특수문자 제거
        # 1. 한글, 영문, 숫자, 공백만 유지
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        # 2. 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        # 3. 앞뒤 공백 제거
        text = text.strip()
        
        # 4. 공백을 하이픈으로 변환
        text = text.replace(' ', '-')
        
        # 5. 연속된 하이픈을 하나로
        text = re.sub(r'-+', '-', text)
        
        # 6. 앞뒤 하이픈 제거
        text = text.strip('-')
        
        return text.lower()
    
    # 제목 슬러그 생성
    title_slug = slugify(title)
    
    # URL 경로 생성
    url_path = f"{branch_en}/{title_slug}"
    
    return url_path

def generate_filename_from_url(url_path):
    """
    URL 경로를 파일명으로 변환합니다.
    예: songdo/contemporary-ss-season-off-sale -> songdo-contemporary-ss-season-off-sale.html
    """
    return f"{url_path.replace('/', '-')}.html"

def test_url_generation():
    """URL 생성 테스트"""
    test_cases = [
        ("컨템포러리 S/S 시즌오프 특가 제안", "송도"),
        ("[Renewal Open] K2 & 네파", "김포"),
        ("골든듀 36주년 창립 행사", "스페이스원"),
        ("현대홈쇼핑 2025 SUMMER BLACK FRIDAY", "송도"),
        ("[ POP-UP ] 피네플리츠", "김포")
    ]
    
    print("🔗 SEO 친화적인 URL 생성 테스트")
    print("=" * 60)
    
    for title, branch in test_cases:
        url_path = generate_seo_url(title, branch)
        filename = generate_filename_from_url(url_path)
        full_url = f"discounts.deluxo.co.kr/{url_path}"
        
        print(f"제목: {title}")
        print(f"지점: {branch}")
        print(f"URL: {full_url}")
        print(f"파일명: {filename}")
        print("-" * 40)

if __name__ == "__main__":
    test_url_generation() 