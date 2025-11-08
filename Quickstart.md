# Echoes Backend - Quickstart Guide

**Optimized for OpenRouter API**

## 🚀 Installation (5 Minutes)

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Mac/Linux)
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install PyTorch CPU (IMPORTANT: Do this first!)
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.3.1+cpu

# Install remaining dependencies
pip install -r requirements.txt
pip install huggingface-hub==0.25.2
```

### 2. Verify Configuration

Your `.env` file is already configured! Just verify:

```bash
# Windows
type .env

# Mac/Linux
cat .env
```

Should show:
```bash
OPENROUTER_API_KEY=sk-or-v1-01ff92a4ec0c5e35c--------------------------------------9acac1
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct
USE_LLM_ETYMOLOGY=true
```

### 3. Start Server

```bash
uvicorn api.main:app --reload --port 8000
```

Expected output:
```
============================================================
Starting Echoes Backend v1.1.0
============================================================
OpenRouter Model: qwen/qwen-2.5-72b-instruct
LLM Etymology: True
Response Caching: True
============================================================
```

### 4. Run Demo

Open a **new terminal**:

```bash
# Activate venv again
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Mac/Linux

# Run demo
python demo_openrouter.py
```

---

## 📚 Quick API Examples

### Health Check

```bash
curl http://localhost:8000/health
```

### Generate Word Evolution

```bash
curl -X POST http://localhost:8000/generate-evolution \
  -H "Content-Type: application/json" \
  -d "{\"word\": \"freedom\", \"eras\": [\"1900s\", \"2020s\"], \"num_examples\": 5}"
```

### Build Complete Embeddings

```bash
curl -X POST http://localhost:8000/build-embeddings \
  -H "Content-Type: application/json" \
  -d "{\"word\": \"freedom\", \"eras\": [\"1900s\", \"2020s\"], \"num_examples\": 5}"
```

### Get Timeline

```bash
curl "http://localhost:8000/timeline?concept=freedom&top_n=5"
```

---

## 🔧 Troubleshooting

### "No module named 'tenacity'"

```bash
pip install tenacity
```

### "Invalid OpenRouter API key"

Check `.env` - key should start with `sk-or-v1-`

### "Request timed out"

Increase timeout in `.env`:
```bash
LLM_TIMEOUT=120
```

### PyTorch Won't Install

```bash
# Force CPU wheel
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.3.1+cpu
```

### Server Won't Start

Check logs:
```bash
# Windows
type logs\echoes.log

# Mac/Linux
cat logs/echoes.log
```

Common fixes:
- Port in use: Change `PORT=8001` in `.env`
- Invalid API key: Check `.env`
- Missing packages: Run `pip install -r requirements.txt`

---

## 💰 Cost Estimation

Using `qwen/qwen-2.5-72b-instruct`:

| Operation | Cost |
|-----------|------|
| Generate evolution (3 eras) | $0.0003 |
| Build embeddings (3 eras) | $0.0003 |
| **Total per concept** | **$0.0006** |

With caching: **Repeated queries = $0**

---

## 🎨 Next Steps

1. **Explore API Docs**: http://localhost:8000/docs
2. **Try Different Words**: "democracy", "technology", "love"
3. **More Eras**: Add "1950s", "1980s" for richer analysis
4. **Build Frontend**: Use `/timeline` endpoint to visualize
5. **Customize Prompts**: Edit `etymology_service.py`

---

## 📖 Documentation

- API Docs: http://localhost:8000/docs
- OpenRouter Models: https://openrouter.ai/models
- OpenRouter Dashboard: https://openrouter.ai/activity

---

**Happy coding! 🚀**