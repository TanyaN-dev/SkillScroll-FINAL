import os
import asyncio
from typing import Dict, Any
import traceback
import json
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))

app = FastAPI(title="SkillScroll MVP API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODELS_TO_TRY = [
    "gemini-2.5-flash-lite",
    "gemini-1.5-flash"
]

async def call_gemini_with_fallback(contents):
    last_exception = None
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(model_name)
            response = await asyncio.to_thread(model.generate_content, contents)
            return response
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            last_exception = e
            continue
            
    raise Exception(f"All Gemini models failed. Last error: {last_exception}")

@app.get("/start_negotiation")
async def start_negotiation(quest_id: str = "quest-1"):
    system_instruction = (
        "You are a strict, impatient, and aggressive Mandi wholesaler from Mysore, Karnataka. "
        "Your job is to lowball the price as much as possible and pressure the silk weaver to accept a bad deal.\n\n"
        "Always reply in natural, spoken Kannada only. Use simple words and short sentences.\n"
        "Be pushy, use expressions like 'Arre', 'en maadodu', 'tago illa bidu', etc.\n"
        "Never agree easily. Never break character. Never speak in English unless the user does.\n\n"
        "Keep every reply under 25 words."
    )
    
    context = "a product"
    if quest_id == "quest-1":
        context = "Mysore silk"
    elif quest_id == "quest-2":
        context = "goods on credit"
    elif quest_id == "quest-3":
        context = "handicrafts"
        
    prompt = f"{system_instruction}\n\nGive your initial lowball offer for {context} to start the negotiation:"
    
    try:
        response = await call_gemini_with_fallback([prompt])
        return {"text": response.text.strip()}
    except Exception as e:
        print(f"Error in /start_negotiation: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=503, detail="Gemini is temporarily unavailable")

async def mock_bhashini_stt(audio_bytes: bytes) -> str:
    """Mock Speech-to-Text using Gemini natively with fallback."""
    if not audio_bytes or len(audio_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Empty or invalid audio file received.")
    
    try:
        prompt = "Transcribe the following speech accurately. Do not add any extra text or commentary. Capture whatever text is spoken."
        audio_part = {
            "mime_type": "audio/webm",
            "data": audio_bytes
        }
        response = await call_gemini_with_fallback([prompt, audio_part])
        text = response.text.strip()
        if not text:
            raise ValueError("Empty transcription returned from model.")
        return text
    except Exception as e:
        print(f"STT error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=503, detail="Gemini is temporarily unavailable")

async def generate_agent_response(user_text: str, quest_id: str, history_arr: list) -> Dict[str, Any]:
    system_instruction = (
        "You are a strict, impatient, and aggressive Mandi wholesaler from Mysore, Karnataka. "
        "Your job is to lowball the price as much as possible and pressure the silk weaver to accept a bad deal.\n\n"
        "Always reply in natural, spoken Kannada only. Use simple words and short sentences.\n"
        "Be pushy, use expressions like 'Arre', 'en maadodu', 'tago illa bidu', etc.\n"
        "Never agree easily. Never break character. Never speak in English unless the user does.\n\n"
        "Keep every reply under 25 words."
    )
    
    context = ""
    if quest_id == "quest-1":
        context = "Context: You are lowballing silk by 30-40%. User wants fair price."
    elif quest_id == "quest-2":
        context = "Context: You are a buyer demanding goods on credit. User wants advance."
    elif quest_id == "quest-3":
        context = "Context: You are negotiating for handicrafts."

    # Build conversation context
    history_text = ""
    for msg in history_arr:
        role = "User" if msg["role"] == "user" else "Wholesaler"
        history_text += f"{role}: {msg['parts'][0]['text']}\n"

    prompt = f"{system_instruction}\n{context}\n\nConversation History:\n{history_text}\nUser: {user_text}\nWholesaler:"
    
    try:
        response = await call_gemini_with_fallback([prompt])
        text = response.text.strip()
        
        score = min(100, max(20, len(user_text) * 2 + 10))
        margin_saved = f"{min(40, score//2)}%"
        
        return {
            "text": text,
            "confidence": score,
            "margin_saved": margin_saved
        }
    except Exception as e:
        print(f"Gemini error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=503, detail="Gemini is temporarily unavailable")

@app.post("/negotiate")
async def negotiate(
    quest_id: str = Form(...),
    history: str = Form("[]"),
    audio: UploadFile = File(...)
):
    try:
        audio_bytes = await audio.read()
        if not audio_bytes or len(audio_bytes) < 1000:
            return JSONResponse(status_code=400, content={"detail": "Empty or invalid audio file."})
            
        history_arr = json.loads(history)
        
        user_text = await mock_bhashini_stt(audio_bytes)
        agent_reply = await generate_agent_response(user_text, quest_id, history_arr)
        
        return JSONResponse(content={
            "user_text": user_text,
            "text": agent_reply["text"],
            "confidence": agent_reply["confidence"],
            "margin_saved": agent_reply["margin_saved"]
        })
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    except Exception as e:
        print(f"Error in /negotiate: {e}")
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})

# Mount frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
