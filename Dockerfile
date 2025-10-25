FROM python:3.11-slim

WORKDIR /app

# Kerakli paketlar
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python kutubxonalarini o'rnatish
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kodlarni nusxalash
COPY . .

# Botni ishga tushirish
CMD ["python", "bot.py"]