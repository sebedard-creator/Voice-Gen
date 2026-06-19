# 🎙️ Voice-Gen

Welcome to **Voice-Gen** (formerly Dry-Voice-Omni), a professional-grade, dual-engine AI voice generation studio designed specifically for audio engineers and post-production workflows.

This web application generates completely "dry", clinical, and artifact-free human vocal tracks, ready to be dropped straight into any Digital Audio Workstation (DAW).

## ✨ Key Features

* **Dual-Engine Architecture:**
  * **Engine 1 (Google Gemini):** Utilizes the ultra-low latency Google GenAI Live API (WebSockets) combined with native multimodal AI voices (Charon, Puck, Aoede, etc.) for highly expressive, generative acting.
  * **Engine 2 (OpenAI):** Utilizes the `gpt-4o-audio-preview` model, giving you access to **11 official OpenAI voices** (Alloy, Ash, Ballad, Coral, Echo, Fable, Nova, Onyx, Sage, Shimmer, Verse) for unparalleled semantic pacing and clarity.
* **AI-Assisted Voice Direction (Stealth Mode):** Integrated with **Anthropic (Claude 3.5 Haiku)**. Simply input your script's context, and Claude will automatically generate professional acting directions (tone, pacing, emotion). This direction is injected silently into the AI's system prompt *without altering your original script*, ensuring clean performance cues.
* **Granular Duration Control:** A dedicated UI slider allows you to force a specific pacing ("Rapide", "Normal", "Long") to fine-tune the final audio's total duration and the actor's word-per-second speed.
* **Clinical "Dry" Output (Anti-Conversational):** A strict, hardcoded system prompt absolutely forbids the AI from adding Foley, room reverberation, or sound effects, ensuring a true zero-noise-floor studio recording exported in **24-bit 48kHz WAV format**. The system also implements a last-millisecond anti-filler injection to prevent the AI from saying "Okay, here is the audio".
* **Zero-Trust Cloud Security (BYOK):** "Bring Your Own Key" architecture. API keys and custom system prompts are saved entirely on the client-side (`localStorage` via JavaScript). The server never touches, stores, or logs your private keys.
* **Hybrid Deployment (Cloud & Local):**
  * **Local Windows:** Run `start.bat`. It will automatically use local `ffmpeg.exe` binaries for rapid local testing without installing anything on your OS.
  * **Cloud (Render.com):** Fully Dockerized. Push this repo to GitHub and connect it to Render. It will automatically build the Linux container and install the system `ffmpeg` packages.

## 🚀 How to Run Locally (Windows)

1. Clone or download this repository.
2. (Optional) Create a `.env` file in the root directory with your API keys for quick local developer testing.
3. Double-click on `dry_voice_omni_bg.vbs`. This will silently launch the Python backend in the background and open your default web browser to the Gradio interface.
4. To stop the server, double-click `stop.bat`.

## ☁️ How to Deploy on Render.com (Free Tier)

1. Push this repository to your own GitHub account.
2. Go to [Render.com](https://render.com) and create a **New Web Service**.
3. Connect your GitHub repository.
4. Ensure the **Runtime** is set to `Docker` (it should detect the `Dockerfile` automatically).
5. Select the **Free** instance type.
6. Click **Create Web Service**. 
7. Done! *Note: You do not need to set any environment variables in Render. Simply enter your API keys securely in the application's UI once it is live.*

## 🛠️ Tech Stack

* **Backend & UI:** Python 3.11, Gradio 6
* **Audio Processing:** Pydub, FFmpeg
* **AI SDKs:** `google-genai`, `openai`, `anthropic`

## 👨‍💻 Author

Created by **Sébastien Bédard** (2026). Version 2.1.
