from __future__ import annotations


from datetime import datetime
from pathlib import Path
import json
import shutil
import uuid
from typing import Any


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
        #     "title": "New chat",
        #     "files": ["IIT Patna AIML Project Guidelines (1) (1).pdf"],
        #     "active_model": null,
        #     "histories": {
        #         "OpenAI": [
        #             {"role": "user", "content": "List the two project names?",
        #              "created_at": "2026-07-25T21:10:12.000000"},
        #             {"role": "assistant",
        #              "content": "According to the Retrieved Context, the two project names are:\n\n1. Project 2 [1]\n2. Project 1 [2]", "created_at": "2026-07-25T21:10:12.000000"}
        #         ],
        #         "Anthropic": [
        #             {"role": "user", "content": "List the two project names?",
        #              "created_at": "2026-07-25T21:10:12.000000"},
        #             {"role": "assistant",
        #              "content": "The two project names are [1] and [2].", "created_at": "2026-07-25T21:10:12.000000"}
        #         ],
        #         "Gemini": [
        #             {"role": "user", "content": "List the two project names?",
        #              "created_at": "2026-07-25T21:10:12.000000"},
        #             {"role": "assistant",
        #              "content": "The two project names are Project 2 [2] and Project 1 [2].", "created_at": "2026-07-25T21:10:12.000000"}
        #         ]
        #     }
        # }
        "histories": {}
    }


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


def record_compare_turn(chat_id, query, answers):
    # histories: {
    #     "OpenAI":    [{role, content, created_at}, {role, content, created_at}, ...],
    #     "Anthropic": [...],
    #     "Gemini":    [...],
    # }
    record = load_chat(chat_id)
    histories = record.get("histories", {})

    for model, answer in answers.items():
        histories.setdefault(model, []).extend([{
            'role': 'user',
            'content': query,
            'created_at':  datetime.now().isoformat()
        }, {
            'role': 'assistant',
            'content': answer,
            'created_at':  datetime.now().isoformat()
        }])

    record["histories"] = histories
    save_chat(record)
    return record


def record_continue_turn(chat_id, model, query, answer):
    record = load_chat(chat_id)
    histories = record.get("histories", {})
    histories.setdefault(model, []).extend([{
        'role': 'user',
        'content': query,
        'created_at':  datetime.now().isoformat()
    }, {
        'role': 'assistant',
        'content': answer,
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


def add_file_to_chat(chat_id: str, filename: str) -> dict[str, Any]:
    record = load_chat(chat_id)
    files = record.setdefault("files", [])
    if filename not in files:
        files.append(filename)
    save_chat(record)
    return record


def delete_chat(chat_id: str) -> None:
    paths = chat_paths(chat_id)
    history_file = paths["history_file"]
    docs_dir = paths["docs_dir"]
    if history_file.exists():
        history_file.unlink()

    if docs_dir.exists() and docs_dir.is_dir():
        shutil.rmtree(docs_dir)

    from rag import clear_index

    clear_index(collection_name(chat_id))


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
