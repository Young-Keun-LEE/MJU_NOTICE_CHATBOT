import requests
from bs4 import BeautifulSoup

def get_mju_notices(category_code: str = "255", limit: int = 8):
    """
    명지대학교 공지사항 크롤러 (텍스트/코드 자동 변환 기능 탑재)
    """
    
    # ---------------------------------------------------------
    # [핵심 수정] Gemini가 한국어로 보내도 숫자로 바꿔주는 매핑 테이블
    # ---------------------------------------------------------
    mapping = {
        # 일반 공지 관련
        "일반": "255", "공지": "255", "255": "255",
        
        # 학사 공지 관련
        "학사": "257", "수강": "257", "졸업": "257", "휴학": "257", "복학": "257", "257": "257",
        
        # 장학 공지 관련
        "장학": "259", "학자금": "259", "대출": "259", "259": "259",
        
        # 취업 공지 관련
        "취업": "260", "진로": "260", "창업": "260", "인턴": "260", "현장": "260", "260": "260"
    }

    # 1. 입력값 정리 (공백 제거 등)
    clean_input = str(category_code).strip()
    
    # 2. 매핑 테이블에서 적절한 코드 찾기
    # 기본값은 '255'(일반공지)로 설정
    target_code = "255" 
    
    for key, val in mapping.items():
        if key in clean_input:
            target_code = val
            break
            
    # ---------------------------------------------------------

    # 디버깅용 출력
    board_names = {"255": "일반공지", "257": "학사공지", "259": "장학공지", "260": "취창업공지"}
    board_name = board_names.get(target_code, "일반공지")
    
    print(f"🕵️ [Crawler] '{clean_input}' -> '{target_code}({board_name})'로 변환하여 접속 중...")
    
    url = f"https://www.mju.ac.kr/mjukr/{target_code}/subview.do"
    
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select("tbody tr")
        
        print(f"📊 [Debug] 발견된 전체 행(Row) 수: {len(rows)}")

        notices = []
        for row in rows:
            columns = row.select("td")
            if len(columns) < 2: continue

            # 제목 찾기 (2번째 or 3번째 칸)
            title_col = columns[1]
            link_tag = title_col.select_one("a")
            if not link_tag and len(columns) > 2:
                title_col = columns[2]
                link_tag = title_col.select_one("a")

            if link_tag:
                # 텍스트 다림질 (공백/엔터 제거)
                raw_text = link_tag.text
                title = " ".join(raw_text.split())
                
                link = link_tag['href']
                if link.startswith("/"):
                    link = "https://www.mju.ac.kr" + link
                
                date = "날짜없음"
                for col in columns[2:]:
                    text = col.text.strip()
                    if len(text) == 10 and "." in text:
                        date = text
                        break

                notices.append(f"- [{date}] {title}\n  (링크: {link})")
            
            if len(notices) >= limit:
                break
        
        if not notices:
            return f"'{board_name}'에서 공지사항을 찾지 못했습니다. (URL: {url})"

        result_text = "\n".join(notices)
        return f"명지대학교 {board_name} 최신 목록입니다 ({len(notices)}개):\n\n{result_text}"

    except Exception as e:
        print(f"❌ [Crawler] 에러 발생: {e}")
        return f"에러 발생: {str(e)}"