from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, cast

Transport = Literal["stdio", "streamable_http"]


@dataclass(frozen=True)
class Settings:
    transport: Transport
    log_level: str
    bind_host: str
    bind_port: int
    mcp_path: str
    protocol_version: str

    @staticmethod
    def from_env() -> "Settings":
        raw_transport = os.getenv("MCP_TRANSPORT", "stdio").strip().lower()    #A
        if raw_transport not in ("stdio", "streamable_http"):
            raise ValueError(
                f"Unsupported MCP_TRANSPORT={raw_transport!r}; "
                "use 'stdio' or 'streamable_http'"
            )    #B

        raw_port = os.getenv("MCP_BIND_PORT", "8000").strip()    #C
        try:
            port = int(raw_port)
        except ValueError as exc:
            raise ValueError(f"Invalid MCP_BIND_PORT={raw_port!r}") from exc
        if not (1 <= port <= 65535):
            raise ValueError("MCP_BIND_PORT must be between 1 and 65535")    #D

        path = os.getenv("MCP_ENDPOINT_PATH", "/mcp").strip()
        if not path.startswith("/") or "?" in path or "#" in path:
            raise ValueError("MCP_ENDPOINT_PATH must be an absolute path like '/mcp'")    #E

        return Settings(
            transport=cast(Transport, raw_transport),    #F
            log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper(),
            bind_host=os.getenv("MCP_BIND_HOST", "127.0.0.1").strip(),
            bind_port=port,
            mcp_path=path,
            protocol_version=os.getenv("MCP_PROTOCOL_VERSION", "2025-11-25").strip(),
        )


#--------------

# ... (from previous listing)

import json
import logging
import sys
from datetime import datetime, timezone


class JsonLogFormatter(logging.Formatter):
    """Structured JSON formatter for operational logs."""

    _BUILTIN_ATTRS = frozenset({
        "name", "msg", "args", "created", "filename", "funcName", "levelname",
        "levelno", "lineno", "module", "msecs", "pathname", "process",
        "processName", "relativeCreated", "stack_info", "exc_info", "exc_text",
        "thread", "threadName", "taskName", "message",
    })

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),    #A
            "level": record.levelname,    #B
            "logger": record.name,    #C
            "message": record.getMessage(),    #D
        }

        for key, val in record.__dict__.items():
            if key not in self._BUILTIN_ATTRS and not key.startswith("_"):
                payload[key] = val    #E

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)    #F

        return json.dumps(payload, ensure_ascii=False, default=str)    #G


def configure_logging(log_level: str) -> None:
    """
    Configure structured logging with stdio-safe stream separation.
    stdout is reserved for protocol messages in stdio mode.
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, log_level, logging.INFO))    #H

    handler = logging.StreamHandler(stream=sys.stderr)    #I
    handler.setFormatter(JsonLogFormatter())

    root.handlers[:] = [handler]    #J

#-------------------

# ... (from previous listing)

import logging


def build_capability_server():
    """
    Return the existing MCP server instance from prior chapters.
    Keep tools/resources/prompts names and schemas unchanged.
    """
    from server import mcp    #A
    return mcp


def run_stdio(server_obj) -> None:
    """
    Start stdio transport.
    In stdio mode, protocol messages use stdout; logs remain on stderr.
    """
    log = logging.getLogger("mcp.transport.stdio")
    log.info("entering stdio transport loop")
    if hasattr(server_obj, "run"):
        server_obj.run()    #B
        return
    raise RuntimeError(
        "Server object has no .run() method. "
        "Ensure build_capability_server() returns a FastMCP instance."
    )


def run_streamable_http(server_obj, settings: Settings) -> None:
    """
    Streamable HTTP seam for section 4.2.
    """
    log = logging.getLogger("mcp.transport.http")
    log.info(
        "streamable HTTP requested",
        extra={
            "host": settings.bind_host,
            "port": settings.bind_port,
            "path": settings.mcp_path,
        },
    )
    raise NotImplementedError("Implemented in section 4.2")    #C


def main() -> None:
    """
    Single startup path:
    1) load settings
    2) configure logging
    3) build capability server
    4) select transport
    """
    settings = Settings.from_env()    #D
    configure_logging(settings.log_level)    #E

    log = logging.getLogger("mcp.entrypoint")
    log.info(
        "MCP server starting",
        extra={
            "transport": settings.transport,
            "protocol_version": settings.protocol_version,
            "log_level": settings.log_level,
        },
    )

    server_obj = build_capability_server()    #F
    log.info("capability server constructed")

    if settings.transport == "stdio":
        run_stdio(server_obj)    #G
    else:
        run_streamable_http(server_obj, settings)    #H


if __name__ == "__main__":
    main()    #I

#------------------------------------------
# ... (from previous listing)

from typing import Any
from fastapi import FastAPI, Request, HTTPException, Response


def _validate_origin(request: Request, allowed_origins: set[str]) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in allowed_origins:    #A
        raise HTTPException(status_code=403, detail="Forbidden origin")


def _require_streamable_accept(request: Request) -> None:
    accept = request.headers.get("accept", "")
    has_json = "application/json" in accept
    has_sse = "text/event-stream" in accept
    if not (has_json and has_sse):    #B
        raise HTTPException(
            status_code=406,
            detail="Accept must include application/json and text/event-stream",
        )


def _parse_single_jsonrpc_object(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):    #C
        raise HTTPException(status_code=400, detail="POST body must be one JSON-RPC object")
    return payload


def create_streamable_http_app(server_obj, settings: Settings) -> FastAPI:
    app = FastAPI()

    @app.api_route(settings.mcp_path, methods=["POST", "GET"])    #D
    async def mcp_endpoint(request: Request):
        _validate_origin(request, settings.allowed_origins)

        if request.method == "GET":
            if not settings.enable_get_sse:  # implementation-defined switch
                return Response(status_code=405, headers={"Allow": "POST"})    #E
            return await open_sse_stream(server_obj, request)    #F (Listing 4.5)

        _require_streamable_accept(request)
        msg = _parse_single_jsonrpc_object(await request.json())

        kind = classify_jsonrpc_message(msg)    #G (Listing 4.5)
        if kind in ("notification", "response"):
            return Response(status_code=202)    #H

        return await handle_jsonrpc_request(server_obj, msg, request)    #I (Listing 4.5)

    return app

#----------------------------------------
# ... (from previous listing)

MessageKind = Literal["request", "notification", "response", "invalid"]


def classify_jsonrpc_message(msg: dict[str, Any]) -> MessageKind:
    if msg.get("jsonrpc") != "2.0":
        return "invalid"                                    #A

    has_method = isinstance(msg.get("method"), str)
    has_id = "id" in msg
    has_result_or_error = ("result" in msg) or ("error" in msg)

    if has_method and has_id:
        return "request"                                    #B
    if has_method and not has_id:
        return "notification"                               #C
    if (not has_method) and has_id and has_result_or_error:
        return "response"                                   #D
    return "invalid"


def _jsonrpc_error(id_value: Any, code: int, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    err: dict[str, Any] = {"code": int(code), "message": message}    #E
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id_value, "error": err}


async def _dispatch_request(server_obj, msg: dict[str, Any]) -> tuple[str, Any]:
    """
    Implementation seam:
    - expected return: ("json", <jsonrpc_obj>) or ("sse", <async_iterable_events>)
    """
    dispatch_fn = getattr(server_obj, "dispatch_jsonrpc", None)
    if dispatch_fn is None:
        raise HTTPException(status_code=501, detail="dispatch_jsonrpc not implemented")  # #F

    out = dispatch_fn(msg)
    if inspect.isawaitable(out):
        out = await out

    if isinstance(out, tuple) and len(out) == 2:
        mode, payload = out
    else:
        mode, payload = "json", out                         #G

    if mode not in ("json", "sse"):
        raise ValueError("dispatch mode must be 'json' or 'sse'")
    return mode, payload


async def handle_jsonrpc_request(server_obj, msg: dict[str, Any], request: Request):
    kind = classify_jsonrpc_message(msg)
    req_id = msg.get("id")

    if kind != "request":
        body = _jsonrpc_error(req_id, -32600, "Invalid Request")      #H
        return JSONResponse(content=body, media_type="application/json", status_code=200)

    try:
        mode, payload = await _dispatch_request(server_obj, msg)
    except ValueError as exc:
        body = _jsonrpc_error(req_id, -32602, "Invalid params", {"detail": str(exc)})    #I
        return JSONResponse(content=body, media_type="application/json", status_code=200)
    except HTTPException:
        raise
    except Exception as exc:
        body = _jsonrpc_error(req_id, -32603, "Internal error", {"detail": str(exc)})
        return JSONResponse(content=body, media_type="application/json", status_code=200)

    if mode == "sse":
        return StreamingResponse(
            payload,
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},             #J
        )

    return JSONResponse(content=payload, media_type="application/json", status_code=200)


#-----------------------------------------
# ... (from previous listings)
# Requires: Settings, configure_logging, build_capability_server,
#           run_stdio(...), create_streamable_http_app(...)

def run_streamable_http(server_obj, settings: Settings) -> None:
    """
    Boot hosted transport using the same capability core.
    """
    log = logging.getLogger("mcp.transport.http")
    log.info(
        "starting streamable HTTP transport",
        extra={
            "host": settings.bind_host,
            "port": settings.bind_port,
            "path": settings.mcp_path,
        },
    )

    app = create_streamable_http_app(server_obj, settings)          #A

    uvicorn.run(                                                     #B
        app,
        host=settings.bind_host,
        port=settings.bind_port,
        log_level=settings.log_level.lower(),
        access_log=True,
    )


def main() -> None:
    """
    Unified startup sequence for both transports.
    """
    settings = Settings.from_env()                                  #C
    configure_logging(settings.log_level)                           #D

    log = logging.getLogger("mcp.entrypoint")
    log.info(
        "MCP server starting",
        extra={
            "transport": settings.transport,
            "protocol_version": settings.protocol_version,
            "log_level": settings.log_level,
        },
    )

    server_obj = build_capability_server()                          #E
    log.info("capability server constructed")

    if settings.transport == "stdio":
        run_stdio(server_obj)                                       #F
    elif settings.transport == "streamable_http":
        run_streamable_http(server_obj, settings)                   #G
    else:
        raise ValueError(f"Unsupported transport: {settings.transport!r}")  #H


if __name__ == "__main__":
    main()                                                          #I


#------------------------------

# ... (from previous listing in app.py)

@dataclass(frozen=True)
class IssueListQuery:
    owner: str
    repo: str
    state: str
    limit: int
    page: int
    include_pull_requests: bool


def _as_non_empty_text(name: str, value: object) -> str:
    text = str(value).strip() if value is not None else ""          #A
    if not text:
        raise ValueError(f"Invalid params: '{name}' is required")   #B
    return text


def _as_bounded_int(name: str, value: object, *, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)                                         #C
    except Exception as exc:
        raise ValueError(f"Invalid params: '{name}' must be an integer") from exc

    if parsed < minimum or parsed > maximum:
        raise ValueError(
            f"Invalid params: '{name}' must be between {minimum} and {maximum}"
        )                                                           #D
    return parsed


def parse_issue_list_query(arguments: dict[str, object]) -> IssueListQuery:
    """
    Parse MCP tool arguments into a deterministic internal query model.
    Raise ValueError on invalid input; dispatch layer maps this to JSON-RPC error.
    """
    owner = _as_non_empty_text("owner", arguments.get("owner"))     #E
    repo = _as_non_empty_text("repo", arguments.get("repo"))        #F

    state = str(arguments.get("state", "open")).strip().lower()     #G
    if state not in {"open", "closed", "all"}:
        raise ValueError("Invalid params: 'state' must be open|closed|all")

    limit = _as_bounded_int("limit", arguments.get("limit", 20), minimum=1, maximum=100)   #H
    page = _as_bounded_int("page", arguments.get("page", 1), minimum=1, maximum=100000)    #I

    include_prs = bool(arguments.get("include_pull_requests", False))                       #J

    return IssueListQuery(
        owner=owner,
        repo=repo,
        state=state,
        limit=limit,
        page=page,
        include_pull_requests=include_prs,
    )                                                                #K


#---------------------------
# ... (from previous listing in app.py)

def _normalize_labels(raw_labels: object) -> list[str]:
    labels: list[str] = []
    if isinstance(raw_labels, list):
        for item in raw_labels:
            if isinstance(item, dict):
                name = str(item.get("name", "")).strip()
                if name:
                    labels.append(name)                                      #A
    return labels


def normalize_issue(raw: dict[str, object]) -> dict[str, object]:
    """
    Map one raw GitHub issue object to the canonical MCP output shape.
    """
    html_url = str(raw.get("html_url") or raw.get("url") or "").strip()      #B
    title = str(raw.get("title") or "").strip()
    state = str(raw.get("state") or "").strip().lower()

    return {
        "number": raw.get("number"),                                          #C
        "title": title,
        "state": state,
        "url": html_url,
        "labels": _normalize_labels(raw.get("labels")),
        "updatedAt": raw.get("updated_at"),                                   #D
        "isPullRequest": isinstance(raw.get("pull_request"), dict),           #E
    }


def normalize_issue_items(
    raw_items: list[dict[str, object]],
    *,
    include_pull_requests: bool,
    limit: int,
) -> list[dict[str, object]]:
    """
    Normalize list payload and enforce contract-level filtering.
    """
    out: list[dict[str, object]] = []

    for raw in raw_items:
        normalized = normalize_issue(raw)                                     #F
        if (not include_pull_requests) and bool(normalized["isPullRequest"]):
            continue                                                           #G
        out.append(normalized)

        if len(out) >= limit:                                                 #H
            break

    return out

#----------------------------------------------

# ... (from previous listing in app.py)

CacheValue = list[dict[str, object]]


@dataclass(frozen=True)
class TTLCacheEntry:
    value: CacheValue
    expires_at_epoch: float


class NormalizedIssuesCache:
    """
    Cache normalized outputs across three scopes:
    - request scope: caller-owned dict (lifetime = one dispatch)
    - session scope: server-held per session id
    - ttl scope: server-held shared cache with expiry
    """

    def __init__(self, *, default_ttl_seconds: int = 30, ttl_max_entries: int = 512) -> None:
        self.default_ttl_seconds = default_ttl_seconds                          #A
        self.ttl_max_entries = ttl_max_entries
        self._session_cache: dict[str, dict[str, CacheValue]] = {}             #B
        self._ttl_cache: dict[str, TTLCacheEntry] = {}                         #C

    @staticmethod
    def key_for_issue_query(query: IssueListQuery) -> str:
        return "|".join([
            query.owner, query.repo, query.state,
            str(query.page), str(query.limit), str(query.include_pull_requests)
        ])                                                                      #D

    @staticmethod
    def _clone(value: CacheValue) -> CacheValue:
        return [dict(item) for item in value]                                   #E

    # ---------- request scope ----------
    def get_request(self, request_cache: dict[str, CacheValue], key: str) -> CacheValue | None:
        hit = request_cache.get(key)
        return None if hit is None else self._clone(hit)                        #F

    def put_request(self, request_cache: dict[str, CacheValue], key: str, value: CacheValue) -> None:
        request_cache[key] = self._clone(value)

    # ---------- session scope ----------
    def get_session(self, session_id: str | None, key: str) -> CacheValue | None:
        if not session_id:
            return None
        bucket = self._session_cache.get(session_id)
        if not bucket:
            return None
        hit = bucket.get(key)
        return None if hit is None else self._clone(hit)                        #G

    def put_session(self, session_id: str | None, key: str, value: CacheValue) -> None:
        if not session_id:
            return
        bucket = self._session_cache.setdefault(session_id, {})
        bucket[key] = self._clone(value)

    # ---------- ttl scope ----------
    def get_ttl(self, key: str, *, now_epoch: float) -> CacheValue | None:
        entry = self._ttl_cache.get(key)
        if entry is None:
            return None
        if now_epoch >= entry.expires_at_epoch:
            self._ttl_cache.pop(key, None)                                      #H
            return None
        return self._clone(entry.value)

    def put_ttl(
        self,
        key: str,
        value: CacheValue,
        *,
        now_epoch: float,
        ttl_seconds: int | None = None,
    ) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        self._ttl_cache[key] = TTLCacheEntry(
            value=self._clone(value),
            expires_at_epoch=now_epoch + max(1, ttl),                           #I
        )
        self._prune_ttl_if_needed()

    def _prune_ttl_if_needed(self) -> None:
        if len(self._ttl_cache) <= self.ttl_max_entries:
            return
        # Remove soonest-to-expire entries first.
        for k, _ in sorted(self._ttl_cache.items(), key=lambda kv: kv[1].expires_at_epoch):
            self._ttl_cache.pop(k, None)
            if len(self._ttl_cache) <= self.ttl_max_entries:
                break                                                           #J


#----------------------------------------
# ... (from previous listing in app.py)
import time


def execute_github_issues_list(
    arguments: dict[str, object],
    *,
    session_id: str | None,
    request_cache: dict[str, CacheValue],
    cache_scope: str,
) -> dict[str, object]:
    query = parse_issue_list_query(arguments)                                  #A
    key = NormalizedIssuesCache.key_for_issue_query(query)                    #B
    now_epoch = time.time()

    # 1) Read from selected cache scope
    cached: CacheValue | None = None
    if cache_scope == "request":
        cached = CACHE.get_request(request_cache, key)                        #C
    elif cache_scope == "session":
        cached = CACHE.get_session(session_id, key)                           #D
    elif cache_scope == "ttl":
        cached = CACHE.get_ttl(key, now_epoch=now_epoch)                      #E

    if cached is not None:
        return {
            "content": cached,
            "meta": {"cache": {"scope": cache_scope, "hit": True}},
        }                                                                      #F

    # 2) Fetch raw provider data through existing integration seam
    # Replace this import with the exact adapter from your current codebase.
    from server import list_github_issues_raw                                 #G
    raw_items = list_github_issues_raw(
        owner=query.owner,
        repo=query.repo,
        state=query.state,
        page=query.page,
        per_page=query.limit,
    )

    # 3) Normalize to stable MCP output contract
    normalized = normalize_issue_items(
        raw_items=raw_items,
        include_pull_requests=query.include_pull_requests,
        limit=query.limit,
    )                                                                          #H

    # 4) Write normalized output to selected cache scope
    if cache_scope == "request":
        CACHE.put_request(request_cache, key, normalized)                      #I
    elif cache_scope == "session":
        CACHE.put_session(session_id, key, normalized)                         #J
    elif cache_scope == "ttl":
        CACHE.put_ttl(key, normalized, now_epoch=now_epoch)                    #K

    return {
        "content": normalized,
        "meta": {"cache": {"scope": cache_scope, "hit": False}},
    }


# ... (inside existing JSON-RPC request dispatcher from Listing 4.5)
if method == "tools/call":
    name = str((params or {}).get("name", "")).strip()
    arguments = (params or {}).get("arguments") or {}

    if name == runtime_github_issues_tool_name:                                #L
        try:
            result = execute_github_issues_list(
                arguments=arguments,
                session_id=session_id,
                request_cache=request_cache,
                cache_scope=cache_scope,
            )
            return _jsonrpc_result(id_value, result)
        except ValueError as exc:
            return _jsonrpc_error(id_value, -32602, str(exc))                  #M


#--------------------------------------------

# ... (from previous listings in app.py)
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional

SESSION_HEADER = "MCP-Session-Id"  # #A


@dataclass
class SessionRecord:
    session_id: str
    phase: str = "new"              # new -> initialized -> operate -> shutdown
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


SESSIONS: Dict[str, SessionRecord] = {}  # #B


def _touch(s: SessionRecord) -> None:
    s.updated_at = datetime.now(timezone.utc).isoformat()


def get_session(session_id: str) -> Optional[SessionRecord]:
    return SESSIONS.get(session_id)


def get_or_create_session(session_id: str) -> SessionRecord:
    s = SESSIONS.get(session_id)
    if not s:
        s = SessionRecord(session_id=session_id)
        SESSIONS[session_id] = s
    return s


def enforce_lifecycle(method: str, session_id: Optional[str]) -> Optional[dict]:
    """
    Returns JSON-RPC error object dict when blocked, else None.
    Lifecycle policy here is implementation-defined but spec-safe.
    """
    if method == "initialize":  # #C
        if not session_id:
            return {"code": -32600, "message": "Invalid Request",
                    "data": {"reason": "missing_session_id"}}  # #D
        s = get_or_create_session(session_id)
        if s.phase == "shutdown":
            return {"code": -32600, "message": "Invalid Request",
                    "data": {"reason": "session_closed"}}
        s.phase = "initialized"
        _touch(s)
        return None

    if method == "notifications/initialized":  # #E
        if not session_id:
            return {"code": -32600, "message": "Invalid Request",
                    "data": {"reason": "missing_session_id"}}
        s = get_or_create_session(session_id)
        if s.phase not in ("initialized", "operate"):
            return {"code": -32600, "message": "Invalid Request",
                    "data": {"reason": "initialize_required"}}
        s.phase = "operate"
        _touch(s)
        return None

    # Operate-phase methods (tools/*, resources/*, prompts/*, tasks/*, notifications/cancelled)
    if method.startswith(("tools/", "resources/", "prompts/", "tasks/", "notifications/cancelled")):  # #F
        if not session_id:
            return {"code": -32600, "message": "Invalid Request",
                    "data": {"reason": "missing_session_id"}}
        s = get_session(session_id)
        if not s or s.phase not in ("operate",):
            return {"code": -32600, "message": "Invalid Request",
                    "data": {"reason": "initialize_then_initialized_required"}}  # #G
        _touch(s)
        return None

    if method == "shutdown":  # implementation-defined administrative method
        if session_id and (s := get_session(session_id)):
            s.phase = "shutdown"
            _touch(s)
        return None

    # Unknown method lifecycle check is deferred to normal dispatcher
    return None

#-------------------------------------

# ... (from previous listing in app.py)
import uuid
from typing import Any, Dict, Optional

TERMINAL_TASK_STATES = frozenset({"completed", "failed", "cancelled"})  # #A


@dataclass
class TaskRecord:
    task_id: str
    session_id: str
    request_id: str
    method: str
    status: str = "running"   # running | completed | failed | cancelled
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    result: Optional[dict] = None
    error: Optional[dict] = None
    cancel_reason: Optional[str] = None


TASKS: Dict[str, TaskRecord] = {}                 # #B
REQUEST_TO_TASK: Dict[str, str] = {}              # #C


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _touch_task(t: TaskRecord) -> None:
    t.updated_at = _now_iso()


def create_task(*, session_id: str, request_id: str, method: str) -> TaskRecord:
    task_id = f"task_{uuid.uuid4().hex[:12]}"      # #D
    t = TaskRecord(task_id=task_id, session_id=session_id, request_id=request_id, method=method)
    TASKS[task_id] = t
    REQUEST_TO_TASK[request_id] = task_id          # #E
    return t


def get_task(task_id: str) -> Optional[TaskRecord]:
    return TASKS.get(task_id)


def get_task_by_request_id(request_id: str) -> Optional[TaskRecord]:
    task_id = REQUEST_TO_TASK.get(request_id)
    return TASKS.get(task_id) if task_id else None


def is_terminal_task(t: TaskRecord) -> bool:
    return t.status in TERMINAL_TASK_STATES        # #F


def complete_task(task_id: str, result: dict) -> TaskRecord:
    t = TASKS[task_id]
    t.status = "completed"
    t.result = result
    _touch_task(t)
    return t


def fail_task(task_id: str, *, code: int, message: str, data: Optional[dict] = None) -> TaskRecord:
    t = TASKS[task_id]
    t.status = "failed"
    t.error = {"code": int(code), "message": message, "data": data or {}}  # #G
    _touch_task(t)
    return t


def cancellable_or_error(t: TaskRecord) -> Optional[dict]:
    """
    Returns a JSON-RPC error object when cancellation is invalid.
    """
    if is_terminal_task(t):
        return {                                  # #H
            "code": -32602,
            "message": "Invalid params",
            "data": {
                "reason": "task_already_terminal",
                "taskId": t.task_id,
                "status": t.status,
            },
        }
    return None


def cancel_task(task_id: str, reason: Optional[str] = None) -> TaskRecord:
    t = TASKS[task_id]
    t.status = "cancelled"
    t.cancel_reason = reason
    _touch_task(t)
    return t


#----------------------------------
# ... (from previous listings in app.py)

INFLIGHT: Dict[str, dict] = {}  # request_id -> {"session_id": str, "method": str, "cancelled": bool}  # #A


def _rpc_result(request_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _rpc_error(request_id, code: int, message: str, data: Optional[dict] = None) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": int(code), "message": message, "data": data or {}}}  # #B


def handle_tasks_method(method: str, params: dict, request_id, session_id: str) -> dict:
    if method in ("tasks/get", "tasks/result"):
        task_id = params.get("taskId")
        t = get_task(task_id) if isinstance(task_id, str) else None
        if not t or t.session_id != session_id:
            return _rpc_error(request_id, -32602, "Invalid params", {"reason": "unknown_task"})
        payload = {"taskId": t.task_id, "status": t.status}
        if method == "tasks/result" and t.status == "completed":
            payload["result"] = t.result
        if method == "tasks/result" and t.status == "failed":
            payload["error"] = t.error
        if t.status == "cancelled":
            payload["cancelReason"] = t.cancel_reason
        return _rpc_result(request_id, payload)

    if method == "tasks/cancel":
        task_id = params.get("taskId")
        t = get_task(task_id) if isinstance(task_id, str) else None
        if not t or t.session_id != session_id:
            return _rpc_error(request_id, -32602, "Invalid params", {"reason": "unknown_task"})
        invalid = cancellable_or_error(t)  # terminal -> -32602
        if invalid:
            return {"jsonrpc": "2.0", "id": request_id, "error": invalid}  # #C
        reason = params.get("reason") if isinstance(params.get("reason"), str) else None
        cancel_task(t.task_id, reason=reason)
        return _rpc_result(request_id, {"taskId": t.task_id, "status": "cancelled"})

    return _rpc_error(request_id, -32601, "Method not found")


def handle_cancel_notification(params: dict) -> None:
    """
    notifications/cancelled: explicit request-level cancellation signal.
    No response is sent for notifications.
    """
    req_id = params.get("requestId")  # #D
    if req_id is None:
        return

    inflight = INFLIGHT.get(str(req_id))
    if not inflight:
        return

    # initialize MUST NOT be cancelled; ignore cancel for that request id
    if inflight["method"] == "initialize":  # #E
        return

    inflight["cancelled"] = True

    # Bridge request-level cancel to task state when correlated
    t = get_task_by_request_id(str(req_id))
    if t and not is_terminal_task(t):
        cancel_task(t.task_id, reason=params.get("reason"))


def dispatch_rpc(request_obj: dict, session_id: Optional[str]) -> Optional[dict]:
    method = request_obj.get("method")
    params = request_obj.get("params") or {}
    request_id = request_obj.get("id")

    # 1) Lifecycle/session gate before business dispatch
    gate_err = enforce_lifecycle(method, session_id)
    if gate_err:
        if request_id is None:   # notification path
            return None
        return {"jsonrpc": "2.0", "id": request_id, "error": gate_err}  # #F

    # 2) notifications/cancelled is fire-and-forget
    if method == "notifications/cancelled":
        handle_cancel_notification(params)
        return None

    # 3) tasks/* control plane
    if method.startswith("tasks/"):
        return handle_tasks_method(method, params, request_id, session_id=session_id)

    # 4) business methods (example: tools/call)
    if request_id is not None:
        INFLIGHT[str(request_id)] = {"session_id": session_id, "method": method, "cancelled": False}

    try:
        if method == "tools/call":
            name = params.get("name")
            args = params.get("arguments") or {}

            # implementation-defined: route long jobs through task model
            if args.get("longRunning") is True:  # #G
                t = create_task(session_id=session_id, request_id=str(request_id), method=method)
                return _rpc_result(request_id, {"accepted": True, "taskId": t.task_id, "status": "running"})

            # short path
            return _rpc_result(request_id, {"ok": True, "tool": name})

        return _rpc_error(request_id, -32601, "Method not found")
    finally:
        if request_id is not None:
            cancelled = INFLIGHT.get(str(request_id), {}).get("cancelled", False)
            INFLIGHT.pop(str(request_id), None)
            if cancelled:
                # caller must suppress response emission for cancelled request
                return None  # #H

