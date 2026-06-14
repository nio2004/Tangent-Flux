import base64

from app.core.config import get_settings


def data_url_for_image(content: bytes, content_type: str) -> str:
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def ingest_image(content: bytes, content_type: str, filename: str) -> str:
    settings = get_settings()
    data_url = data_url_for_image(content, content_type)
    if not settings.openai_api_key:
        return _fallback_description(filename)
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(
            model=settings.openai_vision_model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Analyze this uploaded Tangent-Flux project image. "
                                "Describe only what is visually grounded in the image. Include: "
                                "1. visible title or text, 2. diagram/UI/architecture elements, "
                                "3. relationships or flow arrows, 4. project implications. "
                                "If text is unreadable, say so. Return 4-7 concise sentences."
                            ),
                        },
                        {"type": "input_image", "image_url": data_url},
                    ],
                }
            ],
        )
        text = getattr(response, "output_text", None)
        return _normalize_description(text, filename)
    except Exception as exc:
        return f"{_fallback_description(filename)} Vision ingestion fallback reason: {exc}"


def _normalize_description(text: str | None, filename: str) -> str:
    if not text:
        return _fallback_description(filename)
    cleaned = " ".join(text.split())
    if len(cleaned) < 20:
        return _fallback_description(filename)
    return cleaned[:1200]


def _fallback_description(filename: str) -> str:
    return (
        f"Uploaded image '{filename}' was attached as a project artifact. "
        "Automatic visual extraction was unavailable, so this image should be reviewed manually."
    )
