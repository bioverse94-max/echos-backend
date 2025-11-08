# Echoes Backend - Setup Guide

Complete guide for setting up the Echoes backend with LLM-powered etymology.

## Project Structure(v1.1)

```
echoes-backend/
├── .env                      # Your environment variables (create this!)
├── .env.example              # Template for .env
├── .gitignore               # Git ignore file
├── requirements.txt          # Python dependencies
├── README.md                # Project documentation
├── SETUP.md                 # This file
│
├── api/
│   ├── __init__.py          # Package initializer
│   ├── config.py            # Configuration management
│   ├── main.py              # FastAPI application
│   ├── models.py            # Pydantic models
│   ├── utils.py             # Utility functions
│   └── etymology_service.py # LLM/API etymology service
│
├── scripts/
│   └── build_embeddings.py  # Embedding generation script
│
├── demo_query.py            # Original demo
├── demo_llm_query.py        # LLM demo script
│
├── data/                    # CSV fallback files
├── embeddings/              # Generated embeddings
├── assets/                  # Static assets
└── logs/                    # Log files (auto-created)
```

## Installation Steps

### 1. Clone and Setup Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.venv\Scripts\activate.bat

# Activate (Mac/Linux)
source .venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel
```

### 2. Install Dependencies

```bash
# Install PyTorch CPU version first
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.3.1+cpu

# Install all other requirements
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your preferred editor
```

**Choose ONE LLM provider and add your API key:**

#### Option A: OpenAI (GPT)
```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini
USE_LLM_ETYMOLOGY=true
```

#### Option B: DeepSeek (Cost-effective)
```bash
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_MODEL=deepseek-chat
USE_LLM_ETYMOLOGY=true
```

#### Option C: Google Gemini (Free tier available)
```bash
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-1.5-flash
USE_LLM_ETYMOLOGY=true
```

#### Option D: Anthropic Claude
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
USE_LLM_ETYMOLOGY=true
```

### 4. Create Required Files

Create `api/__init__.py`:
```python
from .config import settings
__version__ = "1.0.0"
```

Create `.gitignore`:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Data (optional - keep embeddings out of git if large)
embeddings/
*.json

# OS
.DS_Store
Thumbs.db
```

## Usage

### Start the Server

```bash
uvicorn api.main:app --reload --port 8000
```

The server will be available at `http://localhost:8000`

### API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

### Run Demo Script

```bash
# Test LLM-powered etymology generation
python demo_llm_query.py
```

## API Endpoints

### 1. Generate Evolution Data (NEW!)

```bash
POST /generate-evolution
{
  "word": "science",
  "eras": ["1900s", "1950s", "2020s"],
  "num_examples": 5
}
```

This uses your configured LLM to generate contextual examples showing how the word evolved.

### 2. Build Complete Embeddings (NEW!)

```bash
POST /build-embeddings
{
  "word": "freedom",
  "eras": ["1900s", "2020s"],
  "num_examples": 5
}
```

This generates evolution data AND creates embedding files in one step.

### 3. Get Timeline

```bash
GET /timeline?concept=freedom&top_n=6
```

### 4. Get Era-Specific Data

```bash
GET /era?concept=freedom&era=1900s&top_n=10
```

### 5. Generate Embedding

```bash
POST /embed
{
  "text": "Your text here"
}
```

## Example Workflow

### Using LLM to Generate New Concept Data

1. **Start the server:**
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

2. **Generate evolution data for "science":**
   ```bash
   curl -X POST "http://localhost:8000/build-embeddings" \
     -H "Content-Type: application/json" \
     -d '{
       "word": "science",
       "eras": ["1900s", "1950s", "2020s"],
       "num_examples": 5
     }'
   ```

3. **View the timeline:**
   ```bash
   curl "http://localhost:8000/timeline?concept=science&top_n=5"
   ```

## Troubleshooting

### No LLM Provider Configured

**Error:** `"llm_provider": null` in health check

**Solution:** Add an API key to your `.env` file:
```bash
OPENAI_API_KEY=sk-your-key-here
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'openai'`

**Solution:** Install the LLM provider packages:
```bash
# For OpenAI/DeepSeek
pip install openai

# For Gemini
pip install google-generativeai

# For Claude
pip install anthropic
```

### PyTorch Installation Issues

See the main README.md for detailed PyTorch troubleshooting.

### Concept Not Found

**Error:** `404: Concept 'xyz' not found`

**Solution:** You need to generate embeddings first:
```bash
curl -X POST "http://localhost:8000/build-embeddings" \
  -H "Content-Type: application/json" \
  -d '{"word": "xyz", "eras": ["1900s", "2020s"], "num_examples": 5}'
```

## Cost Considerations

### LLM API Costs (approximate)

- **DeepSeek:** ~$0.001 per concept (CHEAPEST)
- **OpenAI GPT-4o-mini:** ~$0.01 per concept
- **Gemini Flash:** Free tier available, then ~$0.002 per concept
- **Claude Sonnet:** ~$0.03 per concept

### Recommendations

- **For development/testing:** Use **DeepSeek** or **Gemini** (free tier)
- **For production:** Consider your quality vs. cost needs
- **For offline:** Use CSV fallback files

## Production Deployment

1. **Set proper CORS origins:**
   ```bash
   ALLOWED_ORIGINS=https://yourdomain.com
   ```

2. **Disable reload:**
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

3. **Use a reverse proxy (Nginx/Caddy)**

4. **Enable rate limiting:**
   ```bash
   RATE_LIMIT_ENABLED=true
   RATE_LIMIT_PER_MINUTE=60
   ```

5. **Set up logging:**
   ```bash
   LOG_LEVEL=WARNING
   LOG_FILE=/var/log/echoes/app.log
   ```

## Next Steps

1. Explore the Swagger docs at `http://localhost:8000/docs`
2. Try generating evolution data for different words
3. Build a frontend to visualize the timelines
4. Add more eras for richer historical analysis
5. Customize the LLM prompts in `etymology_service.py`

## Support

For issues or questions:
- Check the logs in `logs/echoes.log`
- Review the FastAPI docs at `/docs`
- Ensure your API keys are valid
- Check that required directories exist

## License

[Your License Here]