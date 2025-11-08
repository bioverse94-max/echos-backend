# Echoes Backend - Semantic Evolution Tracker

> Track how words and concepts evolved across time using AI-powered semantic analysis

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://www.python.org/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-LLM-orange)](https://openrouter.ai/)

## 🌟 Features

- **AI-Powered Etymology**: Generate historical word usage examples using LLMs
- **Semantic Analysis**: Track meaning shifts across time periods
- **Vector Embeddings**: Advanced similarity search using sentence transformers
- **REST API**: Clean, documented endpoints for easy integration
- **Timeline Visualization**: See how concepts evolved over decades
- **Caching**: Built-in response caching for performance

---

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Running as a Server](#running-as-a-server)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd echoes-backend
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Mac/Linux

# 2. Install dependencies
pip install --upgrade pip setuptools wheel
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.3.1+cpu
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OpenRouter API key

# 4. Start server
uvicorn api.main:app --reload --port 8000

# 5. Test it
curl http://localhost:8000/health
```

Visit http://localhost:8000/docs for interactive API documentation.

---

## 💻 Installation

### Prerequisites

- **Python 3.10-3.12**
- **4GB+ RAM** (for sentence transformers)
- **Internet connection** (for model downloads)
- **OpenRouter API key** ([Get one here](https://openrouter.ai/keys))

### Step-by-Step Installation

#### 1. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\Activate.ps1

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

#### 2. Upgrade Build Tools

```bash
python -m pip install --upgrade pip setuptools wheel
```

#### 3. Install PyTorch (CPU Version)

```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.3.1+cpu
```

> **Note**: CPU-only version is sufficient and much smaller than GPU version

#### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 5. Verify Installation

```bash
python -c "import torch, fastapi, sentence_transformers; print('✅ All packages installed')"
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Required: OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-v1-YOUR_API_KEY_HERE
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct

# Optional: Server Configuration
PORT=8000
HOST=0.0.0.0
ALLOWED_ORIGINS=*

# Optional: LLM Settings
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=60

# Optional: Features
USE_LLM_ETYMOLOGY=true
CACHE_LLM_RESPONSES=true
LOG_LEVEL=INFO
```

### Getting an OpenRouter API Key

1. Go to https://openrouter.ai/keys
2. Sign up or log in
3. Click "Create Key"
4. **Add credits to your account** (required for API usage)
5. Copy your key (starts with `sk-or-v1-`)

### Recommended Models

| Model | Cost/Million Tokens | Quality | Speed |
|-------|-------------------|---------|-------|
| `qwen/qwen-2.5-72b-instruct` | $0.50 | ⭐⭐⭐⭐ | Fast |
| `deepseek/deepseek-chat` | $0.10 | ⭐⭐⭐ | Fastest |
| `anthropic/claude-3.5-sonnet` | $3.00 | ⭐⭐⭐⭐⭐ | Slower |

---

## 📚 API Documentation

### Core Endpoints

#### Health Check
```bash
GET /health
```

Returns server status and configuration.

#### Generate Word Evolution
```bash
POST /generate-evolution
Content-Type: application/json

{
  "word": "freedom",
  "eras": ["1900s", "1950s", "2020s"],
  "num_examples": 5
}
```

Generates contextual examples showing how a word's meaning evolved.

#### Build Complete Embeddings
```bash
POST /build-embeddings
Content-Type: application/json

{
  "word": "privacy",
  "eras": ["1900s", "2020s"],
  "num_examples": 5
}
```

Complete pipeline: generates evolution data + creates embeddings + saves to disk.

#### Get Timeline
```bash
GET /timeline?concept=freedom&top_n=6
```

Returns timeline with semantic shifts and top matching examples per era.

#### Get Era-Specific Data
```bash
GET /era?concept=freedom&era=1900s&top_n=10
```

Returns top similar items for a specific time period.

### Full API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI with:
- Try-it-out functionality
- Request/response schemas
- Example payloads

---

## 🌐 Running as a Server

### Local Network Access

To allow other devices on your network to access the server:

#### 1. Find Your Local IP

**Windows:**
```bash
ipconfig
# Look for "IPv4 Address" under your active network adapter
# Example: 192.168.1.100
```

**Mac/Linux:**
```bash
ifconfig | grep "inet "
# or
ip addr show
# Example: 192.168.1.100
```

#### 2. Start Server with Host Binding

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

#### 3. Access from Other Devices

Other devices on your network can now access:
```
http://192.168.1.100:8000/docs
```

#### 4. Configure Firewall

**Windows Firewall:**
```powershell
netsh advfirewall firewall add rule name="Echoes Backend" dir=in action=allow protocol=TCP localport=8000
```

**Linux (ufw):**
```bash
sudo ufw allow 8000/tcp
```

**Mac:**
System Preferences → Security & Privacy → Firewall → Firewall Options → Add port 8000

---

## 🏗️ Production Deployment

### Option 1: Standalone Server (Simple)

```bash
# Install production-grade ASGI server
pip install gunicorn

# Run with multiple workers
gunicorn api.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --log-level info
```

### Option 2: Behind Nginx (Recommended)

#### Install Nginx

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install nginx
```

#### Configure Nginx

Create `/etc/nginx/sites-available/echoes`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # or your server IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for LLM requests
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }
}
```

#### Enable and Start

```bash
sudo ln -s /etc/nginx/sites-available/echoes /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Option 3: With SSL (HTTPS)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renew
sudo certbot renew --dry-run
```

### Option 4: As a Systemd Service

Create `/etc/systemd/system/echoes.service`:

```ini
[Unit]
Description=Echoes Backend API
After=network.target

[Service]
Type=notify
User=your-username
WorkingDirectory=/path/to/echoes-backend
Environment="PATH=/path/to/.venv/bin"
ExecStart=/path/to/.venv/bin/gunicorn api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable echoes
sudo systemctl start echoes
sudo systemctl status echoes
```

### Option 5: Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t echoes-backend .
docker run -d -p 8000:8000 --env-file .env echoes-backend
```

---

## 🛠️ Development

### Project Structure

```
echoes-backend/
├── api/
│   ├── __init__.py          # Package initializer
│   ├── config.py            # Settings & environment
│   ├── main.py              # FastAPI app
│   ├── models.py            # Pydantic models
│   ├── utils.py             # Helper functions
│   └── etymology_service.py # LLM integration
├── scripts/
│   └── build_embeddings.py  # CLI embedding generator
├── data/                    # Sample CSV files
├── embeddings/              # Generated embeddings (gitignored)
├── logs/                    # Application logs (gitignored)
├── .env                     # Your config (gitignored)
├── .env.example             # Template
├── .gitignore              # Git ignore rules
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-cov httpx

# Run tests
pytest

# With coverage
pytest --cov=api --cov-report=html
```

### Hot Reload

For development with auto-reload on file changes:

```bash
uvicorn api.main:app --reload --port 8000
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "User not found" (401 Error)

**Problem**: Invalid API key or no credits

**Solution**:
- Check your OpenRouter API key format
- Verify you have credits: https://openrouter.ai/credits
- Try generating a new API key

#### 2. PyTorch Won't Install

**Problem**: Binary wheel not available

**Solution**:
```bash
# Force CPU wheel
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.3.1+cpu

# If that fails, try a different version
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.2.0+cpu
```

#### 3. Port Already in Use

**Problem**: Another service using port 8000

**Solution**:
```bash
# Use different port
uvicorn api.main:app --port 8001

# Or find and kill process (Windows)
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or find and kill process (Linux/Mac)
lsof -ti:8000 | xargs kill -9
```

#### 4. Module Import Errors

**Problem**: Missing dependencies

**Solution**:
```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

#### 5. Slow First Request

**Problem**: Model loading on first use

**Solution**: This is normal. First request loads the sentence transformer (~80MB). Subsequent requests are fast.

#### 6. Timeout Errors

**Problem**: LLM requests taking too long

**Solution**: Increase timeout in `.env`:
```bash
LLM_TIMEOUT=120
```

### Debug Mode

Enable detailed logging:

```bash
# In .env
LOG_LEVEL=DEBUG

# Or via command line
uvicorn api.main:app --log-level debug
```

Check logs:
```bash
tail -f logs/echoes.log
```

---

## 💰 Cost Estimation

Using `qwen/qwen-2.5-72b-instruct`:

| Operation | API Calls | Cost |
|-----------|-----------|------|
| Generate evolution (3 eras, 5 examples) | 1 | $0.0003 |
| Build embeddings (3 eras) | 1 | $0.0003 |
| **Total per concept** | | **$0.0006** |

With caching enabled: **Repeated queries = $0**

### Cost Optimization Tips

1. **Enable caching**: Set `CACHE_LLM_RESPONSES=true`
2. **Use cheaper models**: Try `deepseek/deepseek-chat`
3. **Reduce examples**: Set `num_examples=3` instead of 5
4. **Batch processing**: Generate multiple concepts in one session
5. **Pre-generate**: Create embeddings for common words ahead of time

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/beastknight933/echoes-backend.git
cd echoes-backend

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

---

## 📄 License

[Your License Here - e.g., MIT]

---

## 🙏 Acknowledgments

- **OpenRouter** for LLM API access
- **Sentence Transformers** for embeddings
- **FastAPI** for the excellent web framework
- **Hugging Face** for model hosting

---

## 📞 Support

- **Issues**: https://github.com/beastknight933/echoes-backend/issues
- **Email**: gaumickhazra@gmail.com
- **OpenRouter Help**: https://openrouter.ai/docs

---

## 🗺️ Roadmap

- [ ] Add authentication/API keys
- [ ] Support for more LLM providers (OpenAI, Anthropic direct)
- [ ] Batch processing endpoint
- [ ] WebSocket support for streaming responses
- [ ] Admin dashboard
- [ ] Rate limiting
- [ ] Redis caching
- [ ] Multi-language support

---

**Built with ❤️ for exploring the evolution of language**