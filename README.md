# Rural Kiosk System 🎙️🤖🌐

A distributed, production-grade, voice-enabled assistant architecture engineered for rural kiosk environments. The system bridges a powerful central processing server (**macOS / Flask / OpenAI Whisper / Google Gemini AI**) with a low-power edge device (**Raspberry Pi audio client**) to provide robust, localized, hands-free multimodal assistance.

---

## 🌟 Comprehensive System Overview

Rural kiosks require high reliability under varying network and hardware conditions. This system addresses those challenges by decoupling audio capture from heavy AI reasoning:

1. **Audio Acquisition & Playback (Client Edge):** The Raspberry Pi listens for kiosk users, records queries, and dispatches audio streams while remaining responsible for local text-to-speech feedback playback via `espeak`.
2. **Local Transcription Engine (Server Core):** Instead of depending on fragile or metered cloud speech-to-text APIs, incoming audio is transcribed locally using **OpenAI Whisper** (`tiny` model configuration for minimal latency).
3. **Multimodal Intelligence & Safety (Google Gemini AI):** Transcriptions and visual payloads are routed directly to **Google Gemini** models. The server incorporates resilient retry mechanisms (`retry` logic handling `503`, `429`, and `UNAVAILABLE` exceptions with exponential backoff) to guarantee uptime.
4. **Web Dashboard Interface:** Provides a lightweight HTML/CSS mobile-responsive interface for operators or administrators to test audio feeds, upload files, and monitor model output in real time.

---

## 🏗️ System Architecture & Data Flow

```text
┌────────────────────────────────────────────────────────┐
│               Raspberry Pi (Client Node)               │
│  - Captures Audio / Input                              │
│  - Executes /speak Endpoint via espeak                 │
└────────────────────────────────────────────────────────┘
                           │
                           │ HTTP POST /speak (JSON Payload)
                           ▼
┌────────────────────────────────────────────────────────┐
│               macOS (Central Server Node)              │
│  ├── Flask Web Dashboard (Mobile-Optimized UI)         │
│  ├── OpenAI Whisper (Offline Audio Transcription)      │
│  └── Google Gemini AI Engine (LLM & Vision Processing) │
└────────────────────────────────────────────────────────┘
```

---

## 📂 Project Directory Structure

```text
rural-kiosk-system/
│
├── server/
│   ├── app.py              # Main Flask backend server (Handles routing, Whisper, & Gemini integration)
│   └── record_and_send.py  # Local hardware utility script for standalone recording & endpoint testing
│
└── client/
    └── client.py           # Lightweight Flask speaker client running on the Raspberry Pi listener port
```

---

## 🛠️ Core Components Deep Dive

### 1. `server/app.py` (Central Brain)
* **Framework:** Flask web server running on port `5000`.
* **Speech-to-Text:** Integrates `openai-whisper` loaded into memory at startup.
* **AI Model Interaction:** Uses the official `google-genai` SDK with built-in fault tolerance and error handling for model throttling or temporary backend unavailability.
* **Security Design:** Fully complies with secret scanning protections by initializing credentials dynamically via `os.environ.get("GEMINI_API_KEY")`.

### 2. `server/record_and_send.py` (Testing Utility)
* Facilitates direct hardware integration tests on local audio hardware before dispatching payloads to the central server.

### 3. `client/client.py` (Edge Speaker Node)
* Runs a lightweight Flask listener on port `5001`.
* Listens for incoming `/speak` POST requests from the central server and triggers synthetic speech generation via `espeak`.

---

## 🚀 Installation & Deployment Guide

### Prerequisites
* Python 3.9 or higher.
* `espeak` package installed on the Raspberry Pi node (`sudo apt install espeak`).

### Step 1: Clone and Configure the Repository
```bash
git clone https://github.com/ankur8178/rural-kiosk-system.git
cd rural-kiosk-system
```

### Step 2: Server Deployment (macOS / Central Node)
```bash
cd server
pip install flask openai-whisper google-genai pillow requests

# Set your secure API key
export GEMINI_API_KEY="your_actual_gemini_api_key_here"

# Launch the server
python app.py
```

### Step 3: Client Deployment (Raspberry Pi Edge Node)
SSH into your Raspberry Pi device:
```bash
cd client
pip install flask requests

# Launch the speaker listener client
python client.py
```

---

## 🔒 Security & Environment Configuration

* **Zero Hardcoded Secrets:** This repository strictly prohibits hardcoded API tokens. 
* Always provision your environment variables before running the application:
  ```bash
  export GEMINI_API_KEY="your_api_key_here"
  ```