import argparse
import json
import sqlite3
import os
import sys
import glob
from datetime import datetime
from pathlib import Path

def create_database(db_path):
    """Create the SQLite database schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create chats table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        chat_id TEXT,
        title TEXT,
        model TEXT,
        model_title TEXT,
        folder_id TEXT,
        created_at TEXT,
        updated_at TEXT,
        synced_at TEXT,
        preview TEXT,
        total_tokens INTEGER,
        total_cost_usd REAL
    )
    ''')

    # Create messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        uuid TEXT PRIMARY KEY,
        chat_id TEXT,
        role TEXT,
        content TEXT,
        created_at TEXT,
        model TEXT,
        finish_reason TEXT,
        tokens INTEGER,
        message_order INTEGER,
        FOREIGN KEY (chat_id) REFERENCES chats(id)
    )
    ''')

    # Create folders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS folders (
        id TEXT PRIMARY KEY,
        title TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    ''')

    # Create characters table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS characters (
        id TEXT PRIMARY KEY,
        title TEXT,
        description TEXT,
        instruction TEXT,
        welcome_message TEXT,
        type TEXT,
        avatar_url TEXT
    )
    ''')

    conn.commit()
    return conn

def extract_message_content(message):
    """Extract the text content from a message."""
    if 'content' not in message:
        return ""

    content = message['content']

    # Handle different content formats
    if isinstance(content, str):
        return content
    elif isinstance(content, list) and len(content) > 0:
        # Extract text from content array
        text_parts = []
        for item in content:
            if isinstance(item, dict) and 'text' in item and 'type' in item:
                text_parts.append(item['text'])
        return "\n".join(text_parts)

    return str(content)

def get_token_count(message):
    """Extract token count from message if available."""
    if 'usage' in message and 'total_tokens' in message['usage']:
        return message['usage']['total_tokens']
    return 0

def load_export_data(json_path):
    """Load TypingMind export data and resolve chunked chats if needed."""
    with open(json_path, 'r', encoding='utf-8') as f:
        payload = json.load(f)

    if 'data' not in payload:
        print(f"Warning: JSON file {json_path} doesn't have the expected structure (missing 'data' key)")
        return None, []

    data = payload['data']
    chats = []
    chats_data = data.get('chats', [])

    if isinstance(chats_data, dict) and 'chunks' in chats_data:
        chunk_paths = chats_data.get('chunks', [])
        for rel_path in chunk_paths:
            chunk_path = json_path.parent / rel_path
            if not chunk_path.exists():
                print(f"Warning: Chunk file not found: {chunk_path}")
                continue

            with open(chunk_path, 'r', encoding='utf-8') as chunk_file:
                chunk_payload = json.load(chunk_file)

            if isinstance(chunk_payload, list):
                chats.extend(chunk_payload)
            elif isinstance(chunk_payload, dict) and 'data' in chunk_payload and 'chats' in chunk_payload['data']:
                chats.extend(chunk_payload['data'].get('chats', []))
            else:
                print(f"Warning: Unexpected chunk format in {chunk_path}")
    elif isinstance(chats_data, list):
        chats = chats_data
    else:
        print(f"Warning: Unexpected chats format in {json_path}")

    return data, chats


def import_data_from_file(json_path, conn, cursor):
    """Import data from a single JSON file to SQLite database."""
    print(f"Reading JSON file: {json_path}")

    data, chats = load_export_data(json_path)
    if data is None:
        return 0, 0, 0, 0

    chat_count = 0
    message_count = 0
    folder_count = 0
    character_count = 0

    # Import folders
    if 'folders' in data:
        folders = data['folders']
        print(f"Importing {len(folders)} folders...")
        for folder in folders:
            cursor.execute(
                "INSERT OR REPLACE INTO folders (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (
                    folder.get('id', ''),
                    folder.get('title', ''),
                    folder.get('createdAt', ''),
                    folder.get('updatedAt', '')
                )
            )
        folder_count = len(folders)

    # Import characters
    if 'userCharacters' in data:
        characters = data['userCharacters']
        print(f"Importing {len(characters)} characters...")
        for character in characters:
            cursor.execute(
                "INSERT OR REPLACE INTO characters (id, title, description, instruction, welcome_message, type, avatar_url) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    character.get('id', ''),
                    character.get('title', ''),
                    character.get('description', ''),
                    character.get('instruction', ''),
                    character.get('welcomeMessage', ''),
                    character.get('type', ''),
                    character.get('avatarURL', '')
                )
            )
        character_count = len(characters)

    # Import chats
    if chats:
        print(f"Importing {len(chats)} chats...")

        for chat in chats:
            # Extract token usage if available
            total_tokens = 0
            total_cost = 0.0
            token_usage = chat.get('tokenUsage') or {}
            if isinstance(token_usage, dict):
                total_tokens = token_usage.get('totalTokens', 0)
                total_cost = token_usage.get('totalCostUSD', 0.0)

            # Extract model info
            model = chat.get('model', '')
            model_title = ''
            if 'modelInfo' in chat and 'title' in chat['modelInfo']:
                model_title = chat['modelInfo']['title']

            # Insert chat record
            cursor.execute(
                """
                INSERT OR REPLACE INTO chats
                (id, chat_id, title, model, model_title, folder_id, created_at, updated_at, synced_at, preview, total_tokens, total_cost_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chat.get('id', ''),
                    chat.get('chatID', ''),
                    chat.get('chatTitle', ''),
                    model,
                    model_title,
                    chat.get('folderID', ''),
                    chat.get('createdAt', ''),
                    chat.get('updatedAt', ''),
                    chat.get('syncedAt', ''),
                    chat.get('preview', ''),
                    total_tokens,
                    total_cost
                )
            )

            # Insert messages
            if 'messages' in chat:
                for i, message in enumerate(chat['messages']):
                    content = extract_message_content(message)
                    tokens = get_token_count(message)

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO messages
                        (uuid, chat_id, role, content, created_at, model, finish_reason, tokens, message_order)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            message.get('uuid', ''),
                            chat.get('id', ''),
                            message.get('role', ''),
                            content,
                            message.get('createdAt', ''),
                            message.get('model', model),
                            message.get('finish', message.get('stop_reason', '')),
                            tokens,
                            i  # Store the message order
                        )
                    )
                message_count += len(chat['messages'])

            chat_count += 1

    conn.commit()
    return chat_count, message_count, folder_count, character_count


def find_export_files(data_dir):
    json_files = list(data_dir.glob("*.json"))
    json_files.extend(list(data_dir.glob("*/data.json")))
    return sorted(set(json_files))

def main():
    # Define paths based on the repository structure
    repo_root = Path(__file__).parent.parent.parent  # Assuming script is in src/typingmind/
    data_dir = repo_root / "src" / "typingmind" / "data"
    db_path = repo_root / "src" / "typingmind" / "chats.db"

    parser = argparse.ArgumentParser(description="Import TypingMind export data into chats.db")
    parser.add_argument(
        "export_path",
        nargs="?",
        help="Path to TypingMind export folder or JSON file (optional)",
    )
    args = parser.parse_args()

    if args.export_path:
        export_path = Path(args.export_path).expanduser()
        if export_path.is_dir():
            data_json = export_path / "data.json"
            if data_json.exists():
                json_files = [data_json]
            else:
                json_files = list(export_path.glob("*.json"))
        elif export_path.is_file():
            json_files = [export_path]
        else:
            print(f"Error: export path '{export_path}' does not exist.")
            return
    else:
        # Check if data directory exists
        if not data_dir.exists() or not data_dir.is_dir():
            print(f"Error: Data directory '{data_dir}' does not exist or is not a directory.")
            return

        # Find all JSON files in the data directory
        json_files = find_export_files(data_dir)

    if not json_files:
        print("Error: No JSON files found to import.")
        return

    source_label = export_path if args.export_path else data_dir
    print(f"Found {len(json_files)} JSON files in {source_label}")

    # Create database
    conn = create_database(db_path)
    cursor = conn.cursor()

    # Import data from each JSON file
    total_chats = 0
    total_messages = 0
    total_folders = 0
    total_characters = 0

    for json_file in json_files:
        chats, messages, folders, characters = import_data_from_file(json_file, conn, cursor)
        total_chats += chats
        total_messages += messages
        total_folders += folders
        total_characters += characters

    # Print summary
    print(f"\nDatabase created successfully at: {db_path}")
    print(f"\nImport Summary:")
    print(f"- Chats: {total_chats}")
    print(f"- Messages: {total_messages}")
    print(f"- Folders: {total_folders}")
    print(f"- Characters: {total_characters}")

    conn.close()

if __name__ == "__main__":
    main()
