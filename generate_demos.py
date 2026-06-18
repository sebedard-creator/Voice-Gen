import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from google import genai
from google.genai import types
from pydub import AudioSegment
import io

# Charger les clés API
load_dotenv()
from app import DEFAULT_SYSTEM_PROMPT

# S'assurer que FFmpeg est trouvé par Pydub
local_dir = os.path.dirname(os.path.abspath(__file__))
bin_dir = os.path.join(local_dir, "bin")
ffmpeg_path = os.path.join(bin_dir, "ffmpeg.exe")
if os.name == "nt" and os.path.exists(ffmpeg_path):
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    AudioSegment.converter = ffmpeg_path

# Mots à prononcer
DEMO_TEXT = "Bonjour, voici un aperçu de ma voix. Je suis prêt pour l'enregistrement."

GEMINI_VOICES = ["charon", "aoede", "puck", "fenrir", "kore"]
OPENAI_VOICES = ["alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer", "verse"]

os.makedirs("demos", exist_ok=True)

async def generate_gemini(voice):
    print(f"Génération Gemini: {voice}")
    try:
        client = genai.Client()
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            )
        )
        audio_bytes = bytearray()
        
        system_instruction = DEFAULT_SYSTEM_PROMPT
        final_text = f"CONSIGNES STRICTES POUR L'ACTEUR :\n{system_instruction}\n\n--- FIN DES CONSIGNES ---\n\nCRITICAL: DO NOT INTRODUCE THE SCRIPT. JUST READ THIS SCRIPT EXACTLY:\n\n{DEMO_TEXT}"
        
        async with client.aio.live.connect(model="gemini-3.1-flash-live-preview", config=config) as session:
            await session.send(input=final_text, end_of_turn=True)
            async for msg in session.receive():
                if msg.server_content is not None:
                    model_turn = msg.server_content.model_turn
                    if model_turn is not None:
                        for part in model_turn.parts:
                            if part.inline_data and part.inline_data.data:
                                audio_bytes.extend(part.inline_data.data)
        
        if len(audio_bytes) > 0:
            audio_segment = AudioSegment.from_raw(
                io.BytesIO(audio_bytes),
                sample_width=2,
                frame_rate=24000,
                channels=1
            )
            audio_segment = audio_segment.set_frame_rate(48000)
            output_path = os.path.join("demos", f"{voice}.mp3")
            audio_segment.export(output_path, format="mp3")
            print(f"  -> Sauvegardé : {output_path}")
        else:
            print(f"  -> ERREUR: Audio vide pour {voice}")
    except Exception as e:
        print(f"  -> ERREUR Gemini {voice}: {e}")

async def generate_openai(voice):
    print(f"Génération OpenAI: {voice}")
    try:
        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model="gpt-audio",
            modalities=["text", "audio"],
            audio={"voice": voice, "format": "wav"},
            messages=[
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": f"CRITICAL INSTRUCTION: DO NOT INTRODUCE THE SCRIPT. Start immediately with the script performance.\n\nSCRIPT TO PERFORM:\n{DEMO_TEXT}"}
            ]
        )
        audio_b64 = response.choices[0].message.audio.data
        import base64
        audio_bytes = base64.b64decode(audio_b64)
        
        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
        audio_segment = audio_segment.set_frame_rate(48000)
        output_path = os.path.join("demos", f"{voice}.mp3")
        audio_segment.export(output_path, format="mp3")
        print(f"  -> Sauvegardé : {output_path}")
    except Exception as e:
        print(f"  -> ERREUR OpenAI {voice}: {e}")

async def main():
    # Générer Gemini
    for v in GEMINI_VOICES:
        await generate_gemini(v)
        
    # Générer OpenAI
    for v in OPENAI_VOICES:
        await generate_openai(v)

if __name__ == "__main__":
    asyncio.run(main())
