# 🚀 Guía de Despliegue PARCERU

## Prerrequisitos del Sistema

### Software Requerido
- **Python 3.11+** (verificar con `python --version`)
- **Node.js 18+** (verificar con `node --version`) 
- **npm 9+** (verificar con `npm --version`)
- **Git** (para clonar el repositorio)

### Variables de Entorno Requeridas
```bash
# Requerida - API key gratuita de Groq
GROQ_API_KEY=tu_key_aqui

# Opcional - Para embeddings premium (si no se especifica usa sentence-transformers)
OPENAI_API_KEY=tu_key_opcional

# Opcional - Rutas personalizadas
CHROMA_PATH=data/chroma_db
TRAMITES_PATH=data/tramites/tramites.json
```

## Desarrollo Local (5 minutos)

### 1. Clonar y Configurar
```bash
git clone https://github.com/tu-usuario/Hackathon-UdeA-Softserve.git
cd Hackathon-UdeA-Softserve

# Configurar variables de entorno
cp .env.example .env
# Editar .env y agregar GROQ_API_KEY
```

### 2. Backend Python
```bash
# Instalar dependencias Python
pip install -r requirements.txt

# Indexar documentos (opcional - funciona sin PDFs)
# Colocar PDFs en data/raw/ antes de ejecutar:
python run_ingesta.py

# Lanzar backend FastAPI
python -m uvicorn backend.main:app --reload --port 8000
```

### 3. Frontend React (terminal separado)
```bash
cd frontend

# Instalar dependencias Node.js
npm install

# Lanzar servidor de desarrollo
npm run dev
```

### 4. Acceder a la aplicación
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Docs API**: http://localhost:8000/docs (Swagger automático)

## Testing Completo

### Backend Python
```bash
# Todos los tests
pytest tests/ -v

# Tests específicos
pytest tests/test_tramites.py -v      # Tests trámites
pytest tests/test_rag.py -v           # Tests RAG y grader

# Coverage report
pytest tests/ --cov=agentes --cov-report=html
```

### Frontend React
```bash
cd frontend

# Tests unitarios
npm test

# Tests con coverage
npm run test:coverage

# Tests en modo watch
npm run test:watch
```

## Producción - Opción 1: Docker (Recomendado)

### 1. Build con Docker
```bash
# Build imagen completa
docker build -t parceru:latest .

# Run con variables de entorno
docker run -p 8000:8000 -p 5173:5173 \
  -e GROQ_API_KEY=tu_key \
  -v $(pwd)/data:/app/data \
  parceru:latest
```

### 2. Docker Compose (Más fácil)
```yaml
# docker-compose.yml
version: '3.8'
services:
  parceru:
    build: .
    ports:
      - "8000:8000"
      - "5173:5173"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

```bash
# Ejecutar con compose
docker-compose up -d

# Ver logs
docker-compose logs -f
```

## Producción - Opción 2: Servicios Cloud

### Railway (Backend FastAPI)
```bash
# Instalar CLI
npm install -g @railway/cli

# Login y deploy
railway login
railway init
railway add --service backend

# Variables de entorno en Railway dashboard
# GROQ_API_KEY=tu_key
# PORT=8000

railway up
```

### Vercel (Frontend React)
```bash
# Build frontend para producción
cd frontend
npm run build

# Deploy con Vercel CLI
npm install -g vercel
vercel --prod

# O conectar repositorio GitHub en vercel.com
```

### Netlify (Frontend React - Alternativa)
```bash
cd frontend
npm run build

# Drag & drop carpeta dist/ en netlify.com
# O conectar repo GitHub
```

## Producción - Opción 3: VPS Manual

### 1. Servidor Ubuntu/Debian
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip

# Instalar Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Instalar Nginx (opcional - para reverse proxy)
sudo apt install nginx
```

### 2. Deploy Backend
```bash
# Crear usuario de aplicación
sudo useradd -m -s /bin/bash parceru
sudo su - parceru

# Clonar código
git clone https://github.com/tu-usuario/Hackathon-UdeA-Softserve.git
cd Hackathon-UdeA-Softserve

# Python virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Variables de entorno
cp .env.example .env
# Editar .env con keys reales

# Indexar documentos
python run_ingesta.py

# Instalar gunicorn para producción
pip install gunicorn

# Test local
gunicorn backend.main:app --bind 0.0.0.0:8000
```

### 3. Deploy Frontend
```bash
cd frontend
npm install
npm run build

# Copiar dist/ a directorio web
sudo cp -r dist/* /var/www/html/
```

### 4. Configurar Nginx
```nginx
# /etc/nginx/sites-available/parceru
server {
    listen 80;
    server_name tu-dominio.com;

    # Frontend React
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/parceru /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### 5. Systemd Service (Auto-start)
```ini
# /etc/systemd/system/parceru.service
[Unit]
Description=PARCERU Copiloto Administrativo
After=network.target

[Service]
Type=exec
User=parceru
WorkingDirectory=/home/parceru/Hackathon-UdeA-Softserve
Environment=PATH=/home/parceru/Hackathon-UdeA-Softserve/venv/bin
ExecStart=/home/parceru/Hackathon-UdeA-Softserve/venv/bin/gunicorn backend.main:app --bind 0.0.0.0:8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Habilitar servicio
sudo systemctl enable parceru
sudo systemctl start parceru
sudo systemctl status parceru
```

## Monitoreo y Logs

### Logs de Desarrollo
```bash
# Backend logs (local)
tail -f logs/app.log

# Frontend logs
# Ver consola del navegador (F12)

# Docker logs
docker-compose logs -f
```

### Logs de Producción
```bash
# Systemd service logs
journalctl -u parceru -f

# Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Application logs
tail -f /home/parceru/Hackathon-UdeA-Softserve/logs/app.log
```

### Métricas Básicas
```bash
# Uso de recursos
htop
df -h
free -h

# Conexiones de red
netstat -tulpn | grep :8000
netstat -tulpn | grep :80
```

## Troubleshooting Común

### Backend no inicia
```bash
# Verificar dependencias
pip list | grep langgraph
pip list | grep fastapi

# Verificar variables de entorno
env | grep GROQ

# Test directo
python -c "from backend.main import app; print('Import OK')"
```

### Frontend no conecta con backend
```bash
# Verificar CORS en backend/main.py
# Verificar URL en frontend (axios baseURL)

# Test conectividad
curl http://localhost:8000/api/health
```

### ChromaDB errors
```bash
# Recrear base vectorial
rm -rf data/chroma_db
python run_ingesta.py
```

### Performance lenta
```bash
# Verificar documentos indexados
ls -la data/chroma_db/
du -sh data/chroma_db/

# Verificar memoria
free -h
```

## SSL/HTTPS (Producción)

### Con Certbot (Let's Encrypt)
```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Generar certificado
sudo certbot --nginx -d tu-dominio.com

# Auto-renovación
sudo crontab -e
# Agregar: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Configuración Nginx HTTPS
```nginx
server {
    listen 443 ssl http2;
    server_name tu-dominio.com;
    
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
    
    # Resto de configuración igual...
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name tu-dominio.com;
    return 301 https://$server_name$request_uri;
}
```

## Backup y Recuperación

### Backup Automático
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/parceru_$DATE"

mkdir -p $BACKUP_DIR

# Backup código
tar -czf $BACKUP_DIR/codigo.tar.gz /home/parceru/Hackathon-UdeA-Softserve

# Backup base de datos vectorial
cp -r /home/parceru/Hackathon-UdeA-Softserve/data/chroma_db $BACKUP_DIR/

# Backup configuración
cp /home/parceru/Hackathon-UdeA-Softserve/.env $BACKUP_DIR/

echo "Backup completado en $BACKUP_DIR"
```

```bash
# Programar backup diario
crontab -e
# 0 2 * * * /path/to/backup.sh
```

---

¡Con estas instrucciones tienes todo lo necesario para desplegar PARCERU en cualquier entorno!