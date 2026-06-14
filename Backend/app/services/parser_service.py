import re
from dataclasses import dataclass
from html import unescape
from urllib.parse import urlparse

import requests


class ParseError(ValueError):
    pass


@dataclass
class ParsedResource:
    source_type: str
    title: str
    clean_content: str
    source_url: str | None = None
    metadata: dict | None = None


def is_url(value: str) -> bool:
    parsed = urlparse(normalize_url(value))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def looks_like_bare_domain(value: str) -> bool:
    candidate = value.strip()
    return bool(
        re.match(r"^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}([/:?#].*)?$", candidate, re.I)
        and not re.search(r"\s", candidate)
    )


def normalize_url(value: str) -> str:
    candidate = value.strip()
    if looks_like_bare_domain(candidate):
        return f"https://{candidate}"
    return candidate


def detect_source_type(value: str) -> str:
    lowered = value.strip().lower()
    if is_url(lowered) and "arxiv.org" in lowered:
        return "arxiv"
    if is_url(lowered) and "reddit.com" in lowered:
        return "reddit"
    if is_url(lowered):
        return "webpage"
    return "raw_text"


def parse_input(value: str, title: str | None = None) -> ParsedResource:
    normalized_value = normalize_url(value)
    source_type = detect_source_type(normalized_value)
    if source_type == "raw_text":
        return parse_raw_text(value, title)
    if source_type == "arxiv":
        return parse_arxiv(normalized_value, title)
    if source_type == "reddit":
        return parse_reddit(normalized_value, title)
    return parse_webpage(normalized_value, title)


def parse_raw_text(value: str, title: str | None = None) -> ParsedResource:
    content = normalize_whitespace(value)
    if len(content) < 20:
        raise ParseError("Raw text must be at least 20 characters.")
    return ParsedResource("raw_text", title or "Raw idea dump", content, None, {})


def parse_webpage(url: str, title: str | None = None) -> ParsedResource:
    try:
        response = requests.get(url, timeout=12, headers={"User-Agent": "TangentFlux/0.1"})
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ParseError(f"Could not fetch webpage: {exc}") from exc

    clean = None
    parser = "html_text"
    try:
        import trafilatura

        clean = trafilatura.extract(response.text)
        if clean:
            parser = "trafilatura"
    except Exception:
        clean = None

    fallback_text = html_to_visible_text(response.text)
    if len(fallback_text) > len(normalize_whitespace(clean or "")):
        clean = fallback_text
        parser = "html_text"
    else:
        clean = normalize_whitespace(clean or "")

    if len(clean) < 200:
        raise ParseError(
            "The page was reachable, but it did not expose enough readable text to save as a resource. "
            "Paste a longer excerpt or use a more specific article/document URL."
        )
    page_title = title or _html_title(response.text) or urlparse(url).netloc
    return ParsedResource("webpage", page_title, clean, url, {"parser": parser})


def parse_arxiv(url: str, title: str | None = None) -> ParsedResource:
    try:
        response = requests.get(url, timeout=12, headers={"User-Agent": "TangentFlux/0.1"})
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ParseError(f"Could not fetch arXiv page: {exc}") from exc

    html = response.text
    page_title = title or _html_title(html) or "arXiv paper"
    abstract_match = re.search(r'<blockquote class="abstract[^"]*">\s*<span[^>]*>Abstract:</span>(.*?)</blockquote>', html, re.S)
    abstract = re.sub("<[^<]+?>", " ", abstract_match.group(1)) if abstract_match else re.sub("<[^<]+?>", " ", html)
    clean = normalize_whitespace(f"{page_title}. {abstract}")
    if len(clean) < 100:
        raise ParseError("The arXiv page did not expose enough abstract text to save as a resource.")
    return ParsedResource("arxiv", page_title, clean, url, {"parser": "arxiv"})


def parse_reddit(url: str, title: str | None = None) -> ParsedResource:
    json_url = url.rstrip("/") + ".json"
    try:
        response = requests.get(json_url, timeout=12, headers={"User-Agent": "TangentFlux/0.1"})
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        raise ParseError(f"Could not fetch Reddit JSON: {exc}") from exc

    parts: list[str] = []
    post_title = title or "Reddit thread"
    try:
        post = payload[0]["data"]["children"][0]["data"]
        post_title = title or post.get("title") or post_title
        parts.append(post.get("selftext") or post.get("title") or "")
        comments = payload[1]["data"]["children"][:5]
        for comment in comments:
            body = comment.get("data", {}).get("body")
            if body:
                parts.append(body)
    except Exception:
        pass
    clean = normalize_whitespace(" ".join(parts))
    if len(clean) < 100:
        raise ParseError("The Reddit thread did not expose enough readable text to save as a resource.")
    return ParsedResource("reddit", post_title, clean, url, {"parser": "reddit_json"})


def _html_title(html: str) -> str | None:
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if not match:
        return None
    return normalize_whitespace(re.sub("<[^<]+?>", " ", match.group(1)))


def html_to_visible_text(html: str) -> str:
    stripped = re.sub(r"(?is)<(script|style|noscript|svg|canvas|template|head|footer)[^>]*>.*?</\1>", " ", html)
    stripped = re.sub(r"(?is)<!--.*?-->", " ", stripped)
    stripped = re.sub(r"(?is)<br\s*/?>|</p>|</div>|</li>|</h[1-6]>", " ", stripped)
    stripped = re.sub(r"(?is)<[^>]+>", " ", stripped)
    return normalize_whitespace(unescape(stripped))

