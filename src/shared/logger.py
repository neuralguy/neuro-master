import asyncio
import logging
import sys
import uuid
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from loguru import logger

from src.config import LOGS_DIR, SRC_DIR, settings

# Suppress noisy loggers
for _logger_name in ("httpx", "httpcore", "urllib3", "aiosqlite"):
    logging.getLogger(_logger_name).setLevel(logging.WARNING)

for _logger_name in ("aiogram", "sqlalchemy.engine"):
    logging.getLogger(_logger_name).setLevel(logging.WARNING)


# === Context Variables ===
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
user_id_var: ContextVar[int] = ContextVar("user_id", default=0)


def get_context() -> dict:
    """Get current logging context."""
    return {
        "request_id": request_id_var.get(),
        "user_id": user_id_var.get(),
    }


def set_context(request_id: str | None = None, user_id: int | None = None) -> None:
    """Set context for current async task."""
    if request_id is not None:
        request_id_var.set(request_id)
    if user_id is not None:
        user_id_var.set(user_id)


def new_request_id() -> str:
    """Generate short unique request ID."""
    return uuid.uuid4().hex[:8]


def context_patcher(record: dict) -> None:
    """Patcher to add context to each log record."""
    record["extra"]["request_id"] = request_id_var.get()
    record["extra"]["user_id"] = user_id_var.get()


# === Formatters ===
def console_formatter(record: dict) -> str:
    """Console format with colors and context."""
    req_id = record["extra"].get("request_id", "-")
    user_id = record["extra"].get("user_id", 0)

    req_part = f"<yellow>{req_id}</yellow>" if req_id != "-" else "<dim>-</dim>"
    user_part = f"<magenta>u:{user_id}</magenta>" if user_id else "<dim>u:-</dim>"

    return (
        f"<green>{{time:HH:mm:ss}}</green> | "
        f"<level>{{level: <8}}</level> | "
        f"{req_part} | {user_part} | "
        f"<cyan>{{name}}:{{line}}</cyan> | "
        f"<level>{{message}}</level>\n"
        f"{{exception}}"
    )


def file_formatter(record: dict) -> str:
    """File format without colors."""
    req_id = record["extra"].get("request_id", "-")
    user_id = record["extra"].get("user_id", 0)

    return (
        f"{{time:YYYY-MM-DD HH:mm:ss}} | "
        f"{{level: <8}} | "
        f"{req_id} | u:{user_id} | "
        f"{{name}}:{{function}}:{{line}} | "
        f"{{message}}\n"
        f"{{exception}}"
    )


# === Decorators ===
def log_call(
    level: str = "DEBUG",
    log_args: bool = True,
    log_result: bool = False,
    max_arg_length: int = 100,
):
    """Decorator for automatic function call logging."""

    def decorator(func: Callable) -> Callable:
        func_name = func.__qualname__

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            args_str = ""
            if log_args:
                args_str = f" | args={_safe_repr(args[1:], max_arg_length)}"
                if kwargs:
                    args_str += f", kwargs={_safe_repr(kwargs, max_arg_length)}"

            logger.log(level, f"→ {func_name}{args_str}")

            start = perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = perf_counter() - start

                result_str = ""
                if log_result:
                    result_str = f" | result={_safe_repr(result, max_arg_length)}"

                logger.log(level, f"← {func_name} | OK | {elapsed:.3f}s{result_str}")
                return result

            except Exception as e:
                elapsed = perf_counter() - start
                logger.error(
                    f"✗ {func_name} | FAILED | {elapsed:.3f}s | {type(e).__name__}: {e}"
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            args_str = ""
            if log_args:
                args_str = f" | args={_safe_repr(args[1:], max_arg_length)}"

            logger.log(level, f"→ {func_name}{args_str}")

            start = perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = perf_counter() - start
                logger.log(level, f"← {func_name} | OK | {elapsed:.3f}s")
                return result
            except Exception as e:
                elapsed = perf_counter() - start
                logger.error(
                    f"✗ {func_name} | FAILED | {elapsed:.3f}s | {type(e).__name__}: {e}"
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def _safe_repr(obj: Any, max_len: int = 100) -> str:
    """Safe string representation of object."""
    try:
        if isinstance(obj, tuple) and len(obj) == 0:
            return "()"
        s = repr(obj)
        if len(s) > max_len:
            return s[:max_len] + "..."
        return s
    except Exception:
        return f"<{type(obj).__name__}>"


# === Telegram Sink ===
class TelegramSink:
    """Sink for sending logs to Telegram with batching."""

    def __init__(
        self, chat_id: int, batch_interval: float = 5.0, max_batch_size: int = 20
    ):
        self.chat_id = chat_id
        self.batch_interval = batch_interval
        self.max_batch_size = max_batch_size
        self.bot = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._buffer: list[str] = []
        self._lock = asyncio.Lock()
        self._flush_task: asyncio.Task | None = None

    def set_bot(self, bot):
        self.bot = bot
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = asyncio.get_event_loop()
        self._flush_task = self._loop.create_task(self._periodic_flush())

    def __call__(self, message):
        if self.bot is None or self._loop is None:
            return

        record = message.record
        text = self._format_short(record)
        self._loop.call_soon_threadsafe(self._add_to_buffer, text)

    def _add_to_buffer(self, text: str):
        self._buffer.append(text)
        if "CRITICAL" in text or len(self._buffer) >= self.max_batch_size:
            self._loop.create_task(self._flush())

    async def _periodic_flush(self):
        """Periodic flush of accumulated logs."""
        while True:
            await asyncio.sleep(self.batch_interval)
            await self._flush()

    async def _flush(self):
        """Send all accumulated logs as one message."""
        if not self._buffer or not self.bot:
            return

        async with self._lock:
            if not self._buffer:
                return
            logs = self._buffer[: self.max_batch_size]
            self._buffer = self._buffer[self.max_batch_size :]

        text = "\n".join(logs)

        try:
            for chunk in self._split_message(text):
                await self.bot.send_message(self.chat_id, chunk, parse_mode="HTML")
                await asyncio.sleep(0.5)
        except Exception as e:
            print(f"[TelegramSink] Failed: {e}", file=sys.stderr)

    def _format_short(self, record) -> str:
        """Short format for batch."""
        emoji = {
            "DEBUG": "🔍",
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🔥",
        }.get(record["level"].name, "📝")

        time_str = record["time"].strftime("%H:%M:%S")
        user_id = record["extra"].get("user_id", 0)
        user_part = f" 👤{user_id}" if user_id else ""

        name = record["name"].replace("src.modules.", "").replace("src.", "")
        location = f"{name}:{record['line']}"

        msg = self._escape(record["message"][:200])
        line = f"{emoji} <code>{time_str}</code>{user_part} | {location}\n   {msg}"

        if record["exception"] and record["level"].name in ("ERROR", "CRITICAL"):
            exc = record["exception"]
            exc_short = f"{exc.type.__name__}: {exc.value}"
            line += f"\n   <code>{self._escape(exc_short[:100])}</code>"

        return line

    def _split_message(self, text: str) -> list[str]:
        """Split long message."""
        max_len = 4000
        if len(text) <= max_len:
            return [text]

        chunks = []
        while text:
            chunk = text[:max_len]
            if len(text) > max_len:
                last_newline = chunk.rfind("\n")
                if last_newline > max_len // 2:
                    chunk = text[:last_newline]
            chunks.append(chunk)
            text = text[len(chunk) :]
        return chunks

    @staticmethod
    def _escape(text: str) -> str:
        return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    async def close(self):
        """Close and flush remaining logs."""
        if self._flush_task:
            self._flush_task.cancel()
        await self._flush()


_telegram_sink: TelegramSink | None = None


def enable_telegram_logging(bot, chat_id: int, level: str = "WARNING"):
    """Enable sending logs to Telegram."""
    global _telegram_sink

    _telegram_sink = TelegramSink(chat_id=chat_id, batch_interval=5, max_batch_size=40)
    _telegram_sink.set_bot(bot)

    logger.add(
        _telegram_sink,
        level=level,
        format="{message}",
        enqueue=False,
        backtrace=True,
        diagnose=True,
    )
    logger.info(f"Telegram logging enabled | chat_id={chat_id}")


# === WebSocket Sink for Admin Panel ===
class WebSocketLogBroadcaster:
    """Broadcaster for sending logs to connected WebSocket clients."""

    def __init__(self):
        self.connections: set = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket):
        async with self._lock:
            self.connections.add(websocket)

    async def disconnect(self, websocket):
        async with self._lock:
            self.connections.discard(websocket)

    async def broadcast(self, message: dict):
        async with self._lock:
            dead_connections = set()
            for ws in self.connections:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead_connections.add(ws)
            self.connections -= dead_connections


log_broadcaster = WebSocketLogBroadcaster()


class WebSocketSink:
    """Loguru sink for WebSocket broadcasting."""

    def __init__(self, broadcaster: WebSocketLogBroadcaster):
        self.broadcaster = broadcaster
        self._loop: asyncio.AbstractEventLoop | None = None

    def __call__(self, message):
        record = message.record

        log_entry = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
            "user_id": record["extra"].get("user_id", 0),
            "request_id": record["extra"].get("request_id", "-"),
        }

        if record["exception"]:
            log_entry["exception"] = str(record["exception"])

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcaster.broadcast(log_entry))
        except RuntimeError:
            pass


def enable_websocket_logging(level: str = "DEBUG"):
    """Enable WebSocket log broadcasting."""
    ws_sink = WebSocketSink(log_broadcaster)
    logger.add(
        ws_sink,
        level=level,
        format="{message}",
        enqueue=False,
        backtrace=False,
        diagnose=False,
    )
    logger.info("WebSocket logging enabled")


# === Logger Setup ===
def setup_logger():
    """Configure and return logger."""
    LOGS_DIR.mkdir(exist_ok=True)
    logger.remove()
    logger.configure(patcher=context_patcher)

    # 1. Console
    logger.add(
        sys.stderr,
        level=settings.LOG_LEVEL,
        format=console_formatter,
        colorize=True,
        diagnose=False,
        backtrace=False,
    )

    # 2. General file
    logger.add(
        LOGS_DIR / "app.log",
        level="INFO",
        format=file_formatter,
        enqueue=True,
        encoding="utf-8",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        diagnose=False,
        backtrace=False,
    )

    # 3. Errors file
    logger.add(
        LOGS_DIR / "errors.log",
        level="ERROR",
        format=file_formatter,
        enqueue=True,
        encoding="utf-8",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        diagnose=True,
        backtrace=True,
    )

    # 4. Module-specific logs
    modules_dir = SRC_DIR / "modules"
    if modules_dir.exists():
        for module_item in modules_dir.iterdir():
            if module_item.is_dir() and not module_item.name.startswith("_"):
                module_name = module_item.name
                logger.add(
                    LOGS_DIR / f"{module_name}.log",
                    level="DEBUG",
                    filter=lambda record, mn=module_name: mn in record["name"],
                    format=file_formatter,
                    enqueue=True,
                    encoding="utf-8",
                    rotation="5 MB",
                    retention="7 days",
                    compression="zip",
                    diagnose=False,
                    backtrace=False,
                )

    return logger


# === Context Manager ===
class LogContext:
    """Context manager for setting logging context."""

    def __init__(self, user_id: int | None = None, request_id: str | None = None):
        self.user_id = user_id
        self.request_id = request_id or new_request_id()
        self._old_user_id = None
        self._old_request_id = None

    def __enter__(self):
        self._old_user_id = user_id_var.get()
        self._old_request_id = request_id_var.get()
        set_context(request_id=self.request_id, user_id=self.user_id)
        return self

    def __exit__(self, *args):
        set_context(request_id=self._old_request_id, user_id=self._old_user_id)

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, *args):
        self.__exit__(*args)


# Initialize logger on import
logger = setup_logger()
