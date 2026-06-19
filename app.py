import os
import io
import base64
import tempfile
from datetime import datetime
import gradio as gr
from google import genai
from google.genai import types
import anthropic
from openai import AsyncOpenAI
import base64
from pydub import AudioSegment
from dotenv import load_dotenv
import tiktoken
import re
import warnings

# Suppression des avertissements de dépréciation (ex: session.send)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Chargement de l'environnement (Clé API)
load_dotenv()

# Forcer tous les dossiers temporaires en local pour garantir l'indépendance totale
local_dir = os.path.dirname(os.path.abspath(__file__))
local_temp_dir = os.path.join(local_dir, "temp")
os.makedirs(local_temp_dir, exist_ok=True)
os.environ["GRADIO_TEMP_DIR"] = local_temp_dir
os.environ["TMPDIR"] = local_temp_dir
os.environ["TMP"] = local_temp_dir
os.environ["TEMP"] = local_temp_dir
tempfile.tempdir = local_temp_dir

# Configuration de Pydub pour utiliser FFmpeg en local (Windows) ou système (Linux/Render)
bin_dir = os.path.join(local_dir, "bin")
ffmpeg_path = os.path.join(bin_dir, "ffmpeg.exe")
if os.name == "nt" and os.path.exists(ffmpeg_path):
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
    AudioSegment.converter = ffmpeg_path
# Si sur Linux, Pydub utilisera automatiquement le ffmpeg installé via apt-get dans le conteneur.

# --- CONFIGURATION DES VOIX GOOGLE GEMINI ---
# On utilise les voix standard de Gemini. Vous pouvez ajouter d'autres identifiants si besoin.
CHARACTER_MAP = {
    "Le Tavernier (Grave)": "Charon",
    "La Narratrice (Douce)": "Aoede",
    "Le Héros (Jeune)": "Puck",
    "Le Méchant (Sombre)": "Fenrir",
    "La Jeune Fille (Calme)": "Kore",
    "L'Enfant (Énergique)": "Aoede"
}

OPENAI_VOICE_MAP = {
    "Alloy (Androgyne, Neutre & Versatile)": "alloy",
    "Ash (Neutre, Calme & Mesuré)": "ash",
    "Ballad (Femme, Mélodieuse & Fluide)": "ballad",
    "Coral (Femme, Amicale & Énergique)": "coral",
    "Echo (Homme, Chaleureux & Profond)": "echo",
    "Fable (Homme, Conteur Expressif)": "fable",
    "Nova (Femme, Énergique & Professionnelle)": "nova",
    "Onyx (Homme, Grave & Sérieux)": "onyx",
    "Sage (Homme, Mature & Réfléchi)": "sage",
    "Shimmer (Femme, Douce & Calme)": "shimmer",
    "Verse (Femme, Rythmique & Poétique)": "verse"
}

DEFAULT_SYSTEM_PROMPT = """ROLE: You are a professional French-Canadian voice actor from Montreal, Quebec (québécois).
ENVIRONMENT: Professional soundproof vocal booth.
TASK: Interpret, then Voice the provided script naturally.

CRITICAL RULES:
1. AUDIO QUALITY: Output MUST be completely "dry". NO background music, NO room reverberation, NO ambient noise, NO foley/sound effects. ONLY the raw human voice.
2. ACCENT & DIALECT: Speak in French Canadian with a natural, authentic standard Quebec accent (Accent québécois). Do not use heavy slang or "joual". The pronunciation should clearly be from Montreal (authentic rhythm and intonation). Under NO CIRCUMSTANCE should you sound like you are from France.
3. NO FILLER: Begin acting the script immediately. DO NOT introduce the audio. DO NOT acknowledge the prompt. NO conversational filler."""

def count_tokens(text):
    """Estimation simple (Gemini n'utilise pas tiktoken, on fait une estimation moyenne)"""
    return int(len(text.split()) * 1.3) if text else 0

def format_audio_to_daw_standard(audio_segment):
    """Convertit l'audio en 48 kHz, 24-bit WAV"""
    audio_segment = audio_segment.set_frame_rate(48000)
    # L'export réel en 24-bit se fera lors de la sauvegarde finale avec pydub
    return audio_segment

async def generate_audio_chunk(client, model_name, text_chunk, voice_id, system_prompt, conversation_history):
    """Appelle la Live API Gemini pour générer un chunk audio natif et retourne l'audio Pydub et le nouveau message."""
    
    contents = conversation_history.copy()
    
    # Contournement pour inclure le contexte dans un système asynchrone qui crée de nouvelles sessions
    if not contents and system_prompt:
        final_text = f"CONSIGNES STRICTES POUR L'ACTEUR :\n{system_prompt}\n\n--- FIN DES CONSIGNES ---\n\nCRITICAL: DO NOT INTRODUCE THE SCRIPT. DO NOT SAY 'D'accord' OR 'Voici'. START YOUR ACTING PERFORMANCE IMMEDIATELY:\n\n{text_chunk}"
    else:
        final_text = f"CRITICAL: DO NOT INTRODUCE THE SCRIPT. DO NOT SAY 'D'accord' OR 'Voici'. START YOUR ACTING PERFORMANCE IMMEDIATELY:\n\n{text_chunk}"
        
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice_id
                )
            )
        )
    )

    audio_bytes = bytearray()
    assistant_text = ""
    
    # Connexion asynchrone à la Live API
    async with client.aio.live.connect(model=model_name, config=config) as session:
        await session.send(input=final_text, end_of_turn=True)
        
        async for msg in session.receive():
            if msg.server_content and msg.server_content.model_turn:
                for part in msg.server_content.model_turn.parts:
                    if part.text:
                        assistant_text += part.text
                    if part.inline_data:
                        audio_bytes.extend(part.inline_data.data)
                            
    if not audio_bytes:
         raise ValueError("L'API Gemini n'a pas retourné de données audio via la Live API.")
         
    # Gemini renvoie un flux PCM brut 16-bit 24kHz (sans en-tête WAV)
    audio_segment = AudioSegment(
        data=bytes(audio_bytes),
        sample_width=2,
        frame_rate=24000,
        channels=1
    )
    
    assistant_message = {"role": "model", "parts": [{"text": assistant_text if assistant_text else " "}]}
    
    return audio_segment, assistant_message

async def generate_openai_audio_chunk(client, model_name, text_chunk, voice_id, system_prompt, conversation_history):
    """Appelle l'API OpenAI pour générer un chunk audio et retourne l'audio Pydub et le nouveau message."""
    messages = conversation_history.copy()
    if system_prompt and not messages:
        messages.append({"role": "system", "content": system_prompt})
        
    strict_user_prompt = f"CRITICAL INSTRUCTION: DO NOT INTRODUCE THE SCRIPT. DO NOT SAY 'D'accord', 'Voici', or any conversational filler. Start your acting performance immediately.\n\nSCRIPT TO PERFORM:\n{text_chunk}"
    messages.append({"role": "user", "content": strict_user_prompt})
    
    response = await client.chat.completions.create(
        model=model_name,
        modalities=["text", "audio"],
        audio={"voice": voice_id, "format": "wav"},
        messages=messages
    )
    
    audio_b64 = response.choices[0].message.audio.data
    audio_bytes = base64.b64decode(audio_b64)
    audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes))
    
    assistant_transcript = response.choices[0].message.audio.transcript
    assistant_message = {"role": "assistant", "content": assistant_transcript}
    
    return audio_segment, assistant_message

def generate_hidden_didascalies(script, anthropic_key_override):
    """Génère une direction d'acteur cachée via l'API Anthropic (Claude)."""
    if not script.strip():
        raise gr.Error("Veuillez fournir un script pour générer des didascalies.")
        
    anthropic_key = anthropic_key_override.strip() if anthropic_key_override.strip() else os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_key:
        raise gr.Error("Clé API Anthropic manquante. Ajoutez-la dans l'onglet Paramètres.")
        
    client = anthropic.Anthropic(api_key=anthropic_key)
    
    prompt = f"""Tu es un directeur d'acteurs de doublage.
Analyse le script suivant et fournis une brève instruction de jeu (didascalie émotionnelle et tonale) pour l'acteur virtuel.
CRITICAL: L'instruction DOIT ÊTRE RÉDIGÉE EN ANGLAIS pour maximiser la compréhension des modèles audio (ex: "Hesitant tone, with a hint of sadness" ou "Energetic and fast voice").
Ne retourne QUE la didascalie en anglais, sans aucun texte d'introduction ni guillemets.

Script :
{script}"""

    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            messages=[{"role": "user", "content": prompt}]
        )
        direction = ""
        for block in message.content:
            if hasattr(block, "text"):
                direction += block.text
        return direction.strip(), gr.update(value="✅ Didascalies prêtes", variant="primary")
    except Exception as e:
        raise gr.Error(f"Erreur Anthropic : {str(e)}")

async def process_generation(engine, script, duration_slider, hidden_didascalies, char_key, google_api_key_override, openai_api_key_override, system_prompt):
    """Fonction principale appelée par Gradio."""
    if not script.strip():
        raise gr.Error("Le script est vide.")
        
    final_script = script
    
    # Injection du rythme dans le system_prompt
    pacing_instruction = ""
    if duration_slider == 0:
        pacing_instruction = "\n\nCRITICAL CONSTRAINT: TARGET DURATION IS 3 SECONDS (Target word count: 8 to 9 words)."
    elif duration_slider == 2:
        pacing_instruction = "\n\nCRITICAL CONSTRAINT: TARGET DURATION IS 10 SECONDS (Target word count: 25 to 30 words)."
    else:
        pacing_instruction = "\n\nCRITICAL CONSTRAINT: TARGET DURATION IS 6 SECONDS (Target word count: 15 to 18 words)."
        
    didascalie_instruction = f"\n\nACTOR DIRECTION (DIDASCALIES): {hidden_didascalies}" if hidden_didascalies else ""
    final_system_prompt = system_prompt + didascalie_instruction + pacing_instruction
        
    google_api_key = google_api_key_override.strip() if google_api_key_override.strip() else os.environ.get("GOOGLE_API_KEY")
    openai_api_key = openai_api_key_override.strip() if openai_api_key_override.strip() else os.environ.get("OPENAI_API_KEY")
    
    try:
        final_audio = None
        
        if engine == "Moteur 2 : OpenAI":
            if not openai_api_key:
                raise gr.Error("Clé API OpenAI manquante. Ajoutez-la dans les paramètres ou le fichier .env.")
            
            client = AsyncOpenAI(api_key=openai_api_key)
            oai_model = "gpt-audio"
            oai_voice_id = OPENAI_VOICE_MAP[char_key]
            
            gr.Info("Génération d'une seule traite via OpenAI...")
            final_audio, _ = await generate_openai_audio_chunk(client, oai_model, final_script, oai_voice_id, final_system_prompt, [])
            
        else:
            # Moteur Gemini Audio
            if not google_api_key:
                raise gr.Error("Clé API Google manquante. Ajoutez-la dans les paramètres ou le fichier .env.")
                
            client = genai.Client(api_key=google_api_key)
            voice_id = CHARACTER_MAP[char_key]
            gemini_model = "gemini-3.1-flash-live-preview"
            
            gr.Info("Génération d'une seule traite via Gemini...")
            final_audio, _ = await generate_audio_chunk(client, gemini_model, final_script, voice_id, final_system_prompt, [])
            
        # Conformation DAW : 48kHz
        final_audio = format_audio_to_daw_standard(final_audio)
        
        # Sauvegarde sur disque
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_char_name = char_key.split(" ")[0]
        filename = f"{safe_char_name}_{timestamp}.wav"
        
        output_dir = os.path.join(local_dir, "outputs")
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        # Export avec pydub en 24-bit
        final_audio.export(filepath, format="wav", parameters=["-c:a", "pcm_s24le"])
        
        return filepath
        
    except Exception as e:
        raise gr.Error(f"Erreur lors de la génération : {str(e)}")

def preview_prompt(duration_slider, hidden_didascalies, system_prompt):
    """Fonction de débogage pour afficher le prompt complet."""
    pacing_instruction = ""
    if duration_slider == 0:
        pacing_instruction = "\n\nCRITICAL CONSTRAINT: TARGET DURATION IS 3 SECONDS (Target word count: 8 to 9 words)."
    elif duration_slider == 2:
        pacing_instruction = "\n\nCRITICAL CONSTRAINT: TARGET DURATION IS 10 SECONDS (Target word count: 25 to 30 words)."
    else:
        pacing_instruction = "\n\nCRITICAL CONSTRAINT: TARGET DURATION IS 6 SECONDS (Target word count: 15 to 18 words)."
        
    didascalie_instruction = f"\n\nACTOR DIRECTION (DIDASCALIES): {hidden_didascalies}" if hidden_didascalies else ""
    return system_prompt + didascalie_instruction + pacing_instruction

# --- Interface Gradio ---
custom_theme = gr.themes.Base(
    primary_hue="sky",
    secondary_hue="blue",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "sans-serif"]
).set(
    body_background_fill="#0f172a",
    body_text_color="#f8fafc",
    block_background_fill="#1e293b",
    block_border_width="1px",
    block_border_color="#334155",
    button_primary_text_color="#ffffff",
    input_background_fill="#0f172a",
)

custom_css = """
body { background: radial-gradient(circle at 50% 0%, #0f172a 0%, #000000 100%); min-height: 100vh; margin: 0; padding: 0; }
gradio-app { display: flex !important; align-items: center !important; justify-content: center !important; min-height: 100vh !important; padding: 2rem 1rem !important; box-sizing: border-box !important; }
@media (max-height: 900px) { gradio-app { align-items: flex-start !important; } }
.gradio-container { max-width: 1000px !important; margin: 0 auto !important; width: 100%; border: 1px solid #1e293b; border-radius: 12px; padding: 1.5rem 2rem !important; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8); background: #0f172a; }
.transparent-block, .transparent-block > div, .transparent-block > .contain { background: transparent !important; border: none !important; box-shadow: none !important; }
button.primary { background: #0284c7 !important; color: #ffffff !important; border: none !important; font-weight: 600 !important; letter-spacing: 0.5px; border-radius: 6px !important; transition: all 0.2s; box-shadow: 0 4px 6px -1px rgba(2, 132, 199, 0.4); }
button.primary:hover { background: #0369a1 !important; transform: translateY(-1px); box-shadow: 0 6px 8px -1px rgba(2, 132, 199, 0.5); }
textarea, input[type="text"], input[type="password"], select { background: #1e293b !important; border: 1px solid #475569 !important; color: #f8fafc !important; border-radius: 6px !important; }
textarea:focus, input[type="text"]:focus, input[type="password"]:focus, select:focus { border-color: #38bdf8 !important; box-shadow: 0 0 0 1px #38bdf8 !important; }
input[type="radio"]:checked, input[type="checkbox"]:checked { background-color: #38bdf8 !important; border-color: #38bdf8 !important; }
h1 { text-align: center; color: #f8fafc; font-weight: 800 !important; letter-spacing: -0.5px; border-bottom: none !important; margin-bottom: 0.5rem !important; }
.tabs { background: transparent !important; border: none !important; }
.tab-nav { border-bottom: 2px solid #1e293b !important; background: transparent !important; margin-bottom: 1rem !important; }
.tab-nav button { color: #94a3b8 !important; font-weight: 600 !important; padding: 0.5rem 1rem !important; transition: all 0.2s; border: none !important; background: transparent !important;}
.tab-nav button:hover { color: #f1f5f9 !important; }
.tab-nav button.selected { color: #38bdf8 !important; border-bottom: 2px solid #38bdf8 !important; }
/* Hide ugly Gradio footers */
footer { display: none !important; }
/* Force Radio to stretch equally on one line */
.full-width-radio > div { display: flex !important; flex-wrap: nowrap !important; width: 100% !important; gap: 0.5rem !important; }
.full-width-radio label { flex: 1 1 0 !important; display: flex !important; justify-content: center !important; text-align: center !important; padding: 0.5rem 0 !important; min-width: 0 !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important;}
/* Tall Generate Button */
.tall-btn { height: 100% !important; min-height: 80px !important; margin-top: 10px !important; }
"""

with gr.Blocks(title="Voice-Gen") as demo:
    gr.Markdown("# 🎙️ Voice-Gen", elem_classes="transparent-block")
    
    with gr.Tabs(elem_classes="transparent-block"):
        # ONGLET 1 : STUDIO
        with gr.Tab("Studio"):
            with gr.Row():
                with gr.Column(scale=2):
                    script_input = gr.Textbox(
                        label="Script",
                        lines=7,
                        placeholder="Entrez le texte ici..."
                    )
                    token_display = gr.Markdown("*Tokens estimés : 0*")
                    hidden_didascalies = gr.State("")
                    
                    # Mise à jour en temps réel des tokens et reset des didascalies
                    def update_script_input(text):
                        t = count_tokens(text)
                        return f"*Tokens estimés (texte) : {t}*", "", gr.update(value="🤖 Enrichir le script avec des didascalies", variant="secondary")
                    
                    gr.Markdown("### 🎭 Didascalies intelligentes (Claude AI)", elem_classes="transparent-block")
                    suggest_direction_btn = gr.Button("🤖 Enrichir le script avec des didascalies", variant="secondary")
                    
                    # Câblage de l'événement de changement du script (Doit être défini après le bouton)
                    script_input.change(fn=update_script_input, inputs=script_input, outputs=[token_display, hidden_didascalies, suggest_direction_btn])
                    
                    gr.Markdown("### ⏱️ Durée", elem_classes="transparent-block")
                    duration_slider = gr.Radio(
                        choices=["🚀 Rapide", "🚶 Normal", "🐢 Long"],
                        value="🚶 Normal",
                        show_label=False,
                        type="index",
                        interactive=True,
                        elem_classes="full-width-radio"
                    )
                        
                with gr.Column(scale=1):
                    engine_radio = gr.Radio(
                        choices=["Moteur 1 : Gemini", "Moteur 2 : OpenAI"],
                        value="Moteur 1 : Gemini",
                        label="Moteur de Rendu"
                    )
                    with gr.Row(equal_height=True):
                        character_dropdown = gr.Dropdown(
                            choices=list(CHARACTER_MAP.keys()),
                            value=list(CHARACTER_MAP.keys())[0],
                            label="Personnage (Gemini)",
                            scale=3
                        )
                        voice_demo_audio = gr.Audio(
                            label="Pré-écoute",
                            interactive=False,
                            autoplay=True,
                            type="filepath",
                            scale=1
                        )
                    
                    def update_character_dropdown(engine_choice):
                        if engine_choice and "OpenAI" in engine_choice:
                            choices = list(OPENAI_VOICE_MAP.keys())
                            return gr.update(label="Personnage (OpenAI)", choices=choices, value=choices[0])
                        else:
                            choices = list(CHARACTER_MAP.keys())
                            return gr.update(label="Personnage (Gemini)", choices=choices, value=choices[0])
                            
                    def update_demo_audio(engine_choice, character_name):
                        # Find the internal ID of the voice
                        voice_id = "charon" # Default
                        if engine_choice and "OpenAI" in engine_choice:
                            voice_id = OPENAI_VOICE_MAP.get(character_name, "alloy")
                        else:
                            voice_id = CHARACTER_MAP.get(character_name, "Charon")
                        
                        demo_path = os.path.join("demos", f"{voice_id}.mp3".lower())
                        if os.path.exists(demo_path):
                            return demo_path
                        return None
                            
                    engine_radio.change(
                        fn=update_character_dropdown, 
                        inputs=engine_radio, 
                        outputs=character_dropdown,
                        queue=False
                    )
                    
                    character_dropdown.change(
                        fn=update_demo_audio,
                        inputs=[engine_radio, character_dropdown],
                        outputs=voice_demo_audio,
                        queue=False
                    )
                    
                    generate_btn = gr.Button("🎧 Générer la piste", variant="primary", size="lg", elem_classes="tall-btn")
                    
            audio_output = gr.Audio(label="Piste Générée (48kHz, 24-bit WAV)", type="filepath")
            
            with gr.Accordion("🔍 Outils de Débogage (Temporaire)", open=False, visible=False, elem_classes="transparent-block"):
                debug_btn = gr.Button("Afficher le System Prompt Final")
                debug_output = gr.Textbox(label="Texte caché envoyé aux acteurs virtuels", lines=8, interactive=False)
            
            gr.Markdown("<div style='text-align: right; font-size: 0.75rem; color: #64748b; margin-top: 1rem;'>v2.1 - Sébastien Bédard - 2026 | <a href='https://github.com/sebedard-creator/Voice-Gen' target='_blank' style='color: #64748b; text-decoration: underline;'>GitHub</a></div>", elem_classes="transparent-block")
            
        # ONGLET 2 : PARAMÈTRES
        with gr.Tab("Paramètres"):
            with gr.Row():
                api_key_input = gr.Textbox(
                    label="Clé API Google (Gemini Moteur 1)",
                    info="[Obtenir une clé Google AI Studio (Gratuit)](https://aistudio.google.com/app/apikey)",
                    type="password",
                    placeholder="AIzaSy...",
                    value=os.environ.get("GOOGLE_API_KEY", "")
                )
                openai_key_input = gr.Textbox(
                    label="Clé API OpenAI (GPT-4o Moteur 2)",
                    info="[Obtenir une clé OpenAI](https://platform.openai.com/api-keys)",
                    type="password",
                    placeholder="sk-proj-...",
                    value=os.environ.get("OPENAI_API_KEY", "")
                )
            with gr.Row():
                anthropic_key_input = gr.Textbox(
                    label="Clé API Anthropic (Direction d'acteur)",
                    info="[Obtenir une clé Anthropic Console](https://console.anthropic.com/settings/keys)",
                    type="password",
                    placeholder="sk-ant-...",
                    value=""
                )
                save_key_btn = gr.Button("💾 Sauvegarder les clés dans mon navigateur", variant="primary")
                
            save_key_btn.click(
                fn=None,
                inputs=[api_key_input, openai_key_input, anthropic_key_input],
                outputs=None,
                js="""
                (g_key, o_key, a_key) => {
                    localStorage.setItem('google_api_key', g_key);
                    localStorage.setItem('openai_api_key', o_key);
                    localStorage.setItem('anthropic_api_key', a_key);
                    alert("Clés API sauvegardées sécuritairement dans votre navigateur !");
                }
                """
            )
            
            system_prompt_input = gr.Textbox(
                label="System Prompt (Negative Prompting)",
                lines=4,
                value=DEFAULT_SYSTEM_PROMPT,
                info="Ce prompt est envoyé à chaque requête pour forcer un signal audio 'dry' sans effets ni bruit de fond."
            )
            with gr.Row():
                save_prompt_btn = gr.Button("💾 Sauvegarder ce Prompt", variant="primary")
                default_prompt_btn = gr.Button("🔄 Revenir au Prompt par Défaut")
                
            save_prompt_btn.click(
                fn=None,
                inputs=[system_prompt_input],
                outputs=None,
                js="""
                (sys_prompt) => {
                    localStorage.setItem('system_prompt', sys_prompt);
                    alert("System Prompt sauvegardé dans le navigateur !");
                }
                """
            )
            default_prompt_btn.click(
                fn=lambda: DEFAULT_SYSTEM_PROMPT,
                inputs=[],
                outputs=[system_prompt_input]
            )

    # Injection du LocalStorage au chargement de la page
    load_js = """
    () => {
        let g_key = localStorage.getItem('google_api_key') || "";
        let o_key = localStorage.getItem('openai_api_key') || "";
        let a_key = localStorage.getItem('anthropic_api_key') || "";
        let sys = localStorage.getItem('system_prompt') || "";
        return [g_key, o_key, a_key, sys];
    }
    """
    
    def merge_load(g_js, o_js, a_js, sys_js):
        g_final = g_js if g_js else os.environ.get("GOOGLE_API_KEY", "")
        o_final = o_js if o_js else os.environ.get("OPENAI_API_KEY", "")
        a_final = a_js if a_js else os.environ.get("ANTHROPIC_API_KEY", "")
        s_final = sys_js if sys_js else DEFAULT_SYSTEM_PROMPT
        return g_final, o_final, a_final, s_final

    demo.load(
        fn=merge_load,
        inputs=[api_key_input, openai_key_input, anthropic_key_input, system_prompt_input],
        outputs=[api_key_input, openai_key_input, anthropic_key_input, system_prompt_input],
        js=load_js
    )

    # Câblage des boutons
    suggest_direction_btn.click(
        fn=generate_hidden_didascalies,
        inputs=[script_input, anthropic_key_input],
        outputs=[hidden_didascalies, suggest_direction_btn]
    )

    generate_btn.click(
        fn=process_generation,
        inputs=[engine_radio, script_input, duration_slider, hidden_didascalies, character_dropdown, api_key_input, openai_key_input, system_prompt_input],
        outputs=audio_output
    )
    
    debug_btn.click(
        fn=preview_prompt,
        inputs=[duration_slider, hidden_didascalies, system_prompt_input],
        outputs=debug_output
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7866))
    demo.launch(server_name="0.0.0.0", server_port=port, theme=custom_theme, css=custom_css, ssr_mode=False)
