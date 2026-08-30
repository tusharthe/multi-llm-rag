from __future__ import annotations
from collections import defaultdict
from typing import TYPE_CHECKING, TypedDict
from datetime import datetime
from pathlib import Path
import json
import shutil
import uuid

if TYPE_CHECKING:
    from streamlit.runtime.uploaded_file_manager import UploadedFile

from logger import logger
from rag import build_index, clear_index
from ingestion import load_and_split
from prompts import format_sources


BASE_DIR = Path(__file__).resolve().parent
CHAT_DIR = BASE_DIR / "chats"
DOCS_DIR = BASE_DIR / "docs"

CHAT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def generate_chat_id() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    return f"{timestamp}_{suffix}"


def collection_name(chat_id: str) -> str:
    return f"chat_{chat_id}"


def chat_paths(chat_id: str) -> dict[str, Path]:
    return {
        "history_file": CHAT_DIR / f"{chat_id}.json",
        "docs_dir": DOCS_DIR / chat_id,
    }


def build_empty_record(chat_id: str, title: str = "New chat") -> dict[str, Any]:
    now = datetime.now().isoformat()
    return {
        "chat_id": chat_id,
        "collection_name": collection_name(chat_id),
        "created_at": now,
        "updated_at": now,
        "title": title.strip() or "New chat",
        "files": [],
        "active_model": None,
        "preferences": {},
        # histories: dict[label -> list[turn]]
        # histories: {
        #     "OpenAI":    [{role, content, created_at}, {role, content, created_at}, ...],
        #     "Anthropic": [...],
        #     "Gemini":    [...],
        # }
        # SAMPLE JSON
        # {
        #     "chat_id": "20260725_210704_b3446bd3",
        #     "collection_name": "chat_20260725_210704_b3446bd3",
        #     "created_at": "2026-07-25T21:07:04.000000",
        #     "updated_at": "2026-07-25T21:10:12.000000",
        #     "preferences": dict[str, str],
        #     "title": "New chat",
        #     "files": ["IIT Patna AIML Project Guidelines (1) (1).pdf"],
        #     "active_model": null,
        #     "histories": {
        #         "OpenAI": [
        #             {"role": "user", "content": "List the two project names?",  turn_id: "a1b2c3",
        #              "created_at": "2026-07-25T21:10:12.000000"},
        #             {"role": "assistant",
        #              "content": "According to the Retrieved Context, the two project names are:\n\n1. Project 2 [1]\n2. Project 1 [2]", "created_at": "2026-07-25T21:10:12.000000"}
        #         ],
        #         "Anthropic": [
        #             {"role": "user", "content": "List the two project names?",  turn_id: "a1b2c3",
        #              "created_at": "2026-07-25T21:10:12.000000"},
        #             {"role": "assistant",
        #              "content": "The two project names are [1] and [2].", "created_at": "2026-07-25T21:10:12.000000"}
        #         ],
        #         "Gemini": [
        #             {"role": "user", "content": "List the two project names?",  turn_id: "a1b2c3",
        #              "created_at": "2026-07-25T21:10:12.000000"},
        #             {"role": "assistant",
        #              "content": "The two project names are Project 2 [2] and Project 1 [2].", "created_at": "2026-07-25T21:10:12.000000"}
        #         ]
        #     }
        # }
        "histories": {}
    }


def group_turn_ids(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Merge all models' turns into ONE timeline, grouped by turn_id.

    Returns a list of turn groups sorted by creation time. Each group:
    {
        "turn_id":  str,
        "created_at": str (isoformat),
        "query":    str | None,
        "answers":  {model_label: answer_text},   # only models that answered
    }

    Old chats without ``turn_id`` fall back to per-item synthetic groups so
    nothing crashes; new chats group perfectly by shared turn_id.
    """
    histories = record.get("histories", {})
    groups: dict[str, dict[str, Any]] = {}

    for model, turns in histories.items():
        for item in turns:
            turn_id = item.get("turn_id")
            if turn_id is None:
                turn_id = (
                    f"legacy:{item['role']}:{item['created_at']}"
                    f":{item['content']}"
                )

            group = groups.setdefault(turn_id, {
                "turn_id": turn_id,
                "created_at": item["created_at"],
                "query": None,
                "sources": None,
                "answers": {},
            })

            if item["role"] == "user":
                group["query"] = item["content"]
                group["sources"] = item.get("sources")
                if item["created_at"] < group["created_at"]:
                    group["created_at"] = item["created_at"]
            else:
                group["answers"][model] = item["content"]

    return sorted(groups.values(), key=lambda g: g["created_at"])


def delete_turn(chat_id: str, turn_id: str) -> dict[str, Any]:
    """Remove a single turn (all dicts with this turn_id) from every model.

    Used by the Compare re-run: the last single-model turn is replaced by a
    fresh all-model turn so the question does not appear duplicated.
    Also clears ``preferences[turn_id]`` if present.
    """
    record = load_chat(chat_id)
    histories = record.get("histories", {})
    for model in list(histories.keys()):
        histories[model] = [
            t for t in histories[model] if t.get("turn_id") != turn_id
        ]
    record["histories"] = histories
    prefs = record.get("preferences")
    if isinstance(prefs, dict) and turn_id in prefs:
        del prefs[turn_id]
        record["preferences"] = prefs
    save_chat(record)
    return record


def save_chat(record: dict[str, Any]) -> None:
    record["updated_at"] = datetime.now().isoformat()
    paths = chat_paths(record["chat_id"])
    paths["history_file"].write_text(
        json.dumps(record, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def new_chat(title: str = "New chat") -> dict[str, Any]:
    chat_id = generate_chat_id()
    paths = chat_paths(chat_id)
    paths["docs_dir"].mkdir(parents=True, exist_ok=True)

    record = build_empty_record(chat_id, title=title)
    save_chat(record)
    return record


def load_chat(chat_id: str) -> dict[str, Any]:
    history_file = chat_paths(chat_id)["history_file"]
    if not history_file.exists():
        raise FileNotFoundError(f"Chat not found: {chat_id}")
    return json.loads(history_file.read_text(encoding="utf-8"))


def list_chats() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for history_file in CHAT_DIR.glob("*.json"):
        try:
            record = json.loads(history_file.read_text(encoding="utf-8"))
            items.append(
                {
                    "chat_id": record["chat_id"],
                    "title": record.get("title", "New chat"),
                    "created_at": record.get("created_at"),
                    "updated_at": record.get("updated_at"),
                    "active_model": record.get("active_model"),
                    "file_count": len(record.get("files", [])),
                    # "message_count": len(record.get("histories", [])),
                }
            )
        except Exception:
            continue

    items.sort(key=lambda x: x.get("updated_at") or "", reverse=True)
    return items


def record_compare_turn(chat_id, query, answers, docs=None):
    # histories: {
    #     "OpenAI":    [{role, content, turn_id, created_at}, ...],
    #     "Anthropic": [...],
    #     "Gemini":    [...],
    # }
    record = load_chat(chat_id)
    histories = record.get("histories", {})
    turn_id = str(uuid.uuid4())
    sources = format_sources(docs) if docs else None

    for model, answer in answers.items():
        histories.setdefault(model, []).extend([{
            'role': 'user',
            'content': query,
            'turn_id': turn_id,
            'sources': sources,
            'created_at':  datetime.now().isoformat()
        }, {
            'role': 'assistant',
            'content': answer,
            'turn_id': turn_id,
            'created_at':  datetime.now().isoformat()
        }])

    record["histories"] = histories
    record.setdefault("preferences", {})
    save_chat(record)
    return record


def record_continue_turn(chat_id, model, query, answer, docs=None):
    record = load_chat(chat_id)
    turn_id = str(uuid.uuid4())
    histories = record.get("histories", {})
    sources = format_sources(docs) if docs else None
    histories.setdefault(model, []).extend([{
        'role': 'user',
        'content': query,
        'turn_id': turn_id,
        'sources': sources,
        'created_at':  datetime.now().isoformat()
    }, {
        'role': 'assistant',
        'content': answer,
        'turn_id': turn_id,
        'created_at':  datetime.now().isoformat()
    }])

    record["active_model"] = model

    save_chat(record)
    return record


def rename_chat(chat_id: str, title: str) -> dict[str, Any]:
    record = load_chat(chat_id)
    record["title"] = title.strip() or "New chat"
    save_chat(record)
    return record


def set_active_model(chat_id: str, model: str | None) -> dict[str, Any]:
    record = load_chat(chat_id)
    record["active_model"] = model
    save_chat(record)
    return record


def get_active_model(chat_id: str) -> str:
    record = load_chat(chat_id)
    return record["active_model"]


def add_file_to_chat(chat_id: str, filename: str) -> dict[str, Any]:
    record = load_chat(chat_id)
    files = record.setdefault("files", [])
    if filename not in files:
        files.append(filename)
    save_chat(record)
    return record


def is_chat_empty(record: dict[str, Any]) -> bool:
    return not record.get("histories") and not record.get("files")


def _remove_partial_file(file_path: Path) -> None:
    """Delete a half-written upload so disk and index don't drift apart."""
    if not file_path.exists():
        return

    try:
        file_path.unlink()
    except OSError:
        logger.warning(
            "Failed to delete partial file '%s'", file_path, exc_info=True
        )


def _purge_chat_storage(chat_id: str) -> None:
    """Remove a chat's vectors and its stored documents.

    Shared by ``clear_chat_documents`` (keeps the conversation) and
    ``delete_chat`` (removes it too).
    """
    clear_index(collection_name(chat_id))

    docs_dir = chat_paths(chat_id)["docs_dir"]
    if docs_dir.is_dir():
        shutil.rmtree(docs_dir)


def clear_chat_documents(chat_id: str) -> dict[str, Any]:
    """Drop a chat's knowledge base but KEEP the conversation.

    Resets ``files`` so ``upload_file`` -- which dedupes against the record --
    will accept the same documents again.
    """
    _purge_chat_storage(chat_id)

    record = load_chat(chat_id)
    record["files"] = []
    save_chat(record)
    return record


def delete_chat(chat_id: str) -> None:
    """Remove a chat entirely -- conversation, documents and vectors."""
    _purge_chat_storage(chat_id)

    history_file = chat_paths(chat_id)["history_file"]
    if history_file.exists():
        history_file.unlink()


class FileUploadResult(TypedDict):
    ok: bool
    error: str | None


def upload_file(uploaded_files: list[UploadedFile], chat_id: str) -> dict[str, FileUploadResult]:
    logger.info("File upload started for chat_id=%s", chat_id)

    upload_path = Path(chat_paths(chat_id)["docs_dir"])
    upload_path.mkdir(parents=True, exist_ok=True)

    known_names = set(load_chat(chat_id).get("files", []))

    results: dict[str, FileUploadResult] = {}

    for uploaded_file in uploaded_files:
        original_name = uploaded_file.name

        if original_name in known_names:
            logger.info("Skipping duplicate file '%s'", original_name)
            results[original_name] = {
                "ok": False,
                "error": f"'{original_name}' has already been uploaded.",
            }
            continue

        file_path = upload_path / original_name

        try:
            file_path.write_bytes(uploaded_file.getbuffer())

            chunks = load_and_split(file_path)
            build_index(chunks, collection_name(chat_id))
            add_file_to_chat(chat_id, original_name)

            known_names.add(original_name)
            results[original_name] = {"ok": True, "error": None}

        except Exception:
            logger.exception("Failed to upload file '%s'", original_name)
            _remove_partial_file(file_path)
            results[original_name] = {
                "ok": False,
                "error": f"Failed to upload '{original_name}'. Please try again."
            }

    logger.info("File upload end result: %s", results)
    return results


if __name__ == "__main__":

    # chat = new_chat(title="text chat")

    data = {
        "query": "List the two project names?",
        "collection": "chat_test",
        "docs": [],
        "answers": {
            "Anthropic": "The two project names are [1] and [2].",
            "Gemini": "The two project names are Project 2 [2] and Project 1 [2].",
            "OpenAI": (
                "According to the Retrieved Context, the two project names are:\n\n"
                "1. Project 2 [1]\n"
                "2. Project 1 [2]"
            ),
        },
    }

    answer = 'Ans here record_continue_turn'

    record = record_compare_turn(
        chat_id='20260725_210704_b3446bd3', query=data['query'], answers=data['answers'])

    record = record_continue_turn(
        chat_id='20260725_210704_b3446bd3', model='OpenAI', query=data['query'], answer=answer)
