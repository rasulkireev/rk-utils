import argparse
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from openai import OpenAI


@dataclass(frozen=True)
class Step:
    key: str
    prompt: str


INSTRUCTIONS = """You are a precise writing assistant for Markdown book notes.

Hard rules:
- Output MUST be valid Markdown (no HTML).
- Follow the user's formatting constraints for each step (e.g. "only bullets", "only YAML frontmatter").
- Do NOT wrap output in triple backticks unless explicitly requested.
- Do NOT add extra headings if told not to.
- If data is missing (dates, rating, cover), choose sensible placeholders but keep them consistent.
"""


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_-]+", "-", value)
    value = re.sub(r"^-+|-+$", "", value)
    return value or "book-notes"


def read_text_file(path: Path, max_chars: int | None) -> str:
    content = path.read_text(encoding="utf-8", errors="replace")
    if max_chars is not None and len(content) > max_chars:
        # Keep the end of the file (often contains latest/most relevant notes).
        content = content[-max_chars:]
    return content


def extract_yaml_frontmatter(text: str) -> tuple[str, dict[str, Any]]:
    """
    Returns (frontmatter_block_including_delimiters, parsed_yaml_dict).
    Falls back gracefully if the model returns YAML without --- delimiters.
    """
    match = re.search(r"^---\s*\n([\s\S]*?)\n---\s*$", text.strip(), flags=re.MULTILINE)
    if match:
        yaml_body = match.group(1)
        data = yaml.safe_load(yaml_body) or {}
        block = f"---\n{yaml_body}\n---"
        return block, data

    # Try treating the entire output as YAML.
    data = yaml.safe_load(text) or {}
    block = text.strip()
    if not block.startswith("---"):
        block = f"---\n{block}\n---"
    return block, data


def run_steps(
    client: OpenAI,
    model: str,
    highlights: str,
    steps: list[Step],
) -> dict[str, str]:
    results: dict[str, str] = {}

    total = len(steps)
    for i, step in enumerate(steps, start=1):
        # Independent calls: each step sees the highlights plus its own instructions.
        step_input = f"BOOK HIGHLIGHTS:\n\n{highlights}\n\n{step.prompt}"

        print(f"[{i}/{total}] Calling model={model} step={step.key} ...", flush=True)
        started = time.time()
        resp = client.responses.create(model=model, instructions=INSTRUCTIONS, input=step_input)
        elapsed_s = time.time() - started
        text = (resp.output_text or "").strip()
        results[step.key] = text
        print(f"[{i}/{total}] Done step={step.key} ({elapsed_s:.1f}s, {len(text):,} chars)", flush=True)

    return results


def build_markdown_doc(
    frontmatter_block: str,
    summary: str,
    learnings: str,
    key_sentences: str,
    unity: str,
    authors_problems: str,
    prompt_ideas: str,
) -> str:
    parts: list[str] = []
    parts.append(frontmatter_block.strip())
    parts.append("")
    parts.append("")
    parts.append("## My Thoughts")
    parts.append("")
    parts.append("...")
    parts.append("")
    parts.append("## Summary")
    parts.append("")
    parts.append(summary.strip())
    parts.append("")
    parts.append("## Learnings")
    parts.append("")
    parts.append(learnings.strip())
    parts.append("")
    parts.append("## '[How to Read a Book](/how-to-read-a-book)' Analysis")
    parts.append("")
    parts.append("### Key Sentences")
    parts.append("")
    parts.append(key_sentences.strip())
    parts.append("")
    parts.append("### Unity of the Book")
    parts.append("")
    parts.append(unity.strip())
    parts.append("")
    parts.append("### Author's Problems")
    parts.append("")
    parts.append(authors_problems.strip())
    parts.append("")
    parts.append("## Prompt / Agent Ideas")
    parts.append("")
    parts.append(prompt_ideas.strip())
    parts.append("")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate book notes markdown from highlights via OpenAI.")
    parser.add_argument("highlights_path", type=str, help="Path to book highlights file (txt/md).")
    parser.add_argument("--model", type=str, default="gpt-5.2", help="OpenAI model name (default: gpt-5.2).")
    parser.add_argument(
        "--out-dir",
        type=str,
        default=str(Path("ignore") / "book-notes"),
        help="Output directory for generated markdown (default: ignore/book-notes).",
    )
    parser.add_argument("--max-chars", type=int, default=120_000, help="Max chars of highlights to send (default: 120000).")
    parser.add_argument("--dry-run", action="store_true", help="Don't write file; print result to stdout.")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set in your environment.")

    highlights_file = Path(args.highlights_path).expanduser().resolve()
    if not highlights_file.exists():
        raise SystemExit(f"Highlights file not found: {highlights_file}")

    highlights = read_text_file(highlights_file, max_chars=args.max_chars)
    print(f"Loaded highlights: {highlights_file} ({len(highlights):,} chars)", flush=True)

    steps: list[Step] = [
        Step(
            key="frontmatter",
            prompt=(
                "Create YAML frontmatter for a book-notes markdown post based on these highlights.\n"
                "Constraints:\n"
                "- Output ONLY the YAML frontmatter including the '---' delimiters.\n"
                "- Must include keys: title, author, rating, slug, description, cover, dateRead, dateCreated, dateUpdated, category, type, notAffiliateLink, hasSummaries, tags.\n"
                "- Use type: book.\n"
                "- tags must be a YAML list.\n"
                "- Tags must be complete words (no hyphens, no abbreviations).\n"
            ),
        ),
        Step(
            key="summary",
            prompt=(
                "Write the book summary in the style of my example.\n"
                "Constraints:\n"
                "- Output ONLY the summary text (no headings like '## Summary').\n"
                "- Max 2 paragraphs.\n"
                "- Be concrete and non-fluffy; anchor claims in the highlights.\n"
            ),
        ),
        Step(
            key="learnings",
            prompt=(
                "Generate condensed learnings from the book.\n"
                "Constraints:\n"
                "- Output ONLY a Markdown bullet list.\n"
                "- One level deep unless absolutely necessary.\n"
                "- 8–16 bullets.\n"
            ),
        ),
        Step(
            key="key_sentences",
            prompt=(
                "Create a 'How to Read a Book' style Key Sentences section.\n"
                "Constraints:\n"
                "- Output ONLY the numbered list content (no '### Key Sentences' heading).\n"
                "- 3–6 key sentences.\n"
                "- Format exactly:\n"
                "  1) \"Quote\"\n"
                "     - **Why it’s crucial**: ...\n"
                "     - **Proposition**: ...\n"
            ),
        ),
        Step(
            key="unity",
            prompt=(
                "Determine the unity of the book.\n"
                "Constraints:\n"
                "- Output ONLY the unity statement (no heading).\n"
                "- ONE sentence, or at most a very short paragraph.\n"
            ),
        ),
        Step(
            key="authors_problems",
            prompt=(
                "Identify the author's problems/questions (How to Read a Book style).\n"
                "Constraints:\n"
                "- Output ONLY Markdown content (no extra commentary).\n"
                "- Use this exact structure:\n"
                "  #### Main Problem\n"
                "  ...\n\n"
                "  #### Supporting Problems\n"
                "  1. ...\n"
                "  2. ...\n\n"
                "  #### Problem Hierarchy\n"
                "  ...\n"
            ),
        ),
        Step(
            key="prompt_ideas",
            prompt=(
                "Below are the highlights I made from the book.\n"
                "Come up with ideas for AI prompts/agents that I could use to automate or improve parts of my life using ideas from these highlights.\n"
                "Constraints:\n"
                "- Output ONLY Markdown content.\n"
                "- Provide 8–15 ideas.\n"
                "- Each idea must include:\n"
                "  - A short name\n"
                "  - Goal (1 sentence)\n"
                "  - Inputs (bullets)\n"
                "  - Outputs (bullets)\n"
                "  - A ready-to-copy prompt skeleton (as a Markdown blockquote)\n"
                "- Keep it practical and non-cringy.\n"
            ),
        ),
    ]

    client = OpenAI(api_key=api_key)
    results = run_steps(client=client, model=args.model, highlights=highlights, steps=steps)

    frontmatter_block, frontmatter_data = extract_yaml_frontmatter(results["frontmatter"])
    slug = frontmatter_data.get("slug")
    if not isinstance(slug, str) or not slug.strip():
        title = frontmatter_data.get("title") if isinstance(frontmatter_data.get("title"), str) else ""
        slug = slugify(title or highlights_file.stem)

    doc = build_markdown_doc(
        frontmatter_block=frontmatter_block,
        summary=results["summary"],
        learnings=results["learnings"],
        key_sentences=results["key_sentences"],
        unity=results["unity"],
        authors_problems=results["authors_problems"],
        prompt_ideas=results["prompt_ideas"],
    )

    if args.dry_run:
        print("Dry run enabled; printing markdown to stdout.\n", flush=True)
        print(doc)
        return 0

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{slug}.md"
    out_path.write_text(doc, encoding="utf-8")
    print(f"Wrote: {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
