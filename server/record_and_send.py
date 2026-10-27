import sounddevice as sd
from scipy.io.wavfile import write
import requests

# Audio configuration
FS = 16000  # Sample rate required by Whisper
DURATION = 5  # Recording duration in seconds
OUTPUT_FILE = "recorded_query.wav"
SERVER_URL = "http://127.0.0.1:5000/process-audio"

# Replace with your Raspberry Pi IP address or hostname (e.g., http://voicepi.local:5001/speak)
PI_SPEAK_URL = "http://10.245.179.18:5001/speak"
print("Press ENTER to start recording your question (5 seconds)...")
input()
print("Recording... Speak into your MacBook microphone now!")

# Record audio from Mac built-in microphone
recording = sd.rec(int(DURATION * FS), samplerate=FS, channels=1, dtype='int16')
sd.wait()
print("Recording complete. Sending to server...")

# Save locally to WAV
write(OUTPUT_FILE, FS, recording)

# Send to Flask server on MacBook
with open(OUTPUT_FILE, "rb") as f:
    files = {"audio": f}
    try:
        response = requests.post(SERVER_URL, files=files)
        if response.status_code == 200:
            data = response.json()
            print("\n--- RESULTS ---")
            print("You said:", data.get("transcript"))
            print("Gemini response:", data.get("response"))
            print("----------------\n")
            
            # Send the response text to the Pi to speak through earphones
            reply_text = data.get("response")
            requests.post(PI_SPEAK_URL, json={"text": reply_text})
            print("Sent response to Raspberry Pi for audio playback!")
        else:
            print("Server error:", response.text)
    except Exception as e:
        print("Error sending audio:", e)
