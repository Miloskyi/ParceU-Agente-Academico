FROM python:3.11-slim

# Dependencias del sistema para sentence-transformers y chromadb
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Crear directorio de ChromaDB si no existe
RUN mkdir -p data/chroma_db data/raw data/tramites

# Puerto expuesto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
