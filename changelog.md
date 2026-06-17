# Changelog - Projet Voice-Gen (ex-Dry-Voice-Omni)

Toutes les modifications apportées au projet seront tracées ici.

## [1.0.0] - 2026-06-17
### Lancement Officiel (Première version publique)
- **Déploiement Hybride (Render.com) :** L'application est désormais conçue pour être déployée publiquement sur le cloud ou exécutée localement de manière transparente.
- **Stockage Sécurisé (BYOK) :** Les clés API et le System Prompt ne sont plus jamais enregistrés sur le serveur (suppression du fichier `.env`). Un script JavaScript utilise le `LocalStorage` du navigateur web de l'utilisateur pour une sécurité multi-tenants parfaite.
- **Conteneurisation (Docker) :** Création d'un `Dockerfile` officiel pour Render afin d'installer le package système `ffmpeg` sous Linux, remplaçant intelligemment le besoin de `ffmpeg.exe` sous Windows.
- **Interface (UI) :** Refonte esthétique complète (thème sombre "Studio Console" Slate & Sky Blue), centrage automatique via CSS Grid/Flexbox, et renommage officiel en "Voice-Gen".

## [0.9.2] - 2026-06-16 (Interne)
### Ajouté (Dual-Engine)
- **Retour de GPT-4o Audio :** Intégration de l'API OpenAI (`gpt-4o-audio-preview`) comme Moteur 2 de rendu, en remplacement du moteur Veo trop restrictif.
- **Support des voix OpenAI :** Ajout d'un menu déroulant conditionnel pour sélectionner les 6 voix officielles d'OpenAI (`alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`).
- **Gestion Multi-Clés :** L'onglet paramètres enregistre désormais simultanément les clés Google, OpenAI et Anthropic dans le fichier `.env`.

## [0.9.1] - 2026-06-16 (Interne)
### Modifié (Architecture Audio)
- **Implémentation de la Live API (WebSockets) :** Refonte asynchrone (`async`/`await`) du moteur audio pour utiliser `client.aio.live.connect`.
- **Restauration de l'Audio Génératif :** Remplacement des modèles TTS de base par les modèles multimodaux natifs (`gemini-2.5-flash`, `gemini-2.0-flash`) permettant un véritable jeu d'acteur génératif.
- Assemblage du flux binaire brut (PCM 16-bit 24kHz) reçu de la Live API via `pydub`.

## [0.9.0] - 2026-06-16 (Interne)
### Modifié (Pivot Majeur)
- **Migration vers Google GenAI** : Le moteur principal de génération vocale (OpenAI) a été entièrement retiré et remplacé par l'API Google Gemini (`gemini-2.0-flash-exp`). L'application utilise les voix intégrées de Gemini (`Charon`, `Puck`, `Aoede`, etc.).
- Intégration du SDK `google-genai` et ajout d'un sélecteur de moteur ("Gemini" ou "Veo").
- Préparation du pipeline Veo pour la génération de soundscapes avec extraction vidéo -> audio via `pydub` (placeholder asynchrone).
- La direction d'acteur assistée (Anthropic) est conservée.

## [1.0.4] - 2026-06-16
### Ajouté
- Ajout d'un menu déroulant "Modèle OpenAI" dans l'onglet Paramètres. Cela permet de résoudre l'erreur 404 ("model not found") si le compte de l'utilisateur n'a pas accès au modèle `gpt-4o-audio-preview` générique. Différentes versions (dont les modèles `mini`) sont désormais sélectionnables.

## [1.0.3] - 2026-06-16
### Modifié
- Interface UI (`app.py`) : Suppression de l'accordéon (menu déroulant) pour la fonctionnalité "Direction d'acteur assistée". Les champs (Contexte, Bouton, et Direction générée) sont maintenant affichés au premier niveau de manière permanente sous le script pour un accès plus rapide.

## [1.0.2] - 2026-06-16
### Modifié
- Réorganisation de l'onglet Studio (`app.py`) : L'accordéon de la Direction d'acteur a été déplacé sous la zone de script. Cela correspond mieux au sens de lecture (le bouton "Analyser le script" vient après avoir tapé le script).

## [1.0.1] - 2026-06-16
### Corrigé
- Correction de la logique de détection automatique des dépendances dans `start.bat`. Le script vérifie désormais l'existence de `anthropic` en plus de `openai` pour garantir que toutes les librairies ajoutées récemment sont bien installées.

## [1.0.0] - 2026-06-16
### Ajouté
- **Direction d'Acteur Assistée (Claude AI)** : Intégration de l'API Anthropic (`claude-haiku-4-5-20251001`). Un nouvel accordéon dans l'onglet Studio permet de renseigner un scénario et d'obtenir une micro-direction d'acteur optimale. Cette direction est automatiquement injectée sous forme de didascalie au début du script avant d'être envoyée au moteur vocal d'OpenAI.
- Ajout du champ pour la `ANTHROPIC_API_KEY` dans l'onglet Paramètres, avec sauvegarde persistante.
- Mise à jour des dépendances (`requirements.txt`) pour inclure `anthropic`.
- Mise à jour majeure du Master Prompt (`omniprompt.md`) documentant cette nouvelle architecture hybride (Anthropic + OpenAI).

## [0.1.9] - 2026-06-16
### Ajouté
- Fonctionnalité de sauvegarde persistante de la clé API. Un bouton "Sauvegarder dans .env" a été ajouté dans l'onglet Paramètres pour écrire la clé directement dans le fichier de configuration sans avoir à l'éditer manuellement. Le champ se pré-remplit désormais avec la clé existante.

## [0.1.8] - 2026-06-16
### Modifié
- Modification du port fixe d'écoute dans `app.py`. Passage du port `7865` au port `7866` suite à un conflit réseau.

## [0.1.7] - 2026-06-16
### Modifié
- Traduction du "System Prompt" par défaut en anglais dans `app.py` et `omniprompt.md` afin d'améliorer la rigueur du modèle d'OpenAI sur les consignes techniques ("dry vocal", "no foley").

## [0.1.6] - 2026-06-16
### Modifié
- Changement de l'adresse IP d'écoute de l'application dans `app.py`. Le serveur démarre désormais sur `10.0.0.30` au lieu de l'hôte local `127.0.0.1`, permettant l'accès depuis le réseau local.

## [0.1.5] - 2026-06-16
### Modifié
- Retour à un port fixe dans `app.py` : l'application est configurée sur le port `7865` à la demande de l'utilisateur.
- Mise à jour de `start.bat` : ajout d'une vérification automatique pour installer les dépendances via `pip install -r requirements.txt` si des modules (comme `openai`) sont manquants lors du lancement.

## [0.1.4] - 2026-06-16
### Ajouté
- Script `start.bat` pour un lancement rapide et convivial. Il détecte automatiquement l'absence de FFmpeg et lance le `setup_ffmpeg.py` lors du premier démarrage.
- Script `stop.bat` pour arrêter proprement le serveur local en tâche de fond.

## [0.1.3] - 2026-06-16
### Modifié
- Suppression du port fixe (7860) dans `app.py` au lancement de Gradio. L'application trouve désormais automatiquement un port libre sur le système pour éviter les conflits avec d'autres programmes.

## [0.1.2] - 2026-06-16
### Ajouté
- Script `setup_ffmpeg.py` permettant de télécharger et d'extraire automatiquement `ffmpeg.exe` et `ffprobe.exe` dans un dossier local `Y:\Omni Prompt\bin\`.
- Configuration dans `app.py` pour forcer `pydub` à utiliser le dossier `bin\` local s'il existe. L'application est désormais 100% portable et indépendante de l'OS.

## [0.1.1] - 2026-06-16
### Modifié
- Isolation des chemins de fichiers dans `app.py` : Forçage de `tempfile` et `Gradio` pour qu'ils utilisent le dossier local `Y:\Omni Prompt\temp` au lieu du répertoire temporaire du système.
- Redirection des fichiers audios finaux générés vers un dossier local `Y:\Omni Prompt\outputs` pour garantir une indépendance totale de l'application vis-à-vis du système.

## [0.1.0] - 2026-06-16
- `app.py` : Application principale avec interface Gradio (Onglets Studio et Paramètres).
- Intégration de l'API OpenAI Chat Completions avec le modèle `gpt-4o-audio-preview` pour la génération audio native.
- Implémentation du Negative Prompting (System Prompt éditable) pour garantir une voix "dry".
- "Mode Script Long" : Découpage intelligent du texte, génération séquentielle avec maintien du contexte.
- Traitement Audio avec `pydub` : Concaténation avec crossfade de 15ms, upsampling à 48kHz, et export en 24-bit WAV.
- Compteur dynamique de tokens via `tiktoken`.
- `requirements.txt` : Dépendances du projet (gradio, openai, pydub, python-dotenv, tiktoken).
- `.env` : Fichier template pour la configuration de la clé API.
- Création initiale du fichier `changelog.md` pour le suivi des modifications.
- Mise en place du protocole de synchronisation continue entre le code et le fichier de spécification `omniprompt.md`.
