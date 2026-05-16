"""Общие утилиты для симуляции входящих Telegram update (Studio preview)."""

from __future__ import annotations

import base64
import hashlib
import os
from io import BytesIO


# Хранилище file_id -> BytesIO для переотправки файлов в превью
_preview_file_storage: dict[str, BytesIO] = {}


def get_preview_file(file_id: str) -> BytesIO | None:
    """Получить BytesIO по file_id (для переотправки файла)."""
    return _preview_file_storage.get(file_id)


def store_preview_file(file_id: str, data: BytesIO) -> None:
    """Сохранить BytesIO под file_id."""
    _preview_file_storage[file_id] = data


def upload_to_telegram_and_get_file_id(token: str, data: BytesIO, is_photo: bool = True) -> str | None:
    """Загрузить файл в Telegram и получить реальный file_id.
    
    Args:
        token: Токен бота Telegram
        data: BytesIO с содержимым файла
        is_photo: True если фото, False если документ
    
    Returns:
        file_id строка или None при ошибке
    """
    import requests
    
    if not token or token in ('YOUR_BOT_TOKEN', '0000000000:PASTE_YOUR_BOTFATHER_TOKEN_HERE', '__STUDIO_PREVIEW__'):
        return None
    
    try:
        base = f"https://api.telegram.org/bot{token}/"
        chat_id = 990000001  # Используем тот же chat_id что и в превью
        
        data.seek(0)
        files = {'photo' if is_photo else 'document': ('file.bin', data)}
        
        resp = requests.post(
            base + ('sendPhoto' if is_photo else 'sendDocument'),
            data={'chat_id': chat_id},
            files=files,
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        
        if not result.get('ok'):
            return None
            
        message = result.get('result', {})
        if is_photo:
            # Фото приходит как массив разных размеров, берём последний (самый большой)
            photos = message.get('photo', [])
            return photos[-1].get('file_id') if photos else None
        else:
            doc = message.get('document', {})
            return doc.get('file_id')
    except Exception:
        return None


def dsl_code_hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def ensure_bot_line(code: str) -> str:
    stripped = code.lstrip("\ufeff")
    for line in stripped.splitlines():
        s = line.strip()
        if s.startswith("бот "):
            return stripped
        if s:
            break
    return 'бот "__STUDIO_PREVIEW__"\n\n' + stripped


def message_update(text: str, chat_id: int, message_id: int = 1, user_id: int = 10001) -> dict:
    return {
        "update_id": message_id,
        "message": {
            "message_id": message_id,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Preview",
                "username": "preview_user",
            },
            "chat": {"id": chat_id, "type": "private"},
            "date": 0,
            "text": text,
        },
    }


def callback_update(callback_data: str, chat_id: int, *, user_id: int = 10001) -> dict:
    return {
        "update_id": 10_000 + abs(hash(callback_data)) % 100_000,
        "callback_query": {
            "id": f"cb_{abs(hash(callback_data)) % 10**9}",
            "from": {"id": user_id, "is_bot": False, "first_name": "Preview"},
            "message": {
                "message_id": 1,
                "chat": {"id": chat_id, "type": "private"},
                "from": {"id": 777000, "is_bot": True},
            },
            "chat_instance": "preview",
            "data": callback_data,
        },
    }


def _b64_to_bytesio(b64_data: str) -> BytesIO | None:
    """Convert base64 string to BytesIO."""
    if not b64_data:
        return None
    try:
        decoded = base64.b64decode(b64_data)
        return BytesIO(decoded)
    except Exception:
        return None


def photo_update(
    photo_payload: dict,
    chat_id: int,
    caption: str = "",
    message_id: int = 1,
    user_id: int = 10001,
    token: str | None = None,
) -> dict | None:
    """Build update for incoming photo (base64 -> BytesIO)."""
    if not photo_payload or not isinstance(photo_payload, dict):
        return None
    b64_data = photo_payload.get("data") or ""
    photo_bytes = _b64_to_bytesio(b64_data)
    if photo_bytes is None:
        return None
    
    # Если есть токен, пытаемся загрузить в Telegram и получить реальный file_id
    file_id = None
    if token:
        real_file_id = upload_to_telegram_and_get_file_id(token, photo_bytes, is_photo=True)
        if real_file_id:
            file_id = real_file_id
    
    # Если не удалось получить реальный file_id - используем превью-ид
    if not file_id:
        file_id = photo_payload.get("fileId") or f"preview_photo_{message_id}_{hash(photo_bytes.getvalue()) % 1000000}"
    
    # Сохраняем в хранилище для переотправки
    store_preview_file(file_id, photo_bytes)
    return {
        "update_id": message_id,
        "message": {
            "message_id": message_id,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Preview",
                "username": "preview_user",
            },
            "chat": {"id": chat_id, "type": "private"},
            "date": 0,
            "photo": [
                {
                    "file_id": file_id,
                    "file_unique_id": f"preview_{message_id}",
                    "file_size": photo_payload.get("fileSize") or len(photo_bytes.getvalue()),
                    "width": 640,
                    "height": 480,
                }
            ],
            "caption": caption,
            "_preview_photo_bytesio": photo_bytes,  # Internal: passed to executor as BytesIO
        },
    }


def document_update(
    document_payload: dict,
    chat_id: int,
    caption: str = "",
    message_id: int = 1,
    user_id: int = 10001,
    token: str | None = None,
) -> dict | None:
    """Build update for incoming document (base64 -> BytesIO)."""
    if not document_payload or not isinstance(document_payload, dict):
        return None
    b64_data = document_payload.get("data") or ""
    doc_bytes = _b64_to_bytesio(b64_data)
    if doc_bytes is None:
        return None
    
    # Если есть токен, пытаемся загрузить в Telegram и получить реальный file_id
    file_id = None
    if token:
        real_file_id = upload_to_telegram_and_get_file_id(token, doc_bytes, is_photo=False)
        if real_file_id:
            file_id = real_file_id
    
    # Если не удалось получить реальный file_id - используем превью-ид
    if not file_id:
        file_id = document_payload.get("fileId") or f"preview_doc_{message_id}_{hash(doc_bytes.getvalue()) % 1000000}"
    
    # Сохраняем в хранилище для переотправки
    store_preview_file(file_id, doc_bytes)
    return {
        "update_id": message_id,
        "message": {
            "message_id": message_id,
            "from": {
                "id": user_id,
                "is_bot": False,
                "first_name": "Preview",
                "username": "preview_user",
            },
            "chat": {"id": chat_id, "type": "private"},
            "date": 0,
            "document": {
                "file_id": file_id,
                "file_unique_id": f"preview_doc_{message_id}",
                "file_name": document_payload.get("fileName") or "file.bin",
                "mime_type": document_payload.get("mimeType") or "application/octet-stream",
                "file_size": document_payload.get("fileSize") or len(doc_bytes.getvalue()),
            },
            "caption": caption,
            "_preview_document_bytesio": doc_bytes,  # Internal: passed to executor as BytesIO
        },
    }
