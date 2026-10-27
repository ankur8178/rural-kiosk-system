import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

def speak_text(text):
    print(f"Speaking: {text}")
    try:
        subprocess.run(["espeak", text], check=False)
    except Exception as e:
        print(f"Speech generation error: {e}")

@app.route("/speak", methods=["POST"])
def speak():
    data = request.get_json() or {}
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400
    speak_text(text)
    return jsonify({"status": "success", "message": "Speaking initiated"})

if __name__ == "__main__":
    print("Raspberry Pi Audio Client listening on port 5001...")
    speak_text("Audio client is ready.")
    app.run(host="0.0.0.0", port=5001, debug=False)
