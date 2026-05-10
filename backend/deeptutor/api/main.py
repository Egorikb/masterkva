import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from deeptutor.logging import get_logger
from deeptutor.services.path_service import get_path_service

# Note: Don't set service_prefix here - start_web.py already adds [Backend] prefix
logger = get_logger("API")


class _SuppressWsNoise(logging.Filter):
    """Suppress noisy uvicorn logs for WebSocket connection churn."""

    _SUPPRESSED = ("connection open", "connection closed")

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(f in msg for f in self._SUPPRESSED)


logging.getLogger("uvicorn.error").addFilter(_SuppressWsNoise())

CONFIG_DRIFT_ERROR_TEMPLATE = (
    "Configuration Drift Detected: Capability tool references {drift} are not "
    "registered in the runtime tool registry. Register the missing tools or "
    "remove the stale tool names from the capability manifests."
)


class SafeOutputStaticFiles(StaticFiles):
    """Static file mount that only exposes explicitly whitelisted artifacts."""

    def __init__(self, *args, path_service, **kwargs):
        super().__init__(*args, **kwargs)
        self._path_service = path_service

    async def get_response(self, path: str, scope):
        if not self._path_service.is_public_output_path(path):
            raise HTTPException(status_code=404, detail="Output not found")
        return await super().get_response(path, scope)


def validate_tool_consistency():
    """
    Validate that capability manifests only reference tools that are actually
    registered in the runtime ``ToolRegistry``.
    """
    try:
        from deeptutor.runtime.registry.capability_registry import get_capability_registry
        from deeptutor.runtime.registry.tool_registry import get_tool_registry

        capability_registry = get_capability_registry()
        tool_registry = get_tool_registry()
        available_tools = set(tool_registry.list_tools())

        referenced_tools = set()
        for manifest in capability_registry.get_manifests():
            referenced_tools.update(manifest.get("tools_used", []) or [])

        drift = referenced_tools - available_tools
        if drift:
            raise RuntimeError(CONFIG_DRIFT_ERROR_TEMPLATE.format(drift=drift))
    except RuntimeError:
        logger.exception("Configuration validation failed")
        raise
    except Exception:
        logger.exception("Failed to load configuration for validation")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management
    Gracefully handle startup and shutdown events, avoid CancelledError
    """
    # Execute on startup
    logger.info("Application startup")

    # Validate configuration consistency
    validate_tool_consistency()

    # Initialize LLM client early so OPENAI_* env vars are available before
    # any downstream provider integrations start.
    try:
        from deeptutor.services.llm import get_llm_client

        llm_client = get_llm_client()
        logger.info(f"LLM client initialized: model={llm_client.config.model}")
    except Exception as e:
        logger.warning(f"Failed to initialize LLM client at startup: {e}")

    try:
        from deeptutor.events.event_bus import get_event_bus

        event_bus = get_event_bus()
        await event_bus.start()
        logger.info("EventBus started")
    except Exception as e:
        logger.warning(f"Failed to start EventBus: {e}")

    try:
        from deeptutor.services.tutorbot import get_tutorbot_manager
        await get_tutorbot_manager().auto_start_bots()
    except Exception as e:
        logger.warning(f"Failed to auto-start TutorBots: {e}")

    yield

    # Execute on shutdown
    logger.info("Application shutdown")

    # Stop TutorBots
    try:
        from deeptutor.services.tutorbot import get_tutorbot_manager
        await get_tutorbot_manager().stop_all()
        logger.info("TutorBots stopped")
    except Exception as e:
        logger.warning(f"Failed to stop TutorBots: {e}")

    # Stop EventBus
    try:
        from deeptutor.events.event_bus import get_event_bus

        event_bus = get_event_bus()
        await event_bus.stop()
        logger.info("EventBus stopped")
    except Exception as e:
        logger.warning(f"Failed to stop EventBus: {e}")


app = FastAPI(
    title="DeepTutor API",
    version="1.0.0",
    lifespan=lifespan,
    # Disable automatic trailing slash redirects to prevent protocol downgrade issues
    # when deployed behind HTTPS reverse proxies (e.g., nginx).
    # Without this, FastAPI's 307 redirects may change HTTPS to HTTP.
    # See: https://github.com/HKUDS/DeepTutor/issues/112
    redirect_slashes=False,
)

# Log only non-200 requests (uvicorn access_log is disabled in run_server.py)
_access_logger = logging.getLogger("uvicorn.access")


@app.middleware("http")
async def selective_access_log(request, call_next):
    response = await call_next(request)
    if response.status_code != 200:
        _access_logger.info(
            '%s - "%s %s" %d',
            request.client.host if request.client else "-",
            request.method,
            request.url.path,
            response.status_code,
        )
    return response


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount a filtered view over user outputs.
# Only whitelisted artifact paths are readable through the static handler.
path_service = get_path_service()
user_dir = path_service.get_public_outputs_root()

# Initialize user directories on startup
try:
    from deeptutor.services.setup import init_user_directories

    init_user_directories()
except Exception:
    # Fallback: just create the main directory if it doesn't exist
    if not user_dir.exists():
        user_dir.mkdir(parents=True)

app.mount(
    "/api/outputs",
    SafeOutputStaticFiles(directory=str(user_dir), path_service=path_service),
    name="outputs",
)

# Import routers only after runtime settings are initialized.
# Some router modules load YAML settings at import time.
from deeptutor.api.routers import (
    agent_config,
    chat,
    co_writer,
    dashboard,
    guide,
    knowledge,
    memory,
    notebook,
    plugins_api,
    question,
    sessions,
    settings,
    solve,
    system,
    tutorbot,
    unified_ws,
    vision_solver,
    question_notebook,
)

# Include routers
app.include_router(solve.router, prefix="/api/v1", tags=["solve"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(question.router, prefix="/api/v1/question", tags=["question"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(co_writer.router, prefix="/api/v1/co_writer", tags=["co_writer"])
app.include_router(notebook.router, prefix="/api/v1/notebook", tags=["notebook"])
app.include_router(guide.router, prefix="/api/v1/guide", tags=["guide"])
app.include_router(memory.router, prefix="/api/v1/memory", tags=["memory"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(question_notebook.router, prefix="/api/v1/question-notebook", tags=["question-notebook"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
app.include_router(plugins_api.router, prefix="/api/v1/plugins", tags=["plugins"])
app.include_router(agent_config.router, prefix="/api/v1/agent-config", tags=["agent-config"])
app.include_router(vision_solver.router, prefix="/api/v1", tags=["vision-solver"])
app.include_router(tutorbot.router, prefix="/api/v1/tutorbot", tags=["tutorbot"])

# Unified WebSocket endpoint
app.include_router(unified_ws.router, prefix="/api/v1", tags=["unified-ws"])


@app.get("/")
async def root():
    return {"message": "Welcome to DeepTutor API"}


if __name__ == "__main__":
    from deeptutor.api.run_server import main as run_server_main

    run_server_main()


# ============ STATS API ============
@app.get("/api/v1/stats/user")
async def get_user_stats():
    """Get user statistics."""
    # Read from chat history
    import sqlite3
    from pathlib import Path
    
    db_path = Path("data/user/chat_history.db")
    if not db_path.exists():
        return {
            "total_sessions": 0,
            "total_messages": 0,
            "total_time_minutes": 0,
            "qi_energy": 45,
            "belt_level": "yellow",
            "correct_answers": 15,
            "total_answers": 22,
            "accuracy_percent": 68,
            "completed_topics": 8,
            "weak_topics": ["Деление на 2 цифры", "Дроби"],
            "strong_topics": ["Сложение", "Вычитание", "Умножение"],
            "weekly_progress": [3, 5, 2, 4, 6, 3, 2],
            "weekly_accuracy": [80, 75, 70, 85, 90, 80, 75],
            "mode_kungfu_sessions": 10,
            "mode_homework_sessions": 8,
            "mode_science_sessions": 4,
        }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total messages
        cursor.execute("SELECT COUNT(*) FROM messages WHERE role = 'user'")
        total_messages = cursor.fetchone()[0] or 0
        
        # Get unique sessions
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM messages")
        total_sessions = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_time_minutes": total_sessions * 15,  # Estimate
            "qi_energy": 45,
            "belt_level": "yellow",
            "correct_answers": 15,
            "total_answers": 22,
            "accuracy_percent": 68,
            "completed_topics": 8,
            "weak_topics": ["Деление", "Дроби"],
            "strong_topics": ["Сложение", "Умножение"],
            "weekly_progress": [3, 5, 2, 4, 6, 3, 2],
            "weekly_accuracy": [80, 75, 70, 85, 90, 80, 75],
            "mode_kungfu_sessions": 10,
            "mode_homework_sessions": 8,
            "mode_science_sessions": 4,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/v1/stats/weekly")


# ============ ADMIN STATS ============
@app.get("/api/v1/admin/stats")
async def get_admin_stats_simple():
    return {
        "total_users": 10,
        "total_messages": 156,
        "total_sessions": 45,
        "return_rate_percent": 72,
        "gpt_tokens_used": 15000,
        "yandex_chars_used": 45000,
        "estimated_cost_rub": 47.0,
        "active_now": 3,
        "last_24h": 12,
        "last_7d": 89,
        "last_30d": 156,
    }


@app.get("/api/v1/admin/costs")
async def get_cost_breakdown():
    return {
        "gpt": {"tokens": 15000, "cost_per_1k": 0.003, "total_rub": 45.0},
        "yandex_tts": {"chars": 45000, "cost_per_1k": 0.04, "total_rub": 1.8},
        "ollama": {"requests": 5000, "cost_per_1k": 0, "total_rub": 0},
        "total_rub": 46.8,
    }

# Audio streaming endpoint
AUDIO_DIR = "/home/egor/ai-agent/workspace/deeptutor_analyzed/audio_storage"

@app.get("/audio_storage/{filename}")
async def get_audio(filename: str):
    """Proxy audio files to avoid CORS issues"""
    audio_path = Path(AUDIO_DIR) / filename
    if audio_path.exists():
        return FileResponse(audio_path, media_type="audio/ogg")
    return {"error": "Audio not found"}
