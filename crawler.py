import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional

# -------------------------------------------------------------------------
# Configuration & Constants
# -------------------------------------------------------------------------
MJU_BASE_URL = "https://www.mju.ac.kr/mjukr"
DEFAULT_BOARD_ID = "255" # General Notices

# Mapping table to resolve natural language keywords to specific board IDs
# This allows the system to understand intents like "Scholarship" or "Academic"
CATEGORY_MAPPING: Dict[str, str] = {
    # General Notices (ID: 255)
    "일반": "255", "공지": "255", "255": "255",
    
    # Academic Notices (ID: 257)
    "학사": "257", "수강": "257", "졸업": "257", "휴학": "257", "복학": "257", "257": "257",
    
    # Scholarship Notices (ID: 259)
    "장학": "259", "학자금": "259", "대출": "259", "259": "259",
    
    # Career/Employment Notices (ID: 260)
    "취업": "260", "진로": "260", "창업": "260", "인턴": "260", "현장": "260", "260": "260"
}

# Human-readable names for board IDs (used for debugging and user feedback)
BOARD_NAMES: Dict[str, str] = {
    "255": "일반공지 (General)",
    "257": "학사공지 (Academic)",
    "259": "장학공지 (Scholarship)",
    "260": "취창업공지 (Career)"
}

def get_mju_notices(category_code: str = "255", limit: int = 8) -> str:
    """
    Crawls Myongji University notices based on the provided category code or keyword.
    
    This function acts as an intelligent parser that resolves natural language inputs
    into valid board IDs, fetches the HTML content, and extracts notice details.

    Args:
        category_code (str): The board ID or a related keyword (e.g., "257" or "수강신청").
        limit (int): The maximum number of notices to retrieve. Defaults to 8.

    Returns:
        str: A formatted string containing the list of notices or an error message.
    """
    
    # 1. Input Sanitization & Resolution
    clean_input = str(category_code).strip()
    target_code = DEFAULT_BOARD_ID
    
    # Resolve input keyword to board ID
    for key, val in CATEGORY_MAPPING.items():
        if key in clean_input:
            target_code = val
            break
            
    board_name = BOARD_NAMES.get(target_code, "Unknown Board")
    print(f"🕵️ [Crawler] Resolving '{clean_input}' -> Target Board: '{target_code}' ({board_name})")
    
    # Construct the target URL
    url = f"{MJU_BASE_URL}/{target_code}/subview.do"
    
    try:
        # 2. HTTP Request
        # Set a timeout to prevent hanging if the server is unresponsive
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx, 5xx)
        
        # 3. HTML Parsing
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select("tbody tr")
        
        print(f"📊 [Debug] Found {len(rows)} rows in the notice board.")

        notices: List[str] = []
        
        for row in rows:
            # Stop if we have collected enough notices
            if len(notices) >= limit:
                break

            columns = row.select("td")
            # Skip invalid rows (e.g., empty or header rows)
            if len(columns) < 2: 
                continue

            # 4. Data Extraction Strategy
            # Attempt to find the title link in the 2nd column (standard layout)
            # Fallback to the 3rd column if the layout shifts (e.g., pinned icons)
            title_col = columns[1]
            link_tag = title_col.select_one("a")
            
            if not link_tag and len(columns) > 2:
                title_col = columns[2]
                link_tag = title_col.select_one("a")

            if link_tag:
                # Clean up the title text (remove excessive whitespace/newlines)
                raw_text = link_tag.text
                title = " ".join(raw_text.split())
                
                # Process the link (convert relative path to absolute URL)
                href = link_tag.get('href', '')
                link = f"https://www.mju.ac.kr{href}" if href.startswith("/") else href
                
                # Extract date (heuristic: look for YYYY.MM.DD format in subsequent columns)
                date = "Unknown Date"
                for col in columns[2:]:
                    text = col.text.strip()
                    # Check for date format (length 10 and contains dots)
                    if len(text) == 10 and "." in text:
                        date = text
                        break

                notices.append(f"- [{date}] {title}\n  (Link: {link})")
        
        # 5. Result Formatting
        if not notices:
            return f"⚠️ Could not find any notices in '{board_name}'. (URL: {url})"

        result_text = "\n".join(notices)
        header = f"📢 Myongji Univ. {board_name} - Latest {len(notices)} Notices:"
        return f"{header}\n\n{result_text}"

    except requests.RequestException as e:
        # Handle network-related errors
        error_msg = f"❌ [Network Error] Failed to connect to MJU website: {e}"
        print(error_msg)
        return error_msg
        
    except Exception as e:
        # Handle unexpected errors (parsing, etc.)
        error_msg = f"❌ [Crawler Error] An unexpected error occurred: {e}"
        print(error_msg)
        return error_msg