import argparse
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def safe_year_prefix(year):
    return str(year)


def print_section(title):
    print(f"\n## {title}\n")


def print_kv(label, value):
    print(f"- **{label}**: {value}")


def print_table(headers, rows):
    if not rows:
        print("_No data._")
        return

    header_line = "| " + " | ".join(headers) + " |"
    sep_line = "| " + " | ".join("---" for _ in headers) + " |"
    print(header_line)
    print(sep_line)
    for row in rows:
        print("| " + " | ".join(str(cell) for cell in row) + " |")


def parse_iso_date(date_str):
    if not date_str:
        return None
    try:
        if date_str.endswith("Z"):
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return datetime.fromisoformat(date_str)
    except ValueError:
        try:
            return datetime.strptime(date_str[:10], "%Y-%m-%d")
        except ValueError:
            return None


def main():
    parser = argparse.ArgumentParser(
        description="Yearly summary stats for TypingMind chats.db"
    )
    parser.add_argument("year", type=int, help="Year to summarize (e.g., 2024)")
    parser.add_argument(
        "--db-path",
        type=str,
        default=str(Path(__file__).parent / "chats.db"),
        help="Path to chats.db (default: src/typingmind/chats.db)",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path).expanduser()
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return

    year_prefix = safe_year_prefix(args.year)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, title, model, model_title, total_cost_usd, total_tokens, created_at
        FROM chats
        WHERE created_at IS NOT NULL AND substr(created_at, 1, 4) = ?
        """,
        (year_prefix,),
    )
    chat_rows = cursor.fetchall()

    if not chat_rows:
        print(f"No chats found for {args.year}")
        conn.close()
        return

    chat_count = len(chat_rows)

    total_cost = 0.0
    model_counts = defaultdict(int)
    cost_by_model = defaultdict(float)
    tokens_by_model = defaultdict(int)
    month_counts = defaultdict(int)
    date_list = []

    chat_ids = []
    for chat_id, title, model, model_title, total_cost_usd, total_tokens, created_at in chat_rows:
        chat_ids.append(chat_id)
        model_label = model_title or model or "unknown"
        model_counts[model_label] += 1
        if total_cost_usd:
            total_cost += float(total_cost_usd)
            cost_by_model[model_label] += float(total_cost_usd)
        if total_tokens:
            tokens_by_model[model_label] += int(total_tokens)
        if created_at:
            month_key = created_at[:7]
            month_counts[month_key] += 1
            parsed = parse_iso_date(created_at)
            if parsed:
                date_list.append(parsed)

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM messages m
        JOIN chats c ON m.chat_id = c.id
        WHERE substr(c.created_at, 1, 4) = ?
        """,
        (year_prefix,),
    )
    total_messages = cursor.fetchone()[0] or 0

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM messages m
        JOIN chats c ON m.chat_id = c.id
        WHERE m.role = 'user' AND substr(c.created_at, 1, 4) = ?
        """,
        (year_prefix,),
    )
    user_messages = cursor.fetchone()[0] or 0

    cursor.execute(
        """
        SELECT m.role, COUNT(*)
        FROM messages m
        JOIN chats c ON m.chat_id = c.id
        WHERE substr(c.created_at, 1, 4) = ?
        GROUP BY m.role
        ORDER BY COUNT(*) DESC
        """,
        (year_prefix,),
    )
    messages_by_role = cursor.fetchall()

    cursor.execute(
        """
        SELECT m.model, COUNT(*), COALESCE(SUM(m.tokens), 0)
        FROM messages m
        JOIN chats c ON m.chat_id = c.id
        WHERE substr(c.created_at, 1, 4) = ?
        GROUP BY m.model
        ORDER BY COUNT(*) DESC
        """,
        (year_prefix,),
    )
    message_model_rows = cursor.fetchall()

    cursor.execute(
        """
        SELECT c.title, COUNT(m.uuid) as message_count
        FROM chats c
        JOIN messages m ON m.chat_id = c.id
        WHERE substr(c.created_at, 1, 4) = ?
        GROUP BY c.id
        ORDER BY message_count DESC
        LIMIT 10
        """,
        (year_prefix,),
    )
    top_chats_by_messages = cursor.fetchall()

    conn.close()

    avg_messages_per_chat = total_messages / chat_count if chat_count else 0
    avg_user_messages_per_chat = user_messages / chat_count if chat_count else 0
    avg_cost_per_chat = total_cost / chat_count if chat_count else 0

    print_section(f"Yearly Chat Summary ({args.year})")
    print_kv("Chats", f"{chat_count:,}")
    print_kv("Total messages", f"{total_messages:,}")
    print_kv("Your messages", f"{user_messages:,}")
    print_kv("Avg messages per chat", f"{avg_messages_per_chat:.1f}")
    print_kv("Avg your messages per chat", f"{avg_user_messages_per_chat:.1f}")
    print_kv("Total cost (USD)", f"${total_cost:,.2f}")
    print_kv("Avg cost per chat", f"${avg_cost_per_chat:,.2f}")

    if date_list:
        print_kv("First chat date", min(date_list).strftime("%Y-%m-%d"))
        print_kv("Last chat date", max(date_list).strftime("%Y-%m-%d"))

    print_section("Chats by Model")
    print_table(
        ["Model", "Chats"],
        sorted(((k, f"{v:,}") for k, v in model_counts.items()), key=lambda x: -int(x[1].replace(",", ""))),
    )

    print_section("Cost by Model (USD)")
    print_table(
        ["Model", "Cost"],
        sorted(((k, f"${v:,.2f}") for k, v in cost_by_model.items()), key=lambda x: -float(x[1].replace("$", "").replace(",", ""))),
    )

    print_section("Tokens by Model (from chats)")
    print_table(
        ["Model", "Tokens"],
        sorted(((k, f"{v:,}") for k, v in tokens_by_model.items()), key=lambda x: -int(x[1].replace(",", ""))),
    )

    print_section("Messages by Role")
    print_table(
        ["Role", "Messages"],
        [(role or "unknown", f"{count:,}") for role, count in messages_by_role],
    )

    print_section("Message Model Usage")
    print_table(
        ["Model", "Messages", "Tokens"],
        [
            (model or "unknown", f"{count:,}", f"{tokens:,}")
            for model, count, tokens in message_model_rows
        ],
    )

    print_section("Chats by Month")
    print_table(
        ["Month", "Chats"],
        [(month, f"{count:,}") for month, count in sorted(month_counts.items())],
    )

    print_section("Top 10 Chats by Message Count")
    print_table(
        ["Title", "Messages"],
        [(title or "(untitled)", f"{count:,}") for title, count in top_chats_by_messages],
    )


if __name__ == "__main__":
    main()
