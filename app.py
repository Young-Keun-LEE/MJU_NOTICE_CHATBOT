import os
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
import google.generativeai as genai

# Import local crawler module
from crawler import get_mju_notices

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key')

# -------------------------------------------------------------------------
# Configuration: Google Gemini API
# -------------------------------------------------------------------------
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing in environment variables.")

genai.configure(api_key=GOOGLE_API_KEY)

# Safety settings to prevent the model from blocking responses unnecessarily
SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

# -------------------------------------------------------------------------
# Configuration: OAuth 2.0 (Google Login)
# -------------------------------------------------------------------------
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    # Using server metadata URL for automatic configuration (JWKS, endpoints, etc.)
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# -------------------------------------------------------------------------
# Tools & Model Initialization
# -------------------------------------------------------------------------
def call_crawler_tool(category: str, limit: int = 8) -> str:
    """
    Wrapper function for the crawler to be used by Gemini's function calling.
    
    Args:
        category (str): The category code or keyword for the notice board.
        limit (int): Number of notices to fetch.
    
    Returns:
        str: Formatted string of notices.
    """
    print(f"[Server] ⚡ Gemini Request - Category: {category}, Limit: {limit}")
    return get_mju_notices(category_code=category, limit=limit)

# Register tools for the LLM
tools = [call_crawler_tool]

# Initialize the Generative Model with tools and configuration
model = genai.GenerativeModel(
    model_name='gemini-2.5-flash', # Using the stable 1.5 Flash model
    tools=tools,
    safety_settings=SAFETY_SETTINGS
)

# Start the chat session with automatic function calling enabled
chat = model.start_chat(enable_automatic_function_calling=True)

# -------------------------------------------------------------------------
# Routes: View & Authentication
# -------------------------------------------------------------------------
@app.route('/')
def index():
    """Render the main page. Passes user info if logged in."""
    user_info = session.get('user')
    return render_template('index.html', user=user_info)

@app.route('/login')
def login():
    """Redirect user to Google's OAuth 2.0 login page."""
    redirect_uri = url_for('auth_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/callback')
def auth_callback():
    """Handle the callback from Google after successful login."""
    try:
        token = google.authorize_access_token()
        
        # Explicitly fetch user info using the OpenID Connect endpoint
        user_info_url = 'https://openidconnect.googleapis.com/v1/userinfo'
        user_info = google.get(user_info_url).json()
        
        # Store user info in the server-side session
        session['user'] = user_info
        return redirect('/')
        
    except Exception as e:
        print(f"[Auth Error] Failed to authenticate: {e}")
        return redirect('/')

@app.route('/logout')
def logout():
    """Clear user session and redirect to home."""
    session.pop('user', None)
    return redirect('/')

# -------------------------------------------------------------------------
# Routes: Chat API
# -------------------------------------------------------------------------
@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    API Endpoint to handle chat messages.
    Receives JSON: {"message": "user input"}
    Returns JSON: {"response": "model response"}
    """
    user_input = request.json.get('message')
    
    if not user_input:
        return jsonify({'error': 'Empty message received'}), 400

    try:
        # Send message to Gemini (handles tool execution internally)
        response = chat.send_message(user_input)
        return jsonify({'response': response.text})
        
    except Exception as e:
        print(f"[Chat Error] {e}")
        return jsonify({'error': str(e)}), 500

# -------------------------------------------------------------------------
# Main Entry Point
# -------------------------------------------------------------------------
if __name__ == '__main__':
    # Run the Flask app (Debug mode enabled for development)
    app.run(debug=True, port=5000)