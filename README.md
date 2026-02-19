# Arvind's Bot (RAG Chatbot)

A FastAPI + Chroma RAG chatbot for B2B onboarding/integration support.

## Features
- Conversational support assistant UI: **Arvind's Bot**
- Vector DB with persistent Chroma storage
- `.docx` knowledge-base ingestion (paragraphs, tables, embedded images)
- Optional image understanding during indexing via Anthropic vision
- Strict retrieval policy: answer only from KB context
- Fallback: asks user to connect with company representative when KB is insufficient
- Critical issue escalation (HIGH PRIORITY)
- Editable prompt/settings and KB upload/reindex directly from UI
- Context window using rolling chat history

## Setup
1. Create venv and install dependencies:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure env:
```bash
cp .env.example .env
# set ANTHROPIC_API_KEY
```

3. Run the app:
```bash
python run.py
```

4. Open:
- [http://localhost:8000](http://localhost:8000)

## Index your initial KB
From the UI, click **Rebuild Vector DB** and add paths in "Extra source paths", for example:
- `/Users/sanskar/Downloads/Compliance Handbook (1).docx`
- `/Users/sanskar/Downloads/SE_SAFETY DOC.docx`
- `/Users/sanskar/Downloads/Security Alert Configuration Guide (1).docx`
- `/Users/sanskar/Downloads/Security Dashboard (1) (1).docx`

Or call the API:
```bash
curl -X POST http://localhost:8000/api/kb/reindex \
  -H "Content-Type: application/json" \
  -d '{"source_paths":["/Users/sanskar/Downloads/Compliance Handbook (1).docx","/Users/sanskar/Downloads/SE_SAFETY DOC.docx","/Users/sanskar/Downloads/Security Alert Configuration Guide (1).docx","/Users/sanskar/Downloads/Security Dashboard (1) (1).docx"]}'
```

## Notes
- Keep API keys out of code and rotate exposed keys.
- `data/chroma` stores the vector DB.
- `data/uploads` stores uploaded KB files.
- Settings/prompt are stored in `data/settings.json`.

## Cloud Hosting
### Option 1: Render (configured)
This repo includes `render.yaml` and `backend/Dockerfile`.

Steps:
1. Push this repo to GitHub.
2. In Render, create a new Blueprint and select this repo.
3. Render will detect `render.yaml` and provision service `arvinds-bot`.
4. Set `ANTHROPIC_API_KEY` in Render environment variables.
5. Deploy.

Important:
- Persistent disk is mounted at `/data` (vector DB + uploads + settings survive restarts).
- Health check: `/api/health`.

### Option 2: Railway
1. Create a new project from this repo.
2. Set root to `backend` Dockerfile path `backend/Dockerfile`.
3. Add env vars:
   - `ANTHROPIC_API_KEY`
   - `MODEL_NAME=claude-haiku-4-5-20251001`
   - `DATA_DIR=/data`
   - `UPLOADS_DIR=/data/uploads`
   - `CHROMA_DIR=/data/chroma`
   - `SIMILARITY_THRESHOLD=1.15`
4. Attach a persistent volume mounted at `/data`.
5. Deploy.
