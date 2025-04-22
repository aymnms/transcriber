FROM python:3.10-slim

# Installer ffmpeg et dépendances
RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Installer Whisper
RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git

# Dossier de travail
WORKDIR /app

# Transcrire les fichiers audios du dossier monté
CMD ["bash", "-c", "shopt -s nocaseglob nullglob; for file in *.{m4a,mp4,mkv,amr,dss,dvf,bmf,tta,tak,ape,alac,flac,ra,rm,wma,opus,ogg,aac,mp3,pcm,raw,au,aiff,wav}; do whisper \"$file\"  --model base; done"]
# model list: tiny base small medium large turbo