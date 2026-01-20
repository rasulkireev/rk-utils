"""
Summarize all the books you've read in a given year using the Readwise Reader API.

What we can (and can't) know about "how much you read in that year"
---------------------------------------------------------------
Reader's Document LIST endpoint returns a *current* `reading_progress` (0..1) plus timestamps like:
- `first_opened_at`, `last_opened_at`: when you opened the document in Reader
- `last_moved_at`: when you moved the doc between locations (e.g. to `archive`)

The API does NOT provide progress history over time, so we can't compute "progress delta within 2025"
exactly. This script therefore uses:
- **Finished in YEAR**: moved to `archive` in that year (or progress >= threshold with activity in year)
- **In progress in YEAR**: opened in that year and progress > 0
- **Sampled in YEAR**: opened in that year and progress is small (e.g. < 20%)

Usage
-----
    READWISE_TOKEN=... python -m src.readwise.annual_book_reading_summary --year 2025

Optional:
    --format markdown|text
    --output /path/to/file.md
    --min-pdf-words 8000
    --include-non-archive  (include books not in archive if opened in the year)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from dotenv import load_dotenv

from src.readwise.utils import fetch_all_documents


def _safe_load_dotenv() -> None:
    """
    In some sandboxed environments, reading `.env` may be blocked.
    Treat dotenv as best-effort; fall back to process env vars.
    """
    try:
        load_dotenv()
    except (PermissionError, OSError):
        pass


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        # Most Readwise timestamps are ISO 8601; many end with 'Z'
        if value.endswith("Z"):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(value)
        # If timezone-less, assume UTC (Reader API docs: "All dates are UTC unless otherwise stated")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _dt_in_year(dt: Optional[datetime], year: int) -> bool:
    if not dt:
        return False
    return dt.astimezone(timezone.utc).year == year


def _as_percent(progress: Optional[float]) -> Optional[int]:
    if progress is None:
        return None
    try:
        p = float(progress)
    except Exception:
        return None
    if p < 0:
        p = 0.0
    if p > 1:
        p = 1.0
    return int(round(p * 100))


def _tag_keys(tags_field: Any) -> Set[str]:
    """
    Reader API returns `tags` as an object/dict in Document LIST.
    We normalize to a set of strings for heuristics.
    """
    keys: Set[str] = set()
    if not tags_field:
        return keys
    if isinstance(tags_field, dict):
        # Often { "some-tag-key": { ... } } or { "some-tag-key": "Some Tag" }
        for k, v in tags_field.items():
            if isinstance(k, str) and k:
                keys.add(k.strip().lower())
            if isinstance(v, str) and v:
                keys.add(v.strip().lower())
            if isinstance(v, dict):
                name = v.get("name")
                if isinstance(name, str) and name:
                    keys.add(name.strip().lower())
                key = v.get("key")
                if isinstance(key, str) and key:
                    keys.add(key.strip().lower())
        return keys
    if isinstance(tags_field, list):
        for t in tags_field:
            if isinstance(t, str) and t:
                keys.add(t.strip().lower())
            elif isinstance(t, dict):
                name = t.get("name")
                if isinstance(name, str) and name:
                    keys.add(name.strip().lower())
                key = t.get("key")
                if isinstance(key, str) and key:
                    keys.add(key.strip().lower())
        return keys
    return keys


@dataclass(frozen=True)
class BookDoc:
    id: str
    title: str
    author: str
    category: str
    location: str
    word_count: int
    reading_progress: Optional[float]
    tags: Set[str]
    first_opened_at: Optional[datetime]
    last_opened_at: Optional[datetime]
    last_moved_at: Optional[datetime]
    updated_at: Optional[datetime]

    @property
    def progress_percent(self) -> Optional[int]:
        return _as_percent(self.reading_progress)

    def estimate_words_read(self) -> Optional[int]:
        if not self.word_count or self.word_count <= 0:
            return None
        if self.reading_progress is None:
            return None
        try:
            p = float(self.reading_progress)
        except Exception:
            return None
        if p < 0:
            p = 0.0
        if p > 1:
            p = 1.0
        return int(round(self.word_count * p))


def _to_bookdoc(doc: Dict[str, Any]) -> BookDoc:
    return BookDoc(
        id=str(doc.get("id") or ""),
        title=str(doc.get("title") or "Untitled").strip(),
        author=str(doc.get("author") or "Unknown").strip(),
        category=str(doc.get("category") or "unknown").strip(),
        location=str(doc.get("location") or "unknown").strip(),
        word_count=int(doc.get("word_count") or 0),
        reading_progress=doc.get("reading_progress", None),
        tags=_tag_keys(doc.get("tags")),
        first_opened_at=_parse_dt(doc.get("first_opened_at")),
        last_opened_at=_parse_dt(doc.get("last_opened_at")),
        last_moved_at=_parse_dt(doc.get("last_moved_at")),
        updated_at=_parse_dt(doc.get("updated_at")),
    )


def _is_probably_book(doc: BookDoc, min_pdf_words: int) -> bool:
    """
    We fetch only `epub` and `pdf` categories.
    - `epub` is almost certainly a book.
    - `pdf` can be a book OR an article/report, so apply a heuristic.
    """
    if doc.category == "epub":
        return True
    if doc.category != "pdf":
        return False

    # Tag-based escape hatch
    if {"book", "books", "ebook", "e-book", "kindle"} & doc.tags:
        return True

    # Word-count heuristic: many PDFs that are actually books are large
    if doc.word_count and doc.word_count >= min_pdf_words:
        return True

    return False


def fetch_all_books() -> List[BookDoc]:
    """
    Fetch all EPUB + PDF docs from Reader and convert to normalized BookDoc objects.
    """
    # Note: fetch_all_documents handles pagination. It requires READWISE_TOKEN in env.
    pdf_docs = fetch_all_documents(category="pdf")
    epub_docs = fetch_all_documents(category="epub")

    by_id: Dict[str, Dict[str, Any]] = {}
    for d in (pdf_docs + epub_docs):
        doc_id = str(d.get("id") or "")
        if not doc_id:
            continue
        by_id[doc_id] = d

    return [_to_bookdoc(d) for d in by_id.values()]


def summarize_books_for_year(
    books: Sequence[BookDoc],
    year: int,
    *,
    include_non_archive: bool,
    min_pdf_words: int,
    finished_threshold: float,
    sampled_threshold: float,
) -> Tuple[List[BookDoc], List[BookDoc], List[BookDoc]]:
    """
    Returns: (finished_in_year, in_progress_in_year, sampled_in_year)
    """
    finished: List[BookDoc] = []
    in_progress: List[BookDoc] = []
    sampled: List[BookDoc] = []

    for b in books:
        if not _is_probably_book(b, min_pdf_words=min_pdf_words):
            continue

        opened_in_year = _dt_in_year(b.first_opened_at, year) or _dt_in_year(b.last_opened_at, year)
        archived_in_year = (b.location == "archive") and _dt_in_year(b.last_moved_at, year)

        # Primary inclusion logic:
        # - always include if archived in year (strong signal of completion)
        # - optionally include if opened in year (captures in-progress reading)
        if not archived_in_year and not (include_non_archive and opened_in_year):
            continue

        p = b.reading_progress
        try:
            p_f = float(p) if p is not None else None
        except Exception:
            p_f = None

        if archived_in_year:
            finished.append(b)
            continue

        # For non-archive: classify by progress
        if p_f is None:
            sampled.append(b)  # opened, but we don't know progress; treat as "sampled/unknown"
        elif p_f >= finished_threshold:
            finished.append(b)
        elif p_f >= sampled_threshold:
            in_progress.append(b)
        elif p_f > 0:
            sampled.append(b)
        else:
            # opened in year but no measurable progress
            sampled.append(b)

    # Sort for readability
    finished.sort(key=lambda b: (b.last_moved_at or b.last_opened_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    in_progress.sort(key=lambda b: (b.last_opened_at or b.updated_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
    sampled.sort(key=lambda b: (b.last_opened_at or b.updated_at or datetime.min.replace(tzinfo=timezone.utc)), reverse=True)

    return finished, in_progress, sampled


def _fmt_book_line(b: BookDoc) -> str:
    parts: List[str] = []
    title_author = f"{b.title} — {b.author}" if b.author and b.author != "Unknown" else b.title
    parts.append(title_author)

    meta: List[str] = []
    if b.category and b.category != "unknown":
        meta.append(b.category)
    if b.location and b.location != "unknown":
        meta.append(f"location={b.location}")

    if (p := b.progress_percent) is not None:
        meta.append(f"progress={p}%")
    else:
        meta.append("progress=unknown")

    if (wr := b.estimate_words_read()) is not None:
        meta.append(f"≈{wr:,} words read")
    elif b.word_count:
        meta.append(f"{b.word_count:,} words total")

    if b.last_opened_at:
        meta.append(f"last_opened={b.last_opened_at.date().isoformat()}")
    if b.last_moved_at and b.location == "archive":
        meta.append(f"archived={b.last_moved_at.date().isoformat()}")

    if meta:
        parts.append(f"({', '.join(meta)})")

    return "- " + " ".join(parts)


def render_summary(
    year: int,
    finished: Sequence[BookDoc],
    in_progress: Sequence[BookDoc],
    sampled: Sequence[BookDoc],
    *,
    output_format: str,
) -> str:
    total = len(finished) + len(in_progress) + len(sampled)

    if output_format == "markdown":
        lines: List[str] = []
        lines.append(f"## Readwise Reader — Book reading summary for {year}")
        lines.append("")
        lines.append(f"- **Total books (heuristic)**: {total}")
        lines.append(f"- **Finished**: {len(finished)}")
        lines.append(f"- **In progress**: {len(in_progress)}")
        lines.append(f"- **Sampled/unknown**: {len(sampled)}")
        lines.append("")

        if finished:
            lines.append("### Finished")
            lines.extend(_fmt_book_line(b) for b in finished)
            lines.append("")

        if in_progress:
            lines.append("### In progress")
            lines.extend(_fmt_book_line(b) for b in in_progress)
            lines.append("")

        if sampled:
            lines.append("### Sampled / unknown")
            lines.extend(_fmt_book_line(b) for b in sampled)
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    # text
    lines = []
    lines.append(f"READWISE READER — BOOK READING SUMMARY {year}")
    lines.append("=" * 48)
    lines.append(f"Total books (heuristic): {total}")
    lines.append(f"Finished: {len(finished)} | In progress: {len(in_progress)} | Sampled/unknown: {len(sampled)}")
    lines.append("")

    def section(title: str, items: Sequence[BookDoc]) -> None:
        if not items:
            return
        lines.append(title)
        lines.append("-" * len(title))
        lines.extend(_fmt_book_line(b) for b in items)
        lines.append("")

    section("Finished", finished)
    section("In progress", in_progress)
    section("Sampled / unknown", sampled)

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    _safe_load_dotenv()

    parser = argparse.ArgumentParser(description="Summarize books read in a given year using Readwise Reader API.")
    parser.add_argument("--year", type=int, default=2025, help="Year to summarize (default: 2025).")
    parser.add_argument("--format", dest="output_format", choices=["markdown", "text"], default="markdown")
    parser.add_argument("--output", type=str, default="", help="Write output to this file (otherwise prints).")
    parser.add_argument(
        "--include-non-archive",
        action="store_true",
        help="Include non-archived books if they were opened in the year (helps capture in-progress reading).",
    )
    parser.add_argument(
        "--min-pdf-words",
        type=int,
        default=8000,
        help="Heuristic: treat PDFs with at least this many words as 'book-like' (default: 8000).",
    )
    parser.add_argument(
        "--finished-threshold",
        type=float,
        default=0.9,
        help="Progress fraction considered finished when not archived (default: 0.9).",
    )
    parser.add_argument(
        "--sampled-threshold",
        type=float,
        default=0.2,
        help="Progress fraction considered 'in progress' vs 'sampled' (default: 0.2).",
    )

    args = parser.parse_args()

    print("Fetching EPUB + PDF documents from Readwise Reader...")
    books = fetch_all_books()
    print(f"Fetched {len(books)} total EPUB/PDF documents.")

    finished, in_progress, sampled = summarize_books_for_year(
        books,
        args.year,
        include_non_archive=args.include_non_archive,
        min_pdf_words=args.min_pdf_words,
        finished_threshold=args.finished_threshold,
        sampled_threshold=args.sampled_threshold,
    )

    output = render_summary(args.year, finished, in_progress, sampled, output_format=args.output_format)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Wrote summary to {args.output}")
    else:
        print("")
        print(output, end="")


if __name__ == "__main__":
    main()
