"""
Plugins API Router
==================

Lists registered tools, capabilities, and playground plugins.
Provides direct tool execution for the Playground tester.
"""

import asyncio
import contextlib
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from deeptutor.runtime.registry.capability_registry import get_capability_registry
from deeptutor.runtime.registry.tool_registry import get_tool_registry
from deeptutor.logging import ConsoleFormatter

logger = logging.getLogger(__name__)

# Load diagnostic pool (for Phase 1)
DIAGNOSTIC_POOL_FILE = Path(__file__).parent.parent.parent.parent / "data" / "diagnostic_pool.json"
diagnostic_pool = {}
if DIAGNOSTIC_POOL_FILE.exists():
    with open(DIAGNOSTIC_POOL_FILE) as f:
        diagnostic_pool = json.load(f)
    logger.info(f"Загружено вопросов для диагностики: {len(diagnostic_pool.get('questions', []))}")
else:
    logger.warning(f"Diagnostic pool not found: {DIAGNOSTIC_POOL_FILE}")
# Load from chinese_math.json
# Topic to class mapping
TOPIC_KEYWORDS = {
    "дроби": 5, "дробь": 5,
    "сложение": 2, "плюс": 2,
    "вычитание": 1, "минус": 1,
    "умножение": 3, "умножить": 3,
    "деление": 3, "делить": 3,
    "отрицательные": 6, "минус": 6,
    "уравнения": 7, "уравнение": 7,
    "неравенства": 9, "неравенство": 9,
    "счёт": 1,
    "многозначные": 4,
}

def find_topic_class(text: str) -> int:
    """Find what class a topic starts from user input like 'не понимаю дроби'"""
    text = text.lower()
    for keyword, grade in TOPIC_KEYWORDS.items():
        if keyword in text:
            return grade
    return 0  # Unknown


def _build_visual_tag(grade: int, topic: str = "default", for_explanation: bool = False) -> str:
    """
    Строим [VISUAL] тег для интерактивной доски.
    
    ЛОГИКА:
    1. for_explanation=True → CPA-компонент (BarModel, TenFrame)
    2. for_explanation=False → страница учебника (fallback)
    
    CPA-компоненты соответствуют китайской методике:
    - TenFrame: 10-клетьтая рамка для счёта до 10
    - BarModel: столбчатая диаграмма для сравнения
    - NumberBond: связки чисел (состав числа)
    """
    page_map = {
        "addition": "042",
        "subtraction": "052",
        "multiplication": "096",
        "division": "097",
        "geometry": "034",
        "numbers": "019",
        "cpa": "042",
        "default": "042",
    }
    page = page_map.get(topic, page_map["default"])
    display_grade = min(grade, 6) if grade > 0 else 1
    
    # CPA-компонент = приоритет!
    if for_explanation:
        # CPA данные для визуализации
        if topic in ["addition", "default", "cpa"]:
            # TenFrame для сложения
            label = "7 + ? = 10"
            fallback = "/images/textbook/page22.png"
            cpa_data = {
                "type": "cpa_component",
                "component": "TenFrame",
                "data": {"filled": 7, "total": 10, "label": label},
                "fallback_image": fallback
            }
        elif topic == "subtraction":
            # BarModel для вычитания
            fallback = "/images/textbook/page22.png"
            cpa_data = {
                "type": "cpa_component",
                "component": "BarModel",
                "data": {"segments": [{"value": 5, "label": "Было", "color": "#4ade80"}, {"value": 3, "label": "Съели", "color": "#f87171"}]},
                "fallback_image": fallback
            }
        elif topic == "multiplication":
            # NumberBond для умножения
            fallback = "/images/textbook/page22.png"
            cpa_data = {
                "type": "cpa_component",
                "component": "NumberBond",
                "data": {"total": 6, "parts": [2, 4]},
                "fallback_image": fallback
            }
        else:
            fallback = "/images/textbook/page22.png"
            cpa_data = {
                "type": "cpa_component",
                "component": "TenFrame",
                "data": {"filled": 5, "total": 10},
                "fallback_image": fallback
            }
        
        import json
        return f'\n\n[VISUAL]{json.dumps(cpa_data)}[/VISUAL]'
    
    # Fallback = страница учебника
    return f'\n\n[VISUAL]{{"type": "textbook_page", "grade": {display_grade}, "page": "{page}"}}[/VISUAL]'

def load_chinese_math():
    import json
    import os
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "chinese_math.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

CHINESE_MATH = load_chinese_math()

DIAGNOSTIC_BY_GRADE = {}
for grade_str, topics in CHINESE_MATH.items():
    grade = int(grade_str)
    for topic, questions in topics.items():
        DIAGNOSTIC_BY_GRADE[grade] = {topic: questions}

def get_diagnostic_question(user_id: str, question_num: int = 1, grade: int = None) -> dict:
    """Get diagnostic question from pool filtered by student grade."""
    if diagnostic_pool.get("questions"):
        all_questions = diagnostic_pool["questions"]
        
        # Filter by grade if available, otherwise use all
        if grade and grade > 0:
            filtered = [q for q in all_questions if q.get("grade") == grade]
            if filtered:
                questions = filtered
            else:
                questions = all_questions
        else:
            questions = all_questions
        
        # Sort by difficulty (easiest first)
        questions = sorted(questions, key=lambda x: x.get("difficulty", 1))
        
        idx = (question_num - 1) % len(questions)
        q = questions[idx]
        return {
            "id": q.get("id"),
            "topic_id": q.get("topic_id"),
            "question": q["question"],
            "answer": q["answer"],
            "alternatives": q.get("alternatives", []),
            "topic": q["topic"],
            "level": q.get("difficulty", 1),
            "grade": q.get("grade", grade or 1),
            "CPA": q.get("CPA", {}),
            "practice_ref": q.get("practice_ref"),
        }
    
    return {"question": "Сколько будет 2 + 2?", "answer": "4", "topic": "addition", "level": 1, "grade": grade or 1}

# === PHASE 3: CPA CYCLE FUNCTIONS ===
def get_cpa_hint(cpa_level: int, topic: str) -> tuple[str, str]:
    """Get hint and visual based on CPA level (Concrete->Pictorial->Abstract)"""
    if cpa_level >= 2:
        # Concrete: objects explanation
        hints = {
            "addition": ("Возьми 5 яблок, добавь ещё 3. Сколько всего? 🍎🍎🍎🍎🍎 + 🍎🍎🍎", "textbook"),
            "subtraction": ("Было 8 конфет. Съели 3. Сколько осталось? 🍬🍬🍬🍬🍬🍬🍬🍬 - 🍬🍬🍬", "textbook"),
            "multiplication": ("По 2 яблока 3 раза. Это 2 × 3 = ? 🍎🍎 | 🍎🍎 | 🍎🍎", "textbook"),
        }
        return hints.get(topic, ("Возьми палочки и посчитай! 🥋", "textbook"))
    elif cpa_level >= 1:
        # Pictorial: visual models  
        visual_map = {
            "addition": "ten_frame",
            "subtraction": "bar_model", 
            "multiplication": "number_bond",
        }
        return ("Мастер видит, что нам нужно посмотреть иначе! Давай на доске! 📊", visual_map.get(topic, "ten_frame"))
    else:
        # Abstract: just numbers
        return ("Попробуй ещё раз. Можешь посчитать на пальцах! 🖐️", None)

def get_cpa_visual(topic: str) -> dict:
    """Get visual data for CPA level"""
    visuals = {
        "ten_frame": {"type": "cpa_component", "component": "TenFrame", "data": {"filled": 7, "total": 10, "label": "7 + ? = 10"}, "fallback_image": "/images/textbook/page22.png"},
        "bar_model": {"type": "cpa_component", "component": "BarModel", "data": {"segments": [{"value": 5, "label": "Было", "color": "#4ade80"}, {"value": 3, "label": "Съели", "color": "#f87171"}]}, "fallback_image": "/images/textbook/page22.png"},
        "number_bond": {"type": "cpa_component", "component": "NumberBond", "data": {"total": 6, "parts": [2, 4]}, "fallback_image": "/images/textbook/page22.png"},
    }
    return visuals.get(topic, visuals["ten_frame"])

    state = get_user_state(user_id)
    level = state.get("diagnostic_progress", {}).get("current_diag_level", 1)
    if level not in DIAGNOSTIC_BY_GRADE:
        level = 1
    topics = DIAGNOSTIC_BY_GRADE.get(level, DIAGNOSTIC_BY_GRADE[1])
    # Always use the first topic for this level
    topic = list(topics.keys())[0]
    # Get questions for first topic
    if isinstance(topics[topic], list):
        questions = topics[topic]
    else:
        questions = list(topics[topic].values())[0]
    idx = (question_num - 1) % len(questions)
    q, a = questions[idx]
    return {"question": f"Сколько будет {q}?", "answer": a, "topic": topic, "level": level, "grade": level}

def generate_parent_report(user_id: str, state: dict, event: str = "session_end") -> str:
    """Generate Parent Report JSON (Phase 1 - Business)"""
    diag = state.get("diagnostic_progress", {})
    strong = diag.get("strong_topics", [])
    weak = diag.get("weak_topics", [])
    level = state.get("grade", 1)
    # Determine recommendation based on weak spots
    recommendation = ""
    if weak:
        recommendation = f"Потренируйте тему '{weak[0]}' дома с помощью палочек или счётных палочек."
    else:
        recommendation = f"Отлично! Продолжайте практиковать текущую тему."
    
    report = {
        "student_name": state.get("name", "Ученик"),
        "grade": level,
        "event": event,
        "strong_topics": strong[:3] if strong else ["счёт до 10"],
        "weak_spots": weak[:3] if weak else [],
        "current_level": level,
        "session_goal": event,
        "recommendation": recommendation,
        "timestamp": time.time()
    }
    
    # Return as hidden JSON block
    return f"[PARENT_REPORT]{json.dumps(report, ensure_ascii=False)}[/PARENT_REPORT]"

# State management
def get_user_states() -> dict:
    from pathlib import Path
    state_file = Path(__file__).parent.parent.parent / "data" / "user_states.json"
    if state_file.exists():
        import json
        with open(state_file) as f:
            return json.load(f)
    return {}

def save_user_states(states: dict):
    from pathlib import Path
    state_file = Path(__file__).parent.parent.parent / "data" / "user_states.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(state_file, "w") as f:
        json.dump(states, f, ensure_ascii=False, indent=2)

def get_user_state(user_id: str) -> dict:
    states = get_user_states()
    if user_id not in states:
        states[user_id] = {"name": None, "grade": 0, "last_topic": None, "onboarding_complete": False}
        save_user_states(states)
    return states[user_id]

def update_user_state(user_id: str, updates: dict):
    states = get_user_states()
    if user_id not in states:
        states[user_id] = {"name": None, "grade": 0, "last_topic": None, "onboarding_complete": False}
    states[user_id].update({k: v for k, v in updates.items() if v is not None})
    save_user_states(states)

def parse_grade(text: str) -> int:
    import re
    text_lower = text.lower()
    
    # More patterns to catch "6", "в 6", "я в 6 классе"
    patterns = [
        r"в\s+(\d+)\s+классе",      # "в 6 классе"
        r"классе\s*(\d+)",             # "классе 6"
        r"класс\s*(\d+)",              # "класс 6" or "6 класс"
        r"(\d+)\s*класс",              # "6класс"
        r"я\s+в\s+(\d+)",            # "я в 6"
        r"учусь\s+в\s+(\d+)",        # "учусь в 6"
        r"(?:^|\s)(\d+)(?:\s|$)",    # standalone "6"
    ]
    
    for p in patterns:
        m = re.search(p, text_lower)
        if m:
            g = m.group(1)
            if g.isdigit() and 1 <= int(g) <= 11:
                return int(g)
    return 0

# Blacklist - not names
NAME_BLACKLIST = {"привет", "здравствуй", "привета", "hi", "hello", "hey", "хай", "прив", "здрав"}

def parse_name(text: str) -> str:
    import re
    text_lower = text.lower().strip()
    
    # Check blacklist first
    if text_lower in NAME_BLACKLIST:
        return ""  # Not a name!
    
    # Patterns
    patterns = [r"меня зовут ([а-яёa-z]+)", r"я ([а-яёa-z]+)", r"моё имя ([а-яёa-z]+)"]
    for p in patterns:
        m = re.search(p, text_lower)
        if m:
            name = m.group(1)
            if name not in NAME_BLACKLIST:
                return name
    
    # NEW: If nothing matched but single word - check if valid name
    words = text.strip().split()
    if len(words) == 1 and len(words[0]) >= 2:
        candidate = words[0].capitalize()
        if candidate.lower() not in NAME_BLACKLIST:
            return candidate
    
    return ""  # No name found


router = APIRouter()
ANSI_ESCAPE_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def _discover_plugins() -> list[Any]:
    try:
        from deeptutor.plugins.loader import discover_plugins
    except Exception:
        logger.debug("Plugin loader unavailable; returning no plugins.", exc_info=True)
        return []
    return discover_plugins()


class ToolExecuteRequest(BaseModel):
    params: dict[str, Any] = {}


class CapabilityExecuteRequest(BaseModel):
    content: str
    tools: list[str] = []
    knowledge_bases: list[str] = []
    language: str = "en"
    config: dict[str, Any] = {}
    attachments: list[dict[str, Any]] = []


@router.get("/list")
async def list_plugins():
    tool_registry = get_tool_registry()
    capability_registry = get_capability_registry()
    plugin_manifests = _discover_plugins()

    tools = [
        {
            "name": definition.name,
            "description": definition.description,
            "parameters": [
                {
                    "name": parameter.name,
                    "type": parameter.type,
                    "description": parameter.description,
                    "required": parameter.required,
                    "default": parameter.default,
                    "enum": parameter.enum,
                }
                for parameter in definition.parameters
            ],
        }
        for definition in tool_registry.get_definitions()
    ]

    capabilities = capability_registry.get_manifests()

    plugins = [
        {
            "name": plugin.name,
            "type": plugin.type,
            "description": plugin.description,
            "stages": plugin.stages,
            "version": plugin.version,
            "author": plugin.author,
        }
        for plugin in plugin_manifests
    ]

    return {
        "tools": tools,
        "capabilities": capabilities,
        "plugins": plugins,
    }


@router.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, body: ToolExecuteRequest):
    """Execute a single tool with explicit parameters (for Playground testing)."""
    registry = get_tool_registry()
    tool = registry.get(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    try:
        result = await tool.execute(**body.params)
        return {
            "success": result.success,
            "content": result.content,
            "sources": result.sources,
            "metadata": result.metadata,
        }
    except Exception as exc:
        logger.exception("Tool execution failed: %s", tool_name)
        raise HTTPException(status_code=500, detail=str(exc))


class _QueueLogHandler(logging.Handler):
    """Temporary handler that pushes formatted log records into an asyncio queue."""

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        super().__init__(level=logging.DEBUG)
        self._queue = queue
        self._loop = loop
        formatter = ConsoleFormatter(service_prefix=None)
        formatter.use_colors = False
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord):
        line = ANSI_ESCAPE_RE.sub("", self.format(record)).strip()
        if line:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, f"[Backend] {line}")


class _QueueTextStream:
    """Capture plain stdout/stderr writes and forward complete lines into the queue."""

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop, stream):
        self._queue = queue
        self._loop = loop
        self._stream = stream
        self._buffer = ""

    def write(self, text: str) -> int:
        if self._stream is not None:
            self._stream.write(text)
            self._stream.flush()

        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.rstrip("\r")
            if line.strip():
                self._loop.call_soon_threadsafe(
                    self._queue.put_nowait, f"[Backend] {ANSI_ESCAPE_RE.sub('', line)}"
                )
        return len(text)

    def flush(self):
        if self._stream is not None:
            self._stream.flush()

    def isatty(self) -> bool:
        return False


def _collect_project_loggers() -> list[logging.Logger]:
    """Collect active project loggers because many do not propagate to the root logger."""
    candidates: list[logging.Logger] = []

    for parent_name in ("deeptutor", "src"):
        parent_logger = logging.getLogger(parent_name)
        if isinstance(parent_logger, logging.Logger):
            candidates.append(parent_logger)

    for name, logger_obj in logging.root.manager.loggerDict.items():
        if not (name.startswith("deeptutor") or name.startswith("src")):
            continue
        if isinstance(logger_obj, logging.Logger):
            candidates.append(logger_obj)

    unique: list[logging.Logger] = []
    seen: set[int] = set()
    for logger_obj in candidates:
        key = id(logger_obj)
        if key in seen:
            continue
        seen.add(key)
        unique.append(logger_obj)
    return unique


async def _execute_stream(tool_name: str, params: dict[str, Any]) -> AsyncGenerator[str, None]:
    """Run a tool while capturing all deeptutor.* logs and yielding SSE events."""
    registry = get_tool_registry()
    tool = registry.get(tool_name)
    if not tool:
        yield f"event: error\ndata: {json.dumps({'detail': f'Tool {tool_name!r} not found'})}\n\n"
        return

    log_queue: asyncio.Queue[str] = asyncio.Queue()
    loop = asyncio.get_running_loop()
    handler = _QueueLogHandler(log_queue, loop)
    stdout_stream = _QueueTextStream(log_queue, loop, stream=None)
    stderr_stream = _QueueTextStream(log_queue, loop, stream=None)

    attached_loggers = _collect_project_loggers()
    for logger_obj in attached_loggers:
        logger_obj.addHandler(handler)

    result_holder: dict[str, Any] = {}
    error_holder: dict[str, str] = {}
    done = asyncio.Event()

    async def _run():
        try:
            import sys

            stdout_stream._stream = sys.stdout
            stderr_stream._stream = sys.stderr
            with contextlib.redirect_stdout(stdout_stream), contextlib.redirect_stderr(
                stderr_stream
            ):
                result = await tool.execute(**params)
            result_holder["data"] = {
                "success": result.success,
                "content": result.content,
                "sources": result.sources,
                "metadata": result.metadata,
            }
        except Exception as exc:
            error_holder["detail"] = str(exc)
        finally:
            done.set()

    task = asyncio.create_task(_run())
    t0 = time.monotonic()

    try:
        while not done.is_set():
            try:
                line = await asyncio.wait_for(log_queue.get(), timeout=0.15)
                yield f"event: log\ndata: {json.dumps({'line': line})}\n\n"
            except asyncio.TimeoutError:
                pass

        while not log_queue.empty():
            line = log_queue.get_nowait()
            yield f"event: log\ndata: {json.dumps({'line': line})}\n\n"

        elapsed_ms = round((time.monotonic() - t0) * 1000)

        if error_holder:
            yield f"event: error\ndata: {json.dumps({'detail': error_holder['detail'], 'elapsed_ms': elapsed_ms})}\n\n"
        else:
            payload = {**result_holder.get("data", {}), "elapsed_ms": elapsed_ms}
            yield f"event: result\ndata: {json.dumps(payload, default=str)}\n\n"
    finally:
        for logger_obj in attached_loggers:
            if handler in logger_obj.handlers:
                logger_obj.removeHandler(handler)
        if not task.done():
            task.cancel()


@router.post("/tools/{tool_name}/execute-stream")
async def execute_tool_stream(tool_name: str, body: ToolExecuteRequest):
    """Execute a tool and stream logs + result as SSE."""
    return StreamingResponse(
        _execute_stream(tool_name, body.params),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _execute_capability_stream(
    capability_name: str,
    body: CapabilityExecuteRequest,
) -> AsyncGenerator[str, None]:
    """Run a capability while streaming logs, trace events, and the final result."""
    from deeptutor.core.context import Attachment, UnifiedContext
    from deeptutor.runtime.orchestrator import ChatOrchestrator

    orch = ChatOrchestrator()
    if capability_name not in orch.list_capabilities():
        yield (
            f"event: error\ndata: "
            f"{json.dumps({'detail': f'Capability {capability_name!r} not found'})}\n\n"
        )
        return

    attachments = [
        Attachment(
            type=a.get("type", "file"),
            url=a.get("url", ""),
            base64=a.get("base64", ""),
            filename=a.get("filename", ""),
            mime_type=a.get("mime_type", ""),
        )
        for a in body.attachments
    ]

    # Get user context data
    user_ctx = body.user_context if hasattr(body, 'user_context') else {}
    chat_history = body.history if hasattr(body, 'history') else []
    
    ctx = UnifiedContext(
        user_message=body.content,
        enabled_tools=body.tools,
        active_capability=capability_name,
        knowledge_bases=body.knowledge_bases,
        attachments=attachments,
        config_overrides=body.config,
        language=body.language,
        conversation_history=chat_history,
        metadata={
            "user_name": user_ctx.get("user_name", ""),
            "grade": user_ctx.get("grade", "")
        }
    )

    log_queue: asyncio.Queue[str] = asyncio.Queue()
    loop = asyncio.get_running_loop()
    handler = _QueueLogHandler(log_queue, loop)
    stdout_stream = _QueueTextStream(log_queue, loop, stream=None)
    stderr_stream = _QueueTextStream(log_queue, loop, stream=None)

    attached_loggers = _collect_project_loggers()
    for logger_obj in attached_loggers:
        logger_obj.addHandler(handler)

    final_result: dict[str, Any] | None = None
    error_holder: dict[str, str] = {}
    done = asyncio.Event()

    async def _run():
        nonlocal final_result
        try:
            import sys

            stdout_stream._stream = sys.stdout
            stderr_stream._stream = sys.stderr
            with contextlib.redirect_stdout(stdout_stream), contextlib.redirect_stderr(
                stderr_stream
            ):
                async for event in orch.handle(ctx):
                    if event.type.value == "result":
                        final_result = dict(event.metadata)
                        continue
                    await log_queue.put(
                        "__STREAM_EVENT__" + json.dumps(event.to_dict(), default=str)
                    )
        except Exception as exc:
            error_holder["detail"] = str(exc)
        finally:
            done.set()

    task = asyncio.create_task(_run())
    t0 = time.monotonic()

    try:
        while not done.is_set():
            try:
                line = await asyncio.wait_for(log_queue.get(), timeout=0.15)
                if line.startswith("__STREAM_EVENT__"):
                    payload = line.removeprefix("__STREAM_EVENT__")
                    yield f"event: stream\ndata: {payload}\n\n"
                else:
                    yield f"event: log\ndata: {json.dumps({'line': line})}\n\n"
            except asyncio.TimeoutError:
                pass

        while not log_queue.empty():
            line = log_queue.get_nowait()
            if line.startswith("__STREAM_EVENT__"):
                payload = line.removeprefix("__STREAM_EVENT__")
                yield f"event: stream\ndata: {payload}\n\n"
            else:
                yield f"event: log\ndata: {json.dumps({'line': line})}\n\n"

        elapsed_ms = round((time.monotonic() - t0) * 1000)
        if error_holder:
            yield (
                f"event: error\ndata: "
                f"{json.dumps({'detail': error_holder['detail'], 'elapsed_ms': elapsed_ms})}\n\n"
            )
        else:
            yield (
                f"event: result\ndata: "
                f"{json.dumps({'success': True, 'data': final_result or {}, 'elapsed_ms': elapsed_ms}, default=str)}\n\n"
            )
    finally:
        for logger_obj in attached_loggers:
            if handler in logger_obj.handlers:
                logger_obj.removeHandler(handler)
        if not task.done():
            task.cancel()


@router.post("/capabilities/{capability_name}/execute-stream")
async def execute_capability_stream(
    capability_name: str,
    body: CapabilityExecuteRequest,
):
    """Execute a capability and stream logs + trace + final result as SSE."""
    return StreamingResponse(
        _execute_capability_stream(capability_name, body),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class ChatRequest(BaseModel):
    user_id: str
    message: str
    name: str | None = None
    grade: int | None = None

# === PHASE 2: Gatekeeper & Normalizer ===
def normalize_input(text: str) -> str:
    """ авто-распознавание опечаток (Раскладка) """
    # English to Russian keyboard layout fix
    en_to_ru = {
        'q':'й', 'w':'ц', 'e':'у', 'r':'к', 't':'е', 'y':'н', 'u':'г', 'i':'ш', 'o':'щ', 'p':'з',
        'a':'ф', 's':'ы', 'd':'в', 'f':'а', 'g':'п', 'h':'р', 'j':'о', 'k':'л', 'l':'д','z':'я', 'x':'ч', 'c':'с', 'v':'м', 'b':'и', 'n':'т', 'm':'ь'
    }
    # Check if text looks like Russian but typed on English layout
    if text and all(c.lower() in en_to_ru for c in text if c.lower().isalpha()):
        return ''.join(en_to_ru.get(c.lower(), c) for c in text)
    return text


def _normalize_answer(text: str) -> str:
    """Normalize answer for comparison: lower, strip, remove extra spaces."""
    if not text:
        return ""
    return text.strip().lower().replace(" ", "").replace(",", ".")


def _levenshtein_distance(a: str, b: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(a) < len(b):
        return _levenshtein_distance(b, a)
    if len(b) == 0:
        return len(a)
    prev_row = list(range(len(b) + 1))
    for i, c1 in enumerate(a):
        curr_row = [i + 1]
        for j, c2 in enumerate(b):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def _extract_single_number(text: str) -> str | None:
    """Extract a single integer token from text if there is exactly one."""
    nums = re.findall(r'-?\d+', text)
    if len(nums) == 1:
        return nums[0]
    return None


def _is_numeric_match(user_ans: str, correct_ans: str) -> bool:
    """Check if both answers contain a single numeric value and match."""
    user_num = _extract_single_number(user_ans)
    correct_num = _extract_single_number(correct_ans)
    return user_num is not None and correct_num is not None and user_num == correct_num


def check_answer_fuzzy(user_answer: str, correct_answer: str, alternatives: list[str] = None, max_typos: int = 1) -> tuple[bool, float]:
    """
    Fuzzy answer checker with multiple strategies.
    
    Returns:
        (is_correct: bool, confidence: float)
    """
    alternatives = alternatives or []
    user_norm = _normalize_answer(user_answer)
    correct_norm = _normalize_answer(correct_answer)
    
    # Strategy 1: Exact match
    if user_norm == correct_norm:
        return True, 1.0
    
    # Strategy 2: Check all alternatives
    all_variants = [correct_answer] + alternatives
    for variant in all_variants:
        var_norm = _normalize_answer(variant)
        if user_norm == var_norm:
            return True, 1.0
        
        # Strategy 3: Numeric match (5 == пять, "ответ: 5" == "5")
        if _is_numeric_match(user_norm, var_norm):
            return True, 0.95

        # If both sides contain a single number, require exact numeric equality.
        # Prevents Levenshtein false positives like "6" vs "5".
        user_num = _extract_single_number(user_norm)
        var_num = _extract_single_number(var_norm)
        if user_num is not None and var_num is not None:
            continue
        
        # Strategy 4: Levenshtein distance for typos
        if len(var_norm) > 0 and len(user_norm) > 0:
            distance = _levenshtein_distance(user_norm, var_norm)
            # Allow 1 typo per 5 chars, max max_typos
            allowed_typos = max(1, len(var_norm) // 5)
            if distance <= min(allowed_typos, max_typos):
                return True, 0.85
    
    return False, 0.0

def check_gatekeeper(text: str) -> str | None:
    """ Anti-distraction: перехват "играть", "котик", etc. """
    text_lower = text.lower()
    distractions = [
        ("котик", "милый котик, но мастерство требует концентрации. 🥋\n\nЗакончим этот прием, и я расскажу легенду о великих числах!"),
        ("играть", "игры — это весело, но мастерство требует практики. 📚\n\nДавай закончим задачу, и в награду — интересная история!"),
        ("ютуб", "ютуб подождет! Давай сначала завершим наш урок. 🎯\n\nПотом можешь смотреть мультики."),
        ("мультик", "мультики — это награда за труд! 🥋\n\nСначала решим задачу, и я расскажу легенду о великих числах!"),
        (" youtube", "ютуб подождет! Сначала — урок. 📚"),
    ]
    for trigger, response in distractions:
        if trigger in text_lower:
            return response
    return None

# Import new diagnostic engine
from deeptutor.services.diagnostic_engine import DiagnosticEngine, diagnostic_engine
from deeptutor.services.practice_engine import PracticeEngine
from deeptutor.services.report_service import build_report

practice_engine = PracticeEngine()


def _panda_response(text: str, state: dict, visual: dict | None = None) -> dict:
    # Keep API contract stable for MVP state machine.
    normalized_state = dict(state or {})
    normalized_state.setdefault("phase", "chat")
    normalized_state.setdefault("weak_topic", None)
    normalized_state.setdefault("current_practice", None)
    normalized_state.setdefault("practice_feedback", None)
    normalized_state.setdefault("report", None)
    return {"text": text, "visual": visual, "state": normalized_state}

@router.post("/panda/chat")
async def panda_chat(request: ChatRequest):
    user_id = request.user_id
    msg = request.message.strip()
    
    # Используем переданные name и grade если есть
    if request.name:
        update_user_state(user_id, {"name": request.name})
    if request.grade and request.grade > 0:
        update_user_state(user_id, {"grade": request.grade})
    
    state = get_user_state(user_id)
    diag = dict(state.get("diagnostic_progress", {}))

    # Stage-0 MVP frontend contract: keep minimal deterministic state fields.
    state.setdefault("phase", "chat")
    state.setdefault("weak_topic", None)
    state.setdefault("current_practice", None)
    state.setdefault("practice_feedback", None)
    state.setdefault("report", None)
    
    # === PHASE 2: Gatekeeper check ===
    gatekeeper_response = check_gatekeeper(msg)
    if gatekeeper_response:
        return _panda_response(gatekeeper_response, state)
    
    # Normalize input (typos, layout)
    original_msg = msg
    msg = normalize_input(msg)
    
    name = state.get("name") or parse_name(msg)
    grade = state.get("grade", 0) or parse_grade(msg)
    pending_confirm = state.get("pending_confirmation", False)
    in_learning = state.get("in_learning", False)
    
    if name and not state.get("name"):
        name = name.capitalize() if name else name
        update_user_state(user_id, {"name": name})
        state["name"] = name
    
    if grade > 0 and not state.get("grade"):
        update_user_state(user_id, {"grade": grade})
        state["grade"] = grade
    
    if not state.get("name"):
        return _panda_response("Привет, мой юный друг! Я твой наставник Панда. 🐼\n\nКак мне называть тебя в нашем зале математических искусств?", state)
    
    if not state.get("grade"):
        return _panda_response(f"Отлично, {state['name']}! 🥋\n\nВ каком классе ты оттачиваешь свое мастерство? (1-9)", state)
    
    if not state.get("path_choice"):
        # Process user choice for path
        msg_lower = msg.lower()
        if "диагностика" in msg_lower:
            start_level = grade if grade else 1
            diag = {"in_diagnostic": True, "questions_answered": 0, "current_diag_level": start_level, "correct_in_row": 0}
            update_user_state(user_id, {"diagnostic_progress": diag})
            q = get_diagnostic_question(user_id, 1, grade)
            response = f"Отлично, {name or 'друг'}! Начнём!\n\n{q['question']}"
            return _panda_response(response, state)
        if diag.get("in_diagnostic"):
            next_q_num = diag.get("questions_answered", 0) + 1
            q = get_diagnostic_question(user_id, next_q_num, grade)

            is_correct, confidence = check_answer_fuzzy(msg, q["answer"], q.get("alternatives", []))
            diag_answers = state.get("diag_answers", [])
            diag_answers.append(
                {
                    "question_id": q.get("id", ""),
                    "grade": q.get("grade", 1),
                    "user_answer": msg,
                    "is_correct": is_correct,
                }
            )

            current_grade_in_diag = diag.get("current_diag_level", 1)
            questions_in_current_grade = diag.get("questions_in_grade", 0) + 1
            errors_in_current_grade = diag.get("errors_in_grade", 0) + (0 if is_correct else 1)

            sequence = state.get("diag_sequence", [])
            if not sequence:
                sequence = diagnostic_engine.build_diagnostic_sequence(grade)
                update_user_state(user_id, {"diag_sequence": sequence})
            questions_for_this_grade = len([item for item in sequence if item["grade"] == current_grade_in_diag])

            diag["questions_answered"] = next_q_num
            diag["questions_in_grade"] = questions_in_current_grade
            diag["errors_in_grade"] = errors_in_current_grade

            if is_correct:
                response = "Правильно! +5 Энергии Ци! 🔥\n\n"
            else:
                response = f"Почти! Правильный ответ: {q['answer']}\n\n"

            if questions_in_current_grade >= questions_for_this_grade:
                if errors_in_current_grade >= diagnostic_engine.FAIL_THRESHOLD:
                    result = diagnostic_engine.run_diagnostic(grade, diag_answers)
                    actual_grade = result.actual_grade
                    weak_topic = diagnostic_engine.select_weak_topic(result)
                    update_user_state(
                        user_id,
                        {
                            "in_learning": True,
                            "diagnostic_progress": {},
                            "actual_grade": actual_grade,
                            "current_topic_id": 1,
                            "diag_answers": [],
                            "diag_sequence": [],
                            "pending_confirmation": False,
                            "weak_topic": weak_topic,
                        },
                    )
                    if weak_topic is None:
                        starting_topic = diagnostic_engine.get_starting_topic(actual_grade)
                        weak_topic = {
                            "grade": actual_grade,
                            "topic_id": str(starting_topic.get("topic_id")),
                            "topic": starting_topic.get("title", "Тема 1"),
                            "source_question_id": "fallback",
                        }
                    explanation_state = {
                        "phase": "explanation",
                        "weak_topic": weak_topic,
                        "current_practice": None,
                        "practice_feedback": None,
                        "report": None,
                    }
                    update_user_state(user_id, explanation_state)
                    state = get_user_state(user_id)
                    response += f"📊 Проверка {current_grade_in_diag} класса завершена.\n"
                    response += f"Обнаружено ошибок: {errors_in_current_grade} из {questions_for_this_grade}\n\n"
                    response += result._generate_message()
                    response += f"\n\n📚 Слабая тема: {weak_topic['topic']}"
                    response += "\nКоротко объясню и затем дам практику. Напиши 'начать', чтобы перейти к практике."
                    return _panda_response(response, state)

                next_grade = current_grade_in_diag + 1
                if next_grade > grade:
                    result = diagnostic_engine.run_diagnostic(grade, diag_answers)
                    actual_grade = grade
                    update_user_state(
                        user_id,
                        {
                            "in_learning": True,
                            "diagnostic_progress": {},
                            "actual_grade": actual_grade,
                            "current_topic_id": 1,
                            "diag_answers": [],
                            "diag_sequence": [],
                            "pending_confirmation": False,
                        },
                    )
                    starting_topic = diagnostic_engine.get_starting_topic(actual_grade)
                    practice_state = {
                        "phase": "practice",
                        "current_practice": {
                            "topic_id": starting_topic.get("topic_id"),
                            "title": starting_topic.get("title", "MVP Practice"),
                        },
                    }
                    update_user_state(user_id, practice_state)
                    state = get_user_state(user_id)
                    response += "🎉 Все классы пройдены успешно!\n"
                    response += f"Твой уровень: {actual_grade} КЛАСС\n\n"
                    response += f"📚 Начинаем с: {starting_topic['title']}"
                    response += "\n\nНапиши 'начать' чтобы приступить к уроку!"
                    return _panda_response(response, state)

                diag["current_diag_level"] = next_grade
                diag["questions_in_grade"] = 0
                diag["errors_in_grade"] = 0
                update_user_state(user_id, {"diagnostic_progress": diag, "in_learning": False})
                response += f"✅ {current_grade_in_diag} класс пройден! Отличная база!\n\n"
                response += f"Переходим к {next_grade} классу...\n\n"
                state = get_user_state(user_id)
                return _panda_response(response, state)

            diag["correct_in_row"] = diag.get("correct_in_row", 0) + (1 if is_correct else 0)
            update_user_state(
                user_id,
                {
                    "diagnostic_progress": diag,
                    "diag_answers": diag_answers,
                    "pending_confirmation": True,
                    "last_correct_answer": q.get("answer", ""),
                    "last_correct_alternatives": q.get("alternatives", []),
                    "current_question": q,
                },
            )
            state = get_user_state(user_id)
            next_q = get_diagnostic_question(user_id, next_q_num + 1, grade)
            question_in_grade = questions_in_current_grade
            total_in_grade = questions_for_this_grade
            if next_q_num < len(sequence):
                response += f"Вопрос {question_in_grade + 1}: {next_q['question']}"
            else:
                response += (
                    "Диагностика завершена!\n\n"
                    f"Твой уровень: {current_grade_in_diag} КЛАСС\n"
                    "Теперь будем учиться! Напиши 'хочу учиться' или 'веди меня'!"
                )
            return _panda_response(response, state)
    
    if "давай" in msg.lower() or "тест" in msg.lower() or "диагностика" in msg.lower():
        start_level = state.get("grade", 1)
        
        # Build full sequence
        sequence = diagnostic_engine.build_diagnostic_sequence(start_level)
        
        diag = {
            "in_diagnostic": True,
            "current_check_grade": 1,  # Start from grade 1
            "questions_in_grade": 0,
            "errors_in_grade": 0
        }
        
        update_user_state(user_id, {
            "diagnostic_progress": diag,
            "in_learning": False,
            "diag_answers": [],
            "actual_grade": None,
            "current_topic_id": None,
            "diag_sequence": sequence
        })
        
        first_q = sequence[0] if sequence else None
        
        if first_q:
            update_user_state(user_id, {
                "pending_confirmation": True,
                "last_correct_answer": first_q["answer"],
                "last_correct_alternatives": first_q.get("alternatives", []),
                "current_question": first_q
            })
            
            # Calculate total questions
            total_q = len(sequence)
            grade_1_q = len([q for q in sequence if q["grade"] == 1])
            
            return {
                "text": (
                    f"🐼 Отлично! Начинаем диагностику!\n\n"
                    f"Я проверю твои знания по порядку: 1 → {start_level} класс.\n"
                    f"Всего вопросов: {total_q}\n\n"
                    f"1 КЛАСС — Вопрос 1 из {grade_1_q}:\n"
                    f"{first_q['question']}\n\n"
                    f"Ты уверен?"
                ),
                "state": state
            }
        else:
            return _panda_response("Ой, что-то пошло не так с вопросами. Давай попробуем ещё раз! 🐼", state)
    
    # Check for topic request
    topic_request = find_topic_class(msg)
    
    if in_learning:
        actual_grade = state.get("actual_grade", state.get("grade", 1))
        current_topic_id = state.get("current_topic_id", 1)
        phase = state.get("phase", "chat")

        if phase == "explanation":
            weak_topic = state.get("weak_topic")
            if weak_topic is None:
                starting_topic = diagnostic_engine.get_starting_topic(actual_grade)
                weak_topic = {
                    "grade": actual_grade,
                    "topic_id": str(starting_topic.get("topic_id")),
                    "topic": starting_topic.get("title", "Тема 1"),
                    "source_question_id": "fallback",
                }
            practice_item = practice_engine.create_practice(weak_topic)
            update_user_state(
                user_id,
                {
                    "phase": "practice",
                    "weak_topic": weak_topic,
                    "current_practice": practice_item,
                    "practice_feedback": None,
                    "report": None,
                },
            )
            state = get_user_state(user_id)
            return _panda_response(
                f"Практика по теме: {practice_item.get('title', weak_topic.get('topic'))}\n{practice_item['question']}",
                state,
            )

        if phase == "practice":
            current_practice = state.get("current_practice") or {}
            if current_practice.get("answer"):
                practice_feedback = practice_engine.check_practice_answer(current_practice, request.message)
                report = build_report(state.get("weak_topic"), practice_feedback)
                update_user_state(
                    user_id,
                    {
                        "phase": "report",
                        "current_practice": current_practice,
                        "practice_feedback": practice_feedback,
                        "report": report,
                    },
                )
                state = get_user_state(user_id)
                return _panda_response(report["summary"], state)

        weak_topic = state.get("weak_topic")
        if weak_topic is None:
            starting_topic = diagnostic_engine.get_starting_topic(actual_grade)
            fallback_weak_topic = {
                "grade": actual_grade,
                "topic_id": str(starting_topic.get("topic_id")),
                "topic": starting_topic.get("title", "Тема 1"),
                "source_question_id": "fallback",
            }
            weak_topic = fallback_weak_topic

        # User asking about specific topic
        if topic_request > 0:
            msg_lower = msg.lower()
            detected_topic = "addition"
            if any(w in msg_lower for w in ["вычита", "минус", "отнять", "съели"]):
                detected_topic = "subtraction"
            elif any(w in msg_lower for w in ["умнож", "пomer", "×", "х"]):
                detected_topic = "multiplication"
            elif any(w in msg_lower for w in ["дел", "делить", "÷"]):
                detected_topic = "division"
            elif any(w in msg_lower for w in ["геометр", "фигур", "треуголь"]):
                detected_topic = "geometry"
            
            response = f"Понял! Разберём тему! 📚\n\n"
            response += f"Эта тема начинается в {topic_request} классе. "
            response += f"Начнём с азов!\n\n"
            if detected_topic == "subtraction":
                response += "Пример: Было 5 яблок, съели 2. Сколько осталось? 🍎"
            elif detected_topic == "multiplication":
                response += "Пример: 2 × 3 = 6 яблок! 🍎🍎🍎"
            elif detected_topic == "division":
                response += "Пример: 6 яблок поделили на 2. Сколько каждому? 🍎"
            else:
                response += "Пример: 1 + 1 = 2🍎"
            
            response += _build_visual_tag(topic_request, detected_topic, True)
            return _panda_response(response, state)
        
        # Continue learning from actual grade
        current_practice = state.get("current_practice", {})

        response = f"Продолжаем обучение! 🎯\n"
        response += f"Твой уровень: {actual_grade} КЛАСС\n"
        response += f"Текущая тема: {current_practice.get('title', 'Тема')}\n\n"
        
        if current_topic_id == 1:
            response += "Начнём с самого начала! Возьми 4 конфеты, потом ещё 3. Сколько конфет? 🍬"
        else:
            response += "Продолжим изучение! Какое задание хочешь решить?"
        
        response += _build_visual_tag(actual_grade, "addition", True)
        return _panda_response(response, state)
    


    state = get_user_state(user_id)
    # Get fresh diagnostic progress each time
    diag = dict(state.get("diagnostic_progress", {}))
    
    name = state.get("name") or parse_name(msg)
    grade = parse_grade(msg)
    
    if name and not state.get("name"):
        update_user_state(user_id, {"name": name})
    if grade > 0:
        update_user_state(user_id, {"grade": grade})
    
    if "давай" in msg.lower() or "начать" in msg.lower() or "диагностика" in msg.lower():
        start_level = grade if grade else 1
        diag = {"in_diagnostic": True, "questions_answered": 0, "current_diag_level": start_level, "correct_in_row": 0}
        update_user_state(user_id, {"diagnostic_progress": diag})
        q = get_diagnostic_question(user_id, 1, grade)
        response = f"Отлично, {name or 'друг'}! Начнём!\n\n{q['question']}"
        return _panda_response(response, state)

    if diag.get("in_diagnostic"):
        # Use questions_answered from state + 1 to get next question
        next_q_num = diag.get("questions_answered", 0) + 1
        q = get_diagnostic_question(user_id, next_q_num, grade)
        
        # Fuzzy answer checking with alternatives
        is_correct, confidence = check_answer_fuzzy(msg, q["answer"], q.get("alternatives", []))
        
        if is_correct:
            correct_in_row = diag.get("correct_in_row", 0) + 1
            questions_answered = diag.get("questions_answered", 0) + 1
            current_level = diag.get("current_diag_level", 1)
            
            response = f"Правильно! +5 Энергии Ци! 🔥\n\n"
            
            if correct_in_row >= 3 and current_level < 9:
                next_level = current_level + 1
                diag["current_diag_level"] = next_level
                diag["correct_in_row"] = 0
                diag["questions_answered"] = 0  # Start from 0 so first question uses idx=0
                update_user_state(user_id, {"diagnostic_progress": diag})
                q2 = get_diagnostic_question(user_id, 1, grade)
                response += f"Отлично! Переходим к уровню {next_level}!\n\nВопрос 1: {q2['question']}"
            elif questions_answered < 5:
                diag["correct_in_row"] = correct_in_row
                diag["questions_answered"] = questions_answered  # Save current count
                update_user_state(user_id, {"diagnostic_progress": diag})
                q2 = get_diagnostic_question(user_id, questions_answered + 1, grade)
                response += f"Вопрос {questions_answered + 1}: {q2['question']}"
            else:
                diag["in_diagnostic"] = False
                update_user_state(user_id, {"diagnostic_progress": diag})
                response += f"Диагностика завершена!\n\nТвой уровень: {current_level} КЛАСС\nТеперь будем учиться! Напиши 'хочу учиться' или 'веди меня'!"
        else:
            current_level = diag.get("current_diag_level", 1)
            diag["in_diagnostic"] = False
            update_user_state(user_id, {"diagnostic_progress": diag})
            response = f"Ой-ой! Наш фундамент задрожал! 🐾\n\nПравильный ответ: {q['answer']}\n\n🎯 Твой уровень: {current_level} КЛАСС\nДиагностика завершена. Теперь учимся! Напиши 'хочу учиться'!"
        
        return _panda_response(response, state)
    
    # Check if user wants teaching
    if "хочу учиться" in msg.lower() or "веди меня" in msg.lower() or "учиться" in msg.lower():
        current_level = diag.get("current_diag_level", grade if grade else 1)
        response = f"Отлично! Начинаем обучение!\n\nТвой уровень: {current_level} КЛАСС\n\nПогнали!"
        return _panda_response(response, state)
    
    response = f"Привет, {name or 'друг'}! Я DeepTutor 🐼\nНапиши 'давай' чтобы начать диагностику!"
    return _panda_response(response, state)
