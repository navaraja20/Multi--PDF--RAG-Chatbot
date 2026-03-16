from __future__ import annotations

import logging
import time
import random
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Callable, Iterable, Optional, Tuple

import requests
from bs4 import BeautifulSoup, SoupStrainer

USER_AGENT = "Mozilla/5.0 (RAG research dataset builder)"
DEFAULT_HEADERS = {"User-Agent": USER_AGENT}
REQUEST_DELAY_RANGE = (2.0, 3.0)
MEDIAWIKI_HOST_SUFFIXES = (
    "wikipedia.org",
    "fandom.com",
    "pcgamingwiki.com",
)

logger = logging.getLogger(__name__)


def _looks_mediawiki(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return any(host.endswith(suffix) for suffix in MEDIAWIKI_HOST_SUFFIXES)


def _mediawiki_api_endpoint(url: str) -> Optional[Tuple[str, str]]:
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        return None
    scheme = parsed.scheme or "https"
    api_base = f"{scheme}://{host}/w/api.php"
    slug = parsed.path.rstrip("/").split("/")[-1]
    if not slug:
        return None
    slug = unquote(slug)
    return api_base, slug


def _wrap_with_title(html: str, title: Optional[str]) -> str:
    if not title:
        return html
    return f"<html><head><title>{title}</title></head><body>{html}</body></html>"


def _fetch_mediawiki_html(url: str, session: requests.Session, timeout: int) -> Optional[str]:
    endpoint_slug = _mediawiki_api_endpoint(url)
    if not endpoint_slug:
        return None
    endpoint, slug = endpoint_slug
    params = {
        "action": "parse",
        "page": slug,
        "format": "json",
        "prop": "text|displaytitle",
        "formatversion": 2,
        "redirects": 1,
    }
    try:
        resp = session.get(endpoint, headers=DEFAULT_HEADERS, params=params, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        parse_obj = data.get("parse", {})
        html = parse_obj.get("text")
        title = parse_obj.get("displaytitle") or parse_obj.get("title")
        if not title or str(title).strip().lower() == "contents":
            title = slug.replace("_", " ").strip() or slug
        return _wrap_with_title(html, title)
    except Exception as exc:
        logger.warning("MediaWiki API fetch failed for %s: %s", url, exc)
        return None


def fetch_html(url: str, session: Optional[requests.Session] = None, timeout: int = 15) -> Optional[str]:
    sess = session or requests.Session()
    if _looks_mediawiki(url):
        html = _fetch_mediawiki_html(url, sess, timeout)
        if html:
            return html
    try:
        resp = sess.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        logger.warning("Failed to fetch %s: %s", url, exc)
        return None


def _drop_unwanted_nodes(soup: BeautifulSoup) -> None:
    for tag in soup([
        "script",
        "style",
        "noscript",
        "nav",
        "header",
        "footer",
        "form",
        "aside",
        "svg",
    ]):
        tag.decompose()


def _choose_container(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
    for selector in ("article", "main", "div#content", "body"):
        node = soup.select_one(selector)
        if node:
            return node
    return soup


def _title_from_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    parsed = urlparse(url)
    slug = parsed.path.rstrip("/").split("/")[-1]
    if not slug:
        return None
    slug = unquote(slug)
    slug = slug.replace("_", " ").replace("-", " ").strip()
    return slug or None


def extract_text_and_title(html: str, url: Optional[str] = None) -> Tuple[str, str]:
    strainer = SoupStrainer(["body", "article", "main", "div"])
    soup = BeautifulSoup(html, "lxml", parse_only=strainer)
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    if not title:
        first_heading = soup.find(["h1", "h2"])
        if first_heading and first_heading.get_text(strip=True):
            title = first_heading.get_text(strip=True)
    if not title:
        url_title = _title_from_url(url)
        if url_title:
            title = url_title
    if not title:
        title = "page"
    _drop_unwanted_nodes(soup)
    container = _choose_container(soup)

    chunks: list[str] = []
    if container:
        for el in container.find_all(["h1", "h2", "h3", "p", "li"]):
            text = el.get_text(separator=" ", strip=True)
            if text:
                chunks.append(text)
    if not chunks:
        fallback = soup.get_text(separator="\n", strip=True)
        return fallback, title
    return "\n".join(chunks), title


def rate_limit_sleep(delay_range: Tuple[float, float] = REQUEST_DELAY_RANGE) -> None:
    low, high = delay_range
    time.sleep(random.uniform(low, high))


def save_raw_text(
    text: str,
    title: str,
    output_dir: Path,
    make_unique: Optional[Callable[[Path], Path]] = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(title) or "page"
    path = output_dir / f"{safe_name}.txt"
    if make_unique:
        path = make_unique(path)
    path.write_text(text, encoding="utf-8")
    return path


def _safe_filename(title: str) -> str:
    cleaned = "_".join(title.split())
    cleaned = "".join(ch for ch in cleaned if ch.isalnum() or ch in {"_", "-"})
    return cleaned[:120]


def sanitize_title(title: str, fallback: str = "page") -> str:
    safe = _safe_filename(title)
    return safe if safe else fallback


def iter_urls(urls: Iterable[str]) -> Iterable[str]:
    for url in urls:
        if url and url.strip():
            yield url.strip()


__all__ = [
    "fetch_html",
    "extract_text_and_title",
    "rate_limit_sleep",
    "save_raw_text",
    "sanitize_title",
    "iter_urls",
    "DEFAULT_HEADERS",
    "USER_AGENT",
    "REQUEST_DELAY_RANGE",
]
