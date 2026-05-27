"""
Rich content extractors for HTML pages.

Each extractor takes a BeautifulSoup-parsed document plus the page URL
and returns a structured slice of the result. Extractors are deliberately
defensive — bad input must not crash the pipeline.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .models import ContactInfo, LinkInfo, MediaAsset, PageMetadata, TableData


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(
    r"(?:(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{3,4})"
)

SOCIAL_DOMAINS = {
    "twitter": ("twitter.com", "x.com", "nitter.net"),
    "facebook": ("facebook.com", "fb.com"),
    "instagram": ("instagram.com",),
    "linkedin": ("linkedin.com",),
    "youtube": ("youtube.com", "youtu.be"),
    "tiktok": ("tiktok.com",),
    "github": ("github.com",),
    "reddit": ("reddit.com", "redd.it"),
    "pinterest": ("pinterest.com",),
    "discord": ("discord.com", "discord.gg"),
    "telegram": ("t.me", "telegram.me"),
    "whatsapp": ("wa.me", "whatsapp.com"),
    "medium": ("medium.com",),
    "mastodon": ("mastodon.social", "mastodon.online"),
}

NOISY_TAGS = ("script", "style", "noscript", "template", "iframe")
LAYOUT_TAGS = ("nav", "footer", "header", "aside")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_soup(html: str) -> BeautifulSoup:
    """Parse with lxml, fall back to html.parser if lxml is missing."""
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def _domain(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def _classify_link(href: str, page_domain: str) -> Tuple[str, str]:
    """Return (kind, domain) for a hyperlink."""
    if not href:
        return "anchor", ""
    if href.startswith("#"):
        return "anchor", page_domain
    if href.startswith("mailto:"):
        return "email", ""
    if href.startswith("tel:"):
        return "tel", ""
    if href.startswith("javascript:"):
        return "javascript", ""

    domain = _domain(href)
    if not domain:
        return "internal", page_domain

    for _, hosts in SOCIAL_DOMAINS.items():
        if any(domain.endswith(h) for h in hosts):
            return "social", domain

    if page_domain and (domain == page_domain or domain.endswith("." + page_domain)):
        return "internal", domain
    return "external", domain


def _abs(url: str, base: str) -> str:
    try:
        return urljoin(base, url)
    except Exception:
        return url


# ---------------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------------

def extract_metadata(soup: BeautifulSoup, url: str) -> PageMetadata:
    md = PageMetadata()

    title = soup.find("title")
    if title:
        md.title = title.get_text(strip=True)[:300]

    desc = soup.find("meta", attrs={"name": "description"})
    if desc and desc.get("content"):
        md.description = desc["content"].strip()[:500]

    canonical = soup.find("link", attrs={"rel": "canonical"})
    if canonical and canonical.get("href"):
        md.canonical_url = _abs(canonical["href"], url)

    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        md.language = html_tag["lang"][:10]

    favicon = soup.find("link", attrs={"rel": re.compile(r"icon", re.I)})
    if favicon and favicon.get("href"):
        md.favicon = _abs(favicon["href"], url)

    keywords = soup.find("meta", attrs={"name": "keywords"})
    if keywords and keywords.get("content"):
        md.keywords = [k.strip() for k in keywords["content"].split(",") if k.strip()][:30]

    for meta in soup.find_all("meta"):
        prop = (meta.get("property") or "").lower()
        name = (meta.get("name") or "").lower()
        content = meta.get("content")
        if not content:
            continue
        if prop.startswith("og:"):
            md.open_graph[prop[3:]] = content[:500]
        elif name.startswith("twitter:"):
            md.twitter_card[name[8:]] = content[:500]

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                md.schema_org.extend(d for d in data if isinstance(d, dict))
            elif isinstance(data, dict):
                md.schema_org.append(data)
        except Exception:
            continue
        if len(md.schema_org) >= 10:
            break

    return md


def extract_text(soup: BeautifulSoup, max_chars: int = 20000) -> Tuple[str, int, float]:
    """Return (clean_text, word_count, reading_time_minutes)."""
    cleaned = BeautifulSoup(str(soup), "html.parser") if soup else None
    if cleaned is None:
        return "", 0, 0.0
    for tag in cleaned(NOISY_TAGS):
        tag.decompose()

    article = cleaned.find("article") or cleaned.find("main") or cleaned
    text = re.sub(r"\s+", " ", article.get_text(separator=" ")).strip()
    if len(text) < 200:
        text = re.sub(r"\s+", " ", cleaned.get_text(separator=" ")).strip()

    text = text[:max_chars]
    words = len(text.split())
    reading_time = round(words / 200.0, 2) if words else 0.0
    return text, words, reading_time


def extract_images(soup: BeautifulSoup, url: str, limit: int = 200) -> List[MediaAsset]:
    images: List[MediaAsset] = []
    seen: set = set()
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
        if not src or src.startswith("data:"):
            continue
        absolute = _abs(src, url)
        if absolute in seen:
            continue
        seen.add(absolute)

        width = img.get("width")
        height = img.get("height")
        try:
            width = int(width) if width else None
        except ValueError:
            width = None
        try:
            height = int(height) if height else None
        except ValueError:
            height = None

        images.append(
            MediaAsset(
                src=absolute,
                alt=(img.get("alt") or "")[:200] or None,
                title=(img.get("title") or "")[:200] or None,
                width=width,
                height=height,
                srcset=img.get("srcset") or None,
                media_type="image",
            )
        )
        if len(images) >= limit:
            break

    for og in soup.find_all("meta", attrs={"property": re.compile(r"og:image", re.I)}):
        content = og.get("content")
        if content:
            absolute = _abs(content, url)
            if absolute not in seen:
                seen.add(absolute)
                images.append(MediaAsset(src=absolute, media_type="image"))
                if len(images) >= limit:
                    break
    return images


def extract_videos(soup: BeautifulSoup, url: str, limit: int = 50) -> List[MediaAsset]:
    videos: List[MediaAsset] = []
    seen: set = set()

    for vid in soup.find_all("video"):
        src = vid.get("src") or ""
        if not src:
            source = vid.find("source")
            if source:
                src = source.get("src", "")
        if not src:
            continue
        absolute = _abs(src, url)
        if absolute in seen:
            continue
        seen.add(absolute)
        videos.append(MediaAsset(src=absolute, media_type="video", title=(vid.get("title") or None)))

    for iframe in soup.find_all("iframe"):
        src = iframe.get("src") or ""
        if not src:
            continue
        if any(host in src for host in ("youtube.com", "youtu.be", "vimeo.com", "dailymotion.com")):
            absolute = _abs(src, url)
            if absolute not in seen:
                seen.add(absolute)
                videos.append(MediaAsset(src=absolute, media_type="video", title=(iframe.get("title") or None)))
        if len(videos) >= limit:
            break

    return videos


def extract_links(soup: BeautifulSoup, url: str, limit: int = 500) -> Dict[str, List[LinkInfo]]:
    """Return links grouped by kind."""
    page_domain = _domain(url)
    grouped: Dict[str, List[LinkInfo]] = {
        "internal": [],
        "external": [],
        "social": [],
        "email": [],
        "tel": [],
    }
    seen: set = set()

    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href:
            continue
        kind, domain = _classify_link(href, page_domain)
        if kind in ("anchor", "javascript"):
            continue

        absolute = href if href.startswith(("mailto:", "tel:")) else _abs(href, url)
        key = (kind, absolute)
        if key in seen:
            continue
        seen.add(key)

        link = LinkInfo(
            href=absolute,
            text=(a.get_text(strip=True) or "")[:200],
            title=(a.get("title") or "")[:200] or None,
            rel=(a.get("rel") and " ".join(a["rel"]) if a.get("rel") else None),
            kind=kind,
            domain=domain or None,
        )
        bucket = grouped.setdefault(kind, [])
        bucket.append(link)

        total = sum(len(v) for v in grouped.values())
        if total >= limit:
            break
    return grouped


def extract_contacts(soup: BeautifulSoup, html: str, links: Optional[Dict[str, List[LinkInfo]]] = None) -> ContactInfo:
    """Extract emails, phones, social handles, basic addresses."""
    info = ContactInfo()

    # Emails: combine raw HTML scan + mailto links + obfuscated patterns
    raw_emails = set(EMAIL_RE.findall(html))
    raw_emails = {e for e in raw_emails if not e.lower().endswith((".png", ".jpg", ".gif", ".css", ".js", ".svg", ".woff"))}

    # Common obfuscations: " at " / " [at] " / " (at) "
    deobfuscated = re.findall(r"([A-Za-z0-9._%+-]+)\s*(?:\[at\]|\(at\)|\s+at\s+)\s*([A-Za-z0-9.-]+)\s*(?:\[dot\]|\(dot\)|\s+dot\s+)\s*([A-Za-z]{2,})", html, flags=re.IGNORECASE)
    for u, d, t in deobfuscated:
        raw_emails.add(f"{u}@{d}.{t}")

    # Phones from visible text
    for tag in soup(NOISY_TAGS):
        tag.decompose()
    page_text = soup.get_text(" ", strip=True)
    raw_phones = set()
    for match in PHONE_RE.findall(page_text):
        digits = re.sub(r"\D", "", match)
        if 7 <= len(digits) <= 15:
            raw_phones.add(match.strip())

    # Add mailto: / tel: from links if provided
    if links:
        for link in links.get("email", []):
            email = link.href.replace("mailto:", "").split("?")[0].strip()
            if email:
                raw_emails.add(email)
        for link in links.get("tel", []):
            phone = link.href.replace("tel:", "").strip()
            if phone:
                raw_phones.add(phone)

    info.emails = sorted(raw_emails)[:50]
    info.phones = sorted(raw_phones)[:50]

    # Social handles
    handles: Dict[str, set] = {}
    if links:
        for link in links.get("social", []):
            for platform, hosts in SOCIAL_DOMAINS.items():
                if any(link.href.lower().find(h) != -1 for h in hosts):
                    path = urlparse(link.href).path.strip("/")
                    if path and "/" not in path.rstrip("/"):
                        handles.setdefault(platform, set()).add(path.rstrip("/"))
                    elif path:
                        handles.setdefault(platform, set()).add(path.split("/")[0])
                    break
    info.social_handles = {k: sorted(v)[:20] for k, v in handles.items() if v}

    # Addresses (heuristic): postal-code patterns + lines containing "Address:"
    address_candidates = []
    for line in page_text.splitlines():
        line = line.strip()
        if not line or len(line) > 200:
            continue
        if re.match(r"^\s*Address\s*[:：]", line, re.I):
            address_candidates.append(line[:200])
        elif re.search(r"\b\d{5}(?:-\d{4})?\b", line) and any(w in line.lower() for w in ("street", "ave", "road", "blvd", "suite", "drive")):
            address_candidates.append(line[:200])
        if len(address_candidates) >= 10:
            break
    info.addresses = address_candidates

    return info


def extract_tables(soup: BeautifulSoup, limit: int = 10) -> List[TableData]:
    tables: List[TableData] = []
    for table in soup.find_all("table"):
        caption_el = table.find("caption")
        caption = caption_el.get_text(strip=True) if caption_el else None

        rows = []
        headers: List[str] = []
        for tr in table.find_all("tr"):
            cells = [c.get_text(strip=True)[:200] for c in tr.find_all(["td", "th"])]
            if not cells:
                continue
            if not headers and tr.find("th"):
                headers = cells
            else:
                rows.append(cells)
            if len(rows) >= 200:
                break
        if rows or headers:
            tables.append(
                TableData(
                    caption=caption,
                    headers=headers,
                    rows=rows[:50],
                    total_rows=len(rows),
                )
            )
        if len(tables) >= limit:
            break
    return tables


# ---------------------------------------------------------------------------
# Composite — run a list of extractors and return a dict
# ---------------------------------------------------------------------------

def run_extractors(
    html: str,
    url: str,
    extract: List[str],
    max_chars: int = 20000,
) -> Dict[str, Any]:
    soup = _parse_soup(html)
    out: Dict[str, Any] = {}

    if "metadata" in extract or "schema_org" in extract:
        out["metadata"] = extract_metadata(soup, url)

    if "text" in extract:
        text, wc, rt = extract_text(soup, max_chars=max_chars)
        out["text"] = text
        out["word_count"] = wc
        out["reading_time_minutes"] = rt

    if "images" in extract:
        out["images"] = extract_images(soup, url)

    if "videos" in extract:
        out["videos"] = extract_videos(soup, url)

    links = None
    if "links" in extract or "contacts" in extract:
        links = extract_links(soup, url)
        if "links" in extract:
            out["links"] = links

    if "contacts" in extract:
        out["contacts"] = extract_contacts(soup, html, links=links)

    if "tables" in extract:
        out["tables"] = extract_tables(soup)

    return out
