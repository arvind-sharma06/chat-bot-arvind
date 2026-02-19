from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .chat_service import ChatService
from .config import config
from .ingestion import DocxIngestor
from .models import ChatRequest, ChatResponse, ReindexPayload, SettingsPayload
from .settings_store import SessionStore, SettingsStore
from .vector_store import VectorStore, list_docx_files


app = FastAPI(title="Arvind's Bot API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config.uploads_dir.mkdir(parents=True, exist_ok=True)
settings_store = SettingsStore()
session_store = SessionStore()
vector_store = VectorStore()
chat_service = ChatService(session_store)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "kb_chunks": vector_store.count()}


@app.get("/api/settings")
def get_settings() -> dict:
    s = settings_store.load()
    s["has_api_key"] = bool(s.get("anthropic_api_key") or config.anthropic_api_key)
    s["anthropic_api_key"] = ""
    return s


@app.post("/api/settings")
def update_settings(payload: SettingsPayload) -> dict:
    current = settings_store.load()
    current.update(payload.model_dump(exclude_none=True))
    settings_store.save(current)
    safe = dict(current)
    safe["has_api_key"] = bool(current.get("anthropic_api_key") or config.anthropic_api_key)
    safe["anthropic_api_key"] = ""
    return safe


@app.post("/api/kb/upload")
async def upload_kb(files: list[UploadFile] = File(...)) -> dict:
    saved = []
    for file in files:
        if not file.filename.lower().endswith(".docx"):
            continue
        target = config.uploads_dir / file.filename
        with target.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        saved.append(str(target))
    return {"uploaded": saved}


@app.post("/api/kb/reindex")
def reindex(payload: ReindexPayload) -> dict:
    settings = settings_store.load()
    api_key = settings.get("anthropic_api_key") or config.anthropic_api_key
    paths = payload.source_paths or []
    paths.append(str(config.uploads_dir))
    files = list_docx_files(paths)
    if not files:
        raise HTTPException(status_code=400, detail="No .docx files found for indexing.")

    ingestor = DocxIngestor(
        api_key=api_key,
        model_name=settings.get("model_name", config.model_name),
        use_image_understanding=bool(settings.get("enable_image_understanding", False)),
    )

    vector_store.clear()
    total = 0
    for f in files:
        chunks = ingestor.parse_docx(f)
        total += vector_store.upsert_chunks(chunks)

    return {
        "indexed_files": [str(f) for f in files],
        "chunks": total,
        "collection_count": vector_store.count(),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    settings = settings_store.load()
    api_key = settings.get("anthropic_api_key") or config.anthropic_api_key
    # Build retrieval query with recent user turns so follow-up questions
    # can resolve references like "that step" or "next one".
    history = session_store.get_history(payload.session_id)
    prior_user_msgs = [m["content"] for m in history if m.get("role") == "user"][-3:]
    retrieval_query = " ".join(prior_user_msgs + [payload.message]).strip()
    retrieval = vector_store.search(retrieval_query, top_k=int(settings.get("top_k", config.top_k)))

    docs = retrieval.get("documents", [[]])[0]
    distances = retrieval.get("distances", [[]])[0]
    threshold = float(settings.get("similarity_threshold", config.similarity_threshold))

    filtered_docs: list[str] = []
    for doc, dist in zip(docs, distances):
        if dist is None:
            continue
        if float(dist) <= threshold:
            filtered_docs.append(doc)

    # If strict filtering removes everything, fall back to top matches so the
    # assistant can still respond from KB instead of always hard-failing.
    if not filtered_docs and docs:
        filtered_docs = docs[: min(2, len(docs))]

    answer, escalated = chat_service.build_response(
        session_id=payload.session_id,
        user_message=payload.message,
        retrieved_docs=filtered_docs,
        settings=settings,
        api_key=api_key,
    )

    return ChatResponse(answer=answer, used_context=filtered_docs, escalated=escalated)


frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
