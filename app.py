import os
import json
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth  # 로그인 라이브러리

# 로컬 크롤러 가져오기
from crawler import get_mju_notices 

load_dotenv()
app = Flask(__name__)

# [필수] 세션 관리를 위한 비밀키 설정
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key')

# Gemini API 설정
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# ---------------------------------------------------------
# [추가됨] 구글 로그인 설정 (OAuth)
# ---------------------------------------------------------
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    # ★ 핵심: 이 주소에 jwks_uri를 포함한 모든 설정 정보가 들어있습니다.
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# ---------------------------------------------------------
# [기존] 크롤러 도구 함수
# ---------------------------------------------------------
def call_crawler_tool(category: str, limit: int = 8):
    print(f"[Server] ⚡ Gemini 요청: 카테고리 {category}, 개수 {limit}")
    return get_mju_notices(category_code=category, limit=limit)

tools = [call_crawler_tool]

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    tools=tools,
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
)
chat = model.start_chat(enable_automatic_function_calling=True)

# ---------------------------------------------------------
# [라우트] 페이지 및 로그인 관련
# ---------------------------------------------------------

@app.route('/')
def index():
    # 로그인된 사용자 정보가 있으면 가져옴
    user_info = session.get('user')
    return render_template('index.html', user=user_info)

@app.route('/login')
def login():
    # 구글 로그인 페이지로 이동시킴
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth_callback():
    # 1. 토큰 받아오기 (성공함)
    token = google.authorize_access_token()
    
    # 2. [수정 포인트] 사용자 정보 가져오기
    # 예전에는 'userinfo'라고만 썼지만, 이제는 전체 주소를 적어줘야 합니다.
    user_info_url = 'https://openidconnect.googleapis.com/v1/userinfo'
    user_info = google.get(user_info_url).json()
    
    # 3. 세션에 저장
    session['user'] = user_info
    return redirect('/')

@app.route('/logout')
def logout():
    # 로그아웃 (세션 삭제)
    session.pop('user', None)
    return redirect('/')

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    user_input = request.json.get('message')
    try:
        response = chat.send_message(user_input)
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)