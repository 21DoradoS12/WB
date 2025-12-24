FROM python:3.13-slim

WORKDIR /wb_bot

ENV PYTHONPATH=/wb_bot

# Устанавливаем системные зависимости для OpenCV, Tesseract и других библиотек
RUN apt update && \
    apt install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 \
        libglx0 \
        libegl1 \
        tesseract-ocr \
        tesseract-ocr-rus \
        tesseract-ocr-eng && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt