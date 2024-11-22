import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from .api.routes import api
from .site.routes import site
from .authentication.routes import auth
from flask_migrate import Migrate
from models import db as root_db, ma
from helpers import JSONEncoder
import logging
from dotenv import load_dotenv
import requests

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
app.config.from_object(Config)  # Load configuration

# Enabling CORS for all routes in the app with specific settings
CORS(app, resources={r"/*": {"origins": ["*"]}}, supports_credentials=True)

app.json_encoder = JSONEncoder

root_db.init_app(app)
ma.init_app(app)
migrate = Migrate(app, root_db)

app.register_blueprint(site)
app.register_blueprint(auth)
app.register_blueprint(api)

logging.basicConfig(level=logging.DEBUG)

@app.route('/api/get_answer', methods=['POST'])
def get_answer():
    """
    Endpoint to process a user's query and fetch an answer from OpenAI API,
    customized for flora-related topics.
    """
    data = request.json
    user_query = data.get("query")

    # Validate input
    if not user_query:
        return jsonify({"error": "Query is missing"}), 400

    # OpenAI API endpoint and headers
    openai_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Custom system prompt for flora-related constraints
    payload = {
        "model": "gpt-4o-mini",  
        "messages": [
            {
                "role": "system",
                "content": (
                    "If users greet you or  ask who you are , greet them first  and introduce yourself as  BotaniQ AI.  You are an expert in flora, including botanics and other related biological sciences. Also , you know plants' significance in humans life , in nature and in science,  practical use cases,  history, all the latest and  upcoming related events."
                    "If they don't ask about you, only  answer questions they ask, don't greet. If they appreciate you, answer properly"
                    " Know plants' scientific description , latest studies, innovations and  applications in different industries such as Biotechnology, food, textiles, fashion, fragrance, literature, science, and medicine,Phytochemistry. As an expert recommend best platforms to learn flora, plants and related sciences. And recommmend other plarforms about above industries on users' demand ."
                    "Do not provide answers unrelated to flora or plants. If the question is unrelated, respond with: "
                    "'My expertise lies in flora and its related fields.'"
                )
            },
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(openai_url, headers=headers, json=payload)
        response.raise_for_status()
        openai_response = response.json()

        # Extract the bot's reply
        bot_reply = openai_response.get("choices", [{}])[0].get("message", {}).get("content", None)

        if not bot_reply:
            logging.error("No valid 'content' found in the OpenAI response.")
            return jsonify({"error": "Failed to get a valid response from OpenAI API."}), 500

        # Return only the assistant's message
        return jsonify({"response": bot_reply})
    except requests.exceptions.RequestException as e:
        logging.error(f"Error communicating with OpenAI API: {e}")
        return jsonify({"error": "Failed to communicate with OpenAI API"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
