from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

url = "https://api.groq.com/openai/v1/chat/completions"

@app.route("/api/chat", methods=["POST"])
def chat():
    # Get API key from environment variable at request time
    API_KEY = os.getenv("GROQ_API_KEY")
    if not API_KEY:
        return jsonify({"error": "Missing GROQ_API_KEY environment variable"}), 500
    
    data = request.get_json()
    messages = data.get("messages")

    if not messages or not isinstance(messages, list):
        return jsonify({"error": "No messages provided or invalid format"}), 400

    messages_for_openai = []
    for msg in messages:
        sender = msg.get("sender")
        if sender == "user":
            role = "user"
        elif sender == "bot":
            role = "assistant"
        elif sender == "system":
            role = "system"
        else:
            continue  # Skip invalid roles

        text = msg.get("text", "")
        messages_for_openai.append({"role": role, "content": text})

    # Limit to last 10 messages to avoid token limits
    if len(messages_for_openai) > 10:
        # Keep system message if it exists, then last 9 messages
        system_msg = None
        if messages_for_openai[0]["role"] == "system":
            system_msg = messages_for_openai[0]
            messages_for_openai = messages_for_openai[-9:]
        else:
            messages_for_openai = messages_for_openai[-10:]
        
        if system_msg:
            messages_for_openai.insert(0, system_msg)

    # Debug logging to inspect request before sending
    print("Sending request to Groq API:", messages_for_openai)

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": messages_for_openai
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return jsonify({"reply": response.json()["choices"][0]["message"]["content"]})
        else:
            print(f"Error calling Groq API: {response.status_code}")
            print(f"Response text: {response.text}")
            return jsonify({"error": f"API error: {response.status_code}"}), 500
    except Exception as e:
        print(f"Exception calling Groq API: {e}")
        return jsonify({"error": str(e)}), 500

# Vercel serverless function handler
def handler(request):
    return app(request)
