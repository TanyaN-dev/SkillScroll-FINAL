# SkillScroll MVP - Audio-Native Negotiation Agent

SkillScroll is an audio-first mobile web application designed to help rural Karnataka artisans practice and improve their negotiation skills against AI-driven realistic buyer personas.

## Features
- **Reels-Style Feed**: Vertical scroll of quest cards.
- **Audio Native UI**: "Hold to Talk" push-to-talk interface.
- **AI Roleplay**: Driven by Gemini Flash with specific local personas (Mandi wholesaler, strict buyer, tourist).
- **Stateless & Scalable**: Designed to be deployed on Google Cloud Run.

## Tech Stack
- **Backend**: FastAPI (Python 3.11)
- **AI Roleplay**: Google Generative AI (Gemini 1.5 Flash)
- **Database**: Firebase Admin SDK (Firestore)
- **Frontend**: Vanilla HTML/JS/CSS (Mobile-first)
- **STT/TTS**: Bhashini (Mocked with async placeholders for MVP)

## Setup Instructions

1. **Clone the repository and navigate to the directory.**

2. **Create a virtual environment and install dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Environment Variables:**
   Copy `.env.example` to `.env` and fill in the values.
   ```bash
   cp .env.example .env
   ```
   You MUST provide a `GEMINI_API_KEY`. 
   For Firebase, provide either the individual `FIREBASE_*` variables, or if you have a `serviceAccountKey.json`, set `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`.

4. **Run Locally:**
   ```bash
   uvicorn main:app --reload
   ```
   The application will be available at `http://localhost:8000`.

## Demo Steps
1. Open `http://localhost:8000` in a mobile browser or use Chrome DevTools device emulator (e.g., iPhone 12/13).
2. Scroll down the feed to see the quests.
3. Tap "Start Negotiation" on "Mandi Hustle".
4. Press and hold the green microphone button, say "I cannot sell for less than 500 rupees", and release.
5. Watch the state change to "Thinking...", see the response appear, and listen to the audio playback (using browser TTS fallback for the MVP).
6. View the feedback modal that pops up after the response.
7. Click "Share to WhatsApp" to test the social sharing.

## SDG 5 & 8 Alignment
- **SDG 5 (Gender Equality)**: Empowers female artisans by building confidence in negotiation and business dealings, historically male-dominated spheres.
- **SDG 8 (Decent Work and Economic Growth)**: Provides tools for artisans to secure fair prices, reducing exploitation by middlemen and driving better economic outcomes for micro-businesses.

## How to Swap Mock Bhashini Functions
In `main.py`, locate `mock_bhashini_stt` and `mock_bhashini_tts`.
1. Inside `mock_bhashini_stt`, make a `httpx` or `aiohttp` POST request to the Bhashini ASR endpoint, passing the `audio_bytes`. Extract and return the transcribed text.
2. Inside `mock_bhashini_tts`, make a POST request to the Bhashini TTS endpoint with the `text`. Return the binary audio response. 
3. In `script.js` `sendAudioToBackend`, replace the `SpeechSynthesisUtterance` fallback with playing the audio blob returned from the backend.
