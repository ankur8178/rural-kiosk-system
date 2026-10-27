import os
import time
import requests
from flask import Flask, request, jsonify, render_template_string
from google import genai
import whisper
from PIL import Image

app = Flask(__name__)

# Initialize the official Google GenAI Client with your new API key
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE"))

# Load Whisper model for local audio transcription (using tiny for speed)
print("Loading Whisper model...")
whisper_model = whisper.load_model("tiny")

# Raspberry Pi speaker listener URL
PI_SPEAK_URL = "http://10.245.179.18:5001/speak"

def generate_with_retry(contents, model="gemini-3.8-flash", retries=3, delay=1):
    for attempt in range(retries):
        try:
            return client.models.generate_content(model=model, contents=contents)
        except Exception as e:
            if "503" in str(e) or "429" in str(e) or "UNAVAILABLE" in str(e):
                print(f"API busy/quota hit. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                raise e
    raise Exception("API limit reached or model busy. Please try again shortly.")

# Polished, high-reliability mobile kiosk dashboard
HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>Rural Kiosk Assistant</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f4f7f6; color: #333; text-align: center; padding: 15px; margin: 0; }
        .container { max-width: 480px; margin: auto; background: white; padding: 20px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        h2 { color: #1a73e8; margin-bottom: 5px; font-size: 22px; }
        p.sub { color: #666; font-size: 13px; margin-bottom: 20px; }
        .card { background: #f8f9fa; padding: 15px; border-radius: 12px; margin-bottom: 12px; text-align: left; border: 1px solid #e9ecef; }
        .card h3 { margin: 0 0 8px 0; font-size: 15px; color: #202124; }
        input[type="file"] { display: none; }
        input[type="text"] { width: calc(100% - 20px); padding: 10px; border: 1px solid #dadce0; border-radius: 8px; font-size: 14px; margin-bottom: 8px; outline: none; }
        .btn { background: #1a73e8; color: white; border: none; padding: 12px 16px; font-size: 15px; border-radius: 8px; cursor: pointer; display: block; width: 100%; text-align: center; box-sizing: border-box; font-weight: 500; text-decoration: none; }
        .btn-green { background: #137333; }
        .btn-purple { background: #8430ce; }
        #result-box { margin-top: 15px; padding: 15px; background: #e8f0fe; border-radius: 10px; font-size: 15px; color: #174ea6; display: none; text-align: left; line-height: 1.4; border-left: 4px solid #1a73e8; }
        .loading { display: none; font-size: 13px; color: #1a73e8; margin-top: 8px; font-weight: 500; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Rural Kiosk Assistant</h2>
        <p class="sub">Select an input method below</p>
        
        <!-- Photo Detection -->
        <div class="card">
            <h3>📷 Photo Detection</h3>
            <form action="/process-phone-vision" method="POST" enctype="multipart/form-data">
                <label class="btn" style="cursor:pointer;">
                    Capture / Upload Image 
                    <input type="file" name="image" accept="image/*" capture="environment" onchange="if(this.files.length > 0) { showLoading('vision'); this.form.submit(); }">
                </label>
            </form>
            <div id="loading-vision" class="loading">Analyzing image...</div>
        </div>

        <!-- Voice Assistant -->
        <div class="card">
            <h3>🎤 Voice Assistant</h3>
            <form action="/process-audio" method="POST" enctype="multipart/form-data">
                <label class="btn btn-green" style="cursor:pointer;">
                    Record / Upload Voice 
                    <input type="file" name="audio" accept="audio/*" capture="microphone" onchange="if(this.files.length > 0) { showLoading('audio'); this.form.submit(); }">
                </label>
            </form>
            <div id="loading-audio" class="loading">Transcribing audio & thinking...</div>
        </div>

        <!-- Text Query -->
        <div class="card">
            <h3>⌨️ Text Query</h3>
            <input type="text" id="text-input" placeholder="Type your question here...">
            <button type="button" class="btn btn-purple" onclick="sendText()">Submit Text Query</button>
            <div id="loading-text" class="loading">Generating response...</div>
        </div>

        <div id="result-box"></div>
    </div>

    <script>
        function showLoading(type) {
            if (type === 'vision') document.getElementById('loading-vision').style.display = 'block';
            if (type === 'audio') document.getElementById('loading-audio').style.display = 'block';
        }

        async function sendText() {
            const text = document.getElementById("text-input").value.trim();
            const resultBox = document.getElementById("result-box");
            const loader = document.getElementById("loading-text");
            
            if (!text) return;

            loader.style.display = "block";
            resultBox.style.display = "none";

            try {
                const res = await fetch("/process-text", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: text })
                });
                const data = await res.json();
                
                loader.style.display = "none";
                resultBox.style.display = "block";
                
                if (res.ok && data.response) {
                    resultBox.innerHTML = `<b>Query:</b> ${text}<br><br><b>Assistant:</b> ${data.response}`;
                } else {
                    resultBox.innerHTML = `<b>Error:</b> ${data.error || "Server error occurred"}`;
                }
            } catch (err) {
                loader.style.display = "none";
                resultBox.style.display = "block";
                resultBox.innerHTML = `<b>Error:</b> Could not reach server.`;
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_DASHBOARD)

@app.route("/process-phone-vision", methods=["POST"])
def process_phone_vision():
    if "image" not in request.files or request.files["image"].filename == "":
        return "No image selected. Please go back and pick an image.", 400

    image_file = request.files["image"]
    image_path = "temp_vision_capture.jpg"
    image_file.save(image_path)

    try:
        img = Image.open(image_path)
        img.thumbnail((800, 800))
        response = generate_with_retry(
            contents=[img, "Identify the main object or item in this image and describe it clearly and concisely."]
        )
        reply_text = response.text.strip().replace("*", "").replace("`", "")
        
        try:
            requests.post(PI_SPEAK_URL, json={"text": reply_text}, timeout=2)
        except Exception as e:
            print(f"Pi speaker note: {e}")

        return f"""
        <html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body style="font-family:sans-serif; text-align:center; padding:40px; background:#f8f9fa;">
            <div style="max-width:400px; margin:auto; background:white; padding:30px; border-radius:16px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#1a73e8;">Vision Result</h2>
                <p style="font-size:18px; color:#333; margin:20px 0; line-height:1.4;">{reply_text}</p>
                <a href="/" style="display:inline-block; background:#1a73e8; color:white; padding:12px 24px; border-radius:8px; text-decoration:none; font-weight:500;">Back to Dashboard</a>
            </div>
        </body></html>
        """
    except Exception as e:
        return f"Error: {str(e)}", 500
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)

@app.route("/process-audio", methods=["POST"])
def process_audio():
    if "audio" not in request.files or request.files["audio"].filename == "":
        return "No audio provided. Please go back and record again.", 400

    audio_file = request.files["audio"]
    audio_path = "temp_query.wav"
    audio_file.save(audio_path)

    try:
        result = whisper_model.transcribe(audio_path)
        user_text = result["text"].strip()
        print(f"🎤 Transcribed Voice: {user_text}")
        
        if not user_text:
            reply_text = "I couldn't hear anything. Please try recording again."
        else:
            prompt = f"Answer concisely: {user_text}"
            response = generate_with_retry(contents=prompt)
            reply_text = response.text.strip()

        try:
            requests.post(PI_SPEAK_URL, json={"text": reply_text}, timeout=2)
        except Exception as e:
            print(f"Pi speaker note: {e}")

        return f"""
        <html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head>
        <body style="font-family:sans-serif; text-align:center; padding:40px; background:#f8f9fa;">
            <div style="max-width:400px; margin:auto; background:white; padding:30px; border-radius:16px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
                <h2 style="color:#137333;">Voice Result</h2>
                <p style="font-size:15px; color:#666; margin-bottom:5px;"><b>You said:</b> "{user_text}"</p>
                <p style="font-size:18px; color:#333; margin:20px 0; line-height:1.4;">{reply_text}</p>
                <a href="/" style="display:inline-block; background:#1a73e8; color:white; padding:12px 24px; border-radius:8px; text-decoration:none; font-weight:500;">Back to Dashboard</a>
            </div>
        </body></html>
        """
    except Exception as e:
        return f"Error: {str(e)}", 500
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

@app.route("/process-text", methods=["POST"])
def process_text():
    data = request.get_json() or {}
    user_text = data.get("text", "")
    
    if not user_text:
        return jsonify({"error": "No text provided"}), 400

    try:
        prompt = f"Answer concisely: {user_text}"
        response = generate_with_retry(contents=prompt)
        reply_text = response.text.strip()

        try:
            requests.post(PI_SPEAK_URL, json={"text": reply_text}, timeout=2)
        except Exception as e:
            print(f"Pi speaker note: {e}")

        return jsonify({"response": reply_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
