#!/bin/bash

set -e

echo "======================================"
echo "     Instalando RoadEye v0.1"
echo "======================================"

echo ""
echo "Actualizando Debian..."
sudo apt update

echo ""
echo "Instalando dependencias del sistema..."
sudo apt install -y \
    python3-venv \
    python3-picamera2

echo ""
echo "Creando entorno virtual..."

rm -rf .venv

python3 -m venv --system-site-packages .venv

source .venv/bin/activate

echo ""
echo "Actualizando pip..."
python -m pip install --upgrade pip

echo ""
echo "Instalando dependencias de Python..."
pip install -r requirements.txt

echo ""
echo "Comprobando instalación..."

python -c "from picamera2 import Picamera2; print('✓ Picamera2 OK')"
python -c "import fastapi; print('✓ FastAPI OK')"
python -c "import cv2; print('✓ OpenCV OK')"
python -c "import uvicorn; print('✓ Uvicorn OK')"

echo ""
echo "======================================"
echo "RoadEye instalado correctamente"
echo "======================================"
