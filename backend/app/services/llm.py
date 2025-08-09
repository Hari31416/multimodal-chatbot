"""LLM provider abstraction (MVP stub).

In production, implement calls to OpenAI or other providers here.
"""

import asyncio
from typing import Optional


async def text_completion(message: str, session_id: Optional[str] = None) -> str:
    # Stub: echo with simple transformation
    await asyncio.sleep(0)  # yield control
    return f"(stub) You said: {message}" + (
        f" [session {session_id}]" if session_id else ""
    )


async def vision_completion(prompt: str, image_bytes: bytes, filename: str) -> str:
    # Stub: just report file size & prompt
    kb = len(image_bytes) / 1024
    return f"(stub vision) Prompt: '{prompt}'. Image '{filename}' size: {kb:.1f} KB"
