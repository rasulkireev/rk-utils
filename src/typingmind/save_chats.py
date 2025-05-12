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

def import_data_from_file(json_path, conn, cursor):
    """Import data from a single JSON file to SQLite database."""
    print(f"Reading JSON file: {json_path}")

    # Load JSON data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Check if we have the expected structure
    if 'data' not in data:
        print(f"Warning: JSON file {json_path} doesn't have the expected structure (missing 'data' key)")
        return 0, 0, 0, 0

    chat_count = 0
    message_count = 0
    folder_count = 0
    character_count = 0

    # Import folders
    if 'folders' in data['data']:
        folders = data['data']['folders']
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
    if 'userCharacters' in data['data']:
        characters = data['data']['userCharacters']
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
    if 'chats' in data['data']:
        chats = data['data']['chats']
        print(f"Importing {len(chats)} chats...")

        for chat in chats:
            # Extract token usage if available
            total_tokens = 0
            total_cost = 0.0
            if 'tokenUsage' in chat:
                total_tokens = chat['tokenUsage'].get('totalTokens', 0)
                total_cost = chat['tokenUsage'].get('totalCostUSD', 0.0)

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

def main():
    # Define paths based on the repository structure
    repo_root = Path(__file__).parent.parent.parent  # Assuming script is in src/typingmind/
    data_dir = repo_root / "src" / "typingmind" / "data"
    db_path = repo_root / "src" / "typingmind" / "chats.db"

    # Check if data directory exists
    if not data_dir.exists() or not data_dir.is_dir():
        print(f"Error: Data directory '{data_dir}' does not exist or is not a directory.")
        return

    # Find all JSON files in the data directory
    json_files = list(data_dir.glob("*.json"))

    if not json_files:
        print(f"Error: No JSON files found in '{data_dir}'.")
        return

    print(f"Found {len(json_files)} JSON files in {data_dir}")

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
