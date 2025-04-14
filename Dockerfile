FROM python:3.11-slim

# Instalar dependencias básicas
RUN apt-get update && apt-get install -y wget gnupg unzip fonts-liberation libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpangocairo-1.0-0 libcairo2 libpango-1.0-0 libx11-xcb1 libxcb1 libxext6 libx11-6

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos
COPY . .

# Instalar dependencias de Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Instalar navegadores de Playwright
RUN playwright install --with-deps

# Comando para ejecutar el script
CMD ["python", "guardar_partidos_playwright.py"]
