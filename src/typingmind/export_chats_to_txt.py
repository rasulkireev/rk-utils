import sqlite3
import os
from datetime import datetime
from pathlib import Path

def export_user_messages():
    """
    Export all user messages from the database to a text file.
    Uses a fixed database path and outputs to chats.txt in the script directory.
    """
    # Fixed database path
    db_path = "/Users/rasul/code/rk-utils/src/typingmind/chats.db"

    # Output file in the same directory as this script
    script_dir = Path(__file__).parent
    output_file = script_dir / "chats.txt"

    # Check if database exists
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return

    # Connect to the database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all chats
    cursor.execute("SELECT id, title, model FROM chats ORDER BY created_at DESC")
    chats = cursor.fetchall()

    with open(output_file, 'w', encoding='utf-8') as f:
        for chat in chats:
            chat_id = chat['id']
            chat_title = chat['title'] or "Untitled"
            chat_model = chat['model'] or "Unknown model"

            # Get all user messages for this chat
            cursor.execute("""
                SELECT content, created_at, message_order
                FROM messages
                WHERE chat_id = ? AND role = 'user'
                ORDER BY message_order ASC
            """, (chat_id,))

            messages = cursor.fetchall()

            # Skip chats with no user messages
            if not messages:
                continue

            # Write chat header
            f.write("======================\n")
            f.write(f"chat id: {chat_id}\n")
            f.write(f"chat title: {chat_title}\n")
            f.write(f"chat model: {chat_model}\n\n")
            f.write("messages:\n")

            # Write all user messages
            for msg in messages:
                content = msg['content']
                created_at = msg['created_at']
                message_order = msg['message_order']

                # Try to format the timestamp if it's in a standard format
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, AttributeError):
                    timestamp = created_at or "Unknown time"

                f.write(f"\n[{timestamp}] Message #{message_order}:\n")
                f.write(f"{content}\n")

            f.write("======================\n\n")

    conn.close()
    print(f"Export completed. User messages saved to {output_file}")

if __name__ == "__main__":
    export_user_messages()
