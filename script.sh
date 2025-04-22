#!/bin/bash

set -e

# Vérifie si Docker est installé
if ! command -v docker &> /dev/null; then
  echo "❌ Docker n'est pas installé. Pour l'installer, veuillez vous rendre sur https://www.docker.com"
fi

# Vérifie si le dossier audio existe
if [ ! -d "./audio" ]; then
  echo "❌ Le dossier audio n'existait pas. Veuillez rajouter vos fichiers .mp3 dedans et relancer le script."
  mkdir audio
  exit 1
fi

# Construire l'image Docker
echo "🔧 Construction de l'image Docker..."
docker build -t whisper-runner .

# Lancer la transcription
echo "▶️ Lancement de la transcription..."
docker run --rm -v "$(pwd)/audio":/app whisper-runner

echo "✅ Transcription terminée. Les fichiers générés sont dans le dossier audio"
