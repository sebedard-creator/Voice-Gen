FROM python:3.11-slim

# Installer FFmpeg pour le système Linux (Render)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier les requirements et installer les paquets
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code de l'application
COPY . .

# Exposer le port par défaut (Render peut le changer dynamiquement)
EXPOSE 7866

# Lancer l'application
CMD ["python", "app.py"]
