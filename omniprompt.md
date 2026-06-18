# MASTER PROMPT: Générateur Vocal de Post-Production (Projet "Dry-Voice-Omni")

## 1. Contexte et Rôle de l'IA
Tu es un développeur Python expert spécialisé dans les interfaces Gradio et le traitement audio. Ton rôle est d'écrire le code complet d'une application web locale destinée à un ingénieur du son. 
L'objectif de l'application est de générer des pistes vocales "dry" (voix pures) pour de la post-production dans un DAW. L'application est un "Dual-Engine" utilisant l'API Google (Gemini via Live API) pour le Moteur 1, et l'API OpenAI (`gpt-4o-audio-preview`) pour le Moteur 2.

## 2. Stack Technique
* **Backend & Interface :** Python 3, `gradio` (fonctions asynchrones `async`/`await`).
* **API Génération Audio (Moteur 1) :** `google-genai` via la **Live API** (`client.aio.live.connect`) pour Gemini.
* **API Génération Audio (Moteur 2) :** `openai` (modèle `gpt-4o-audio-preview` en appel asynchrone).
* **API Direction d'Acteur :** `anthropic` (modèle `claude-haiku-4-5-20251001` pour l'analyse de script).
* **Traitement Audio :** `pydub` (assemblage de flux PCM 16-bit 24kHz brut de Gemini vers WAV 48kHz).
* **Utilitaires :** `python-dotenv` (pour fallback local uniquement).
* **Déploiement :** Docker (Render.com) pour la prod, Batch script pour le dev local.

## 3. Architecture de l'Interface (Gradio)
L'interface doit être organisée en deux onglets principaux :

### Onglet 1 : Studio (Génération)
* **Menu déroulant "Moteur de Rendu" :** Choix entre Gemini (Moteur 1) et OpenAI (Moteur 2).
* **Didascalies Intelligentes (Stealth Mode) :** Un bouton appelant Claude Haiku pour suggérer une direction vocale. Cette direction est stockée de manière invisible en arrière-plan et est injectée directement dans le System Prompt.
* **Sélecteur de Durée :** Boutons radio (Rapide, Normal, Long) qui définissent le rythme imposé à l'IA.
* **Zone de texte principale :** Pour le script/prompt.
* **Menu déroulant "Personnage" :** Dynamique. Affiche les personnages Gemini (ex: "Le Tavernier" -> `Charon`) ou les 11 voix OpenAI.
* **Bouton :** "Générer la piste".
* **Lecteur de sortie :** Composant `gr.Audio` pour écouter et télécharger le résultat.

### Onglet 2 : Paramètres (Settings)
* **Clés API :** Champs texte (masqués en mode password) pour charger les clés `GOOGLE_API_KEY`, `OPENAI_API_KEY` et `ANTHROPIC_API_KEY`. Un script JavaScript (`js=...` dans Gradio) sauvegarde et recharge ces clés directement depuis le **LocalStorage du navigateur** de l'utilisateur (stratégie "Bring Your Own Key" pour protéger le serveur cloud). Le backend ne doit JAMAIS écrire dans le fichier `.env` du serveur.
* **System Prompt (Éditable) :** Un bloc de texte large contenant la directive agressive de "Negative Prompting" (voir section 4.1). Doit être modifiable par l'utilisateur.

## 4. Logique d'Affaires et Traitement Audio (CRITIQUE)

### 4.1. Le System Prompt (Negative Prompting)
La directive suivante doit être envoyée avec **chaque** requête API pour garantir un signal pur, et doit être modifiable dans l'onglet Paramètres :
> "ROLE: You are a professional French-Canadian voice actor from Montreal, Quebec.
ENVIRONMENT: Professional soundproof vocal booth.
TASK: Voice the provided script naturally.
CRITICAL RULES:
1. AUDIO QUALITY: Output MUST be completely "dry". NO background music, NO room reverberation...
2. ACCENT & DIALECT: Speak in French with a natural, authentic standard Quebec accent...
3. NO FILLER: Begin acting the script immediately. DO NOT introduce the audio."

* **Moteur 1 (Gemini) :** Utiliser la **Live API** de Google (`client.aio.live.connect`). Le flux `inline_data.data` est du PCM 16-bit 24kHz brut, reconstruit via `pydub`.
* **Moteur 2 (OpenAI) :** Utiliser `client.chat.completions.create` avec `modalities=["text", "audio"]`. Le flux base64 renvoyé est reconstruit via `pydub`.
* **Anti-conversational wrapper :** Le texte final envoyé doit TOUJOURS être encapsulé dans une instruction stricte de ne pas faire d'introduction (ex: "CRITICAL INSTRUCTION: DO NOT INTRODUCE THE SCRIPT...").

### 4.3. Gestion des Fichiers et Erreurs
* **Indépendance Système (Cloud & Local) :** Tous les fichiers temporaires doivent aller dans un dossier local `temp/`.
* **FFmpeg Hybride :** Le backend doit vérifier dynamiquement s'il est sous Windows (utiliser un exécutable local `bin/ffmpeg.exe`) ou sous Linux (utiliser le ffmpeg système de l'image Docker).
* **Nommage auto :** `[NomDuPersonnage]_[YYYYMMDD]_[HHMMSS].wav`.
* **Robustesse :** Envelopper les appels API dans des blocs `try/except`. Si l'API timeout, retourner un message d'erreur clair dans l'interface Gradio sans faire crasher le serveur Python.

---

## 5. HISTORIQUE DES DÉCISIONS (CE QU'IL NE FAUT ABSOLUMENT PAS FAIRE)
*Pour t'éviter de fausses bonnes idées, voici les chemins architecturaux que nous avons expressément rejetés lors du brainstorming :*

* **REJETÉ : Moteur Vidéo Veo.**
    * *Pourquoi :* Google Veo est trop coûteux et limitatif au niveau des quotas (exige une facturation spécifique Google Cloud) uniquement pour en extraire de l'audio. L'API OpenAI (gpt-audio) est beaucoup plus efficace et économique pour le rôle de Moteur 2.
* **REJETÉ : Sélection dynamique de la voix par un LLM (Auto-Voice).**
    * *Pourquoi :* Si un LLM analyse le texte pour choisir la voix, cela détruit la continuité du personnage en post-production. Le choix de la voix (`Charon`, `Aoede`, etc.) doit rester fermement verrouillé par le choix du menu "Personnage".
* **REJETÉ : Hardcoder le System Prompt dans le backend.**
    * *Pourquoi :* L'ingénieur du son doit pouvoir ajuster le niveau de "Negative Prompting" directement depuis l'interface Gradio sans toucher au code source.

## 6. Action Requise
Génère le script Python complet (`app.py`) ainsi que le fichier `requirements.txt` nécessaires pour lancer ce projet. Ajoute des commentaires en français pour expliquer les étapes de traitement avec `pydub` et la gestion du contexte pour le Mode Script Long.