import os
import sqlite3
import pandas as pd
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

def ensure_nltk_data():
    """Ensure required NLTK data is downloaded."""
    nltk_data_dir = os.path.expanduser('~/nltk_data')
    os.makedirs(nltk_data_dir, exist_ok=True)

    # Download required NLTK data
    try:
        # Try to use punkt tokenizer to see if it's properly installed
        nltk.tokenize.word_tokenize("Test sentence")
    except LookupError:
        print("Downloading NLTK punkt tokenizer...")
        nltk.download('punkt', download_dir=nltk_data_dir)

    try:
        # Try to access stopwords to see if they're properly installed
        stopwords.words('english')
    except LookupError:
        print("Downloading NLTK stopwords...")
        nltk.download('stopwords', download_dir=nltk_data_dir)

    # Add the directory to NLTK's search path
    if nltk_data_dir not in nltk.data.path:
        nltk.data.path.append(nltk_data_dir)

# Call this function at the beginning of your script
ensure_nltk_data()

# Now import NLTK modules after ensuring data is available
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

def analyze_chats_db():
    # Connect to the database
    db_path = "/Users/rasul/code/rk-utils/src/typingmind/chats.db"  # Since it will be in the same directory
    conn = sqlite3.connect(db_path)

    # Basic stats
    print("\n=== BASIC STATISTICS ===\n")

    # Number of total chats
    chat_count = pd.read_sql_query("SELECT COUNT(*) as count FROM chats", conn).iloc[0]['count']
    print(f"Total number of chats: {chat_count}")

    # Number of total messages
    message_count = pd.read_sql_query("SELECT COUNT(*) as count FROM messages", conn).iloc[0]['count']
    print(f"Total number of messages: {message_count}")

    # Number of messages by role
    role_counts = pd.read_sql_query("SELECT role, COUNT(*) as count FROM messages GROUP BY role", conn)
    print("\nMessages by role:")
    for _, row in role_counts.iterrows():
        print(f"  {row['role']}: {row['count']}")

    # Total tokens
    total_tokens = pd.read_sql_query("SELECT SUM(tokens) as total FROM messages", conn).iloc[0]['total']
    print(f"\nTotal tokens used: {total_tokens:,}")

    # Total cost
    total_cost = pd.read_sql_query("SELECT SUM(total_cost_usd) as total FROM chats", conn).iloc[0]['total']
    print(f"Total cost: ${total_cost:.2f}")

    # Character count analysis
    messages_df = pd.read_sql_query("SELECT role, content FROM messages", conn)
    total_chars = messages_df['content'].str.len().sum()
    print(f"\nTotal characters in all messages: {total_chars:,}")

    # Characters by role
    role_chars = messages_df.groupby('role')['content'].apply(lambda x: sum(len(s) for s in x))
    print("\nCharacters by role:")
    for role, chars in role_chars.items():
        print(f"  {role}: {chars:,}")

    # Time-based analysis
    print("\n=== TIME-BASED ANALYSIS ===\n")

    # Convert timestamps to datetime objects
    chats_df = pd.read_sql_query("SELECT created_at FROM chats", conn)
    chats_df['created_at'] = pd.to_datetime(chats_df['created_at'])

    # Chats by month
    chats_by_month = chats_df.groupby(chats_df['created_at'].dt.strftime('%Y-%m')).size()
    print("Chats by month:")
    for month, count in chats_by_month.items():
        print(f"  {month}: {count}")

    # Content analysis
    print("\n=== CONTENT ANALYSIS ===\n")

    # Get user messages for content analysis
    user_messages = pd.read_sql_query("SELECT content FROM messages WHERE role = 'user'", conn)

    # Extract all text from user messages
    all_text = ' '.join(user_messages['content'].tolist())

    # Tokenize and clean text - using a simpler approach to avoid punkt_tab issues
    try:
        # Try using the standard tokenizer
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(all_text.lower())
        words = [word for word in words if word.isalpha() and word not in stop_words and len(word) > 2]
    except LookupError:
        # Fallback to a simple tokenization if NLTK tokenizer fails
        print("Warning: Using simple tokenization as NLTK tokenizer failed")
        stop_words = set(stopwords.words('english')) if 'stopwords' in nltk.data.path else set()
        words = all_text.lower().split()
        words = [word for word in words if word.isalpha() and word not in stop_words and len(word) > 2]

    # Count word frequencies
    word_freq = Counter(words)

    # Print top words
    print("Top 30 words in your messages:")
    for word, count in word_freq.most_common(30):
        print(f"  {word}: {count}")

    # Model usage analysis
    print("\n=== MODEL USAGE ===\n")

    model_usage = pd.read_sql_query("SELECT model, COUNT(*) as count, SUM(tokens) as tokens FROM messages GROUP BY model", conn)
    print("Usage by model:")
    for _, row in model_usage.iterrows():
        print(f"  {row['model']}: {row['count']} messages, {row['tokens']:,} tokens")

    # Average tokens per message by model
    print("\nAverage tokens per message by model:")
    for _, row in model_usage.iterrows():
        avg_tokens = row['tokens'] / row['count'] if row['count'] > 0 else 0
        print(f"  {row['model']}: {avg_tokens:.1f}")

    # Topic extraction (simple approach)
    print("\n=== TOPIC ANALYSIS ===\n")

    # Get chat titles and previews
    chats_content = pd.read_sql_query("SELECT title, preview FROM chats", conn)

    # Extract common topics from titles using simple tokenization to avoid NLTK issues
    all_titles = ' '.join(chats_content['title'].dropna().tolist())
    try:
        title_words = word_tokenize(all_titles.lower())
    except LookupError:
        title_words = all_titles.lower().split()

    title_words = [word for word in title_words if word.isalpha() and word not in stop_words and len(word) > 2]
    title_freq = Counter(title_words)

    print("Common topics from chat titles:")
    for word, count in title_freq.most_common(15):
        print(f"  {word}: {count}")

    # Analyze chat frequency over time
    print("\n=== CHAT ACTIVITY PATTERNS ===\n")

    # Get all messages with timestamps
    messages_time = pd.read_sql_query("SELECT created_at FROM messages", conn)
    messages_time['created_at'] = pd.to_datetime(messages_time['created_at'])

    # Messages by hour of day
    hour_counts = messages_time['created_at'].dt.hour.value_counts().sort_index()
    print("Messages by hour of day:")
    for hour, count in hour_counts.items():
        # Convert hour to int before formatting
        hour_int = int(hour)
        print(f"  {hour_int:02d}:00 - {hour_int:02d}:59: {count}")

    # Messages by day of week
    day_mapping = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday',
                   4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    day_counts = messages_time['created_at'].dt.dayofweek.value_counts().sort_index()
    print("\nMessages by day of week:")
    for day, count in day_counts.items():
        # Convert day to int if it's a float
        day_int = int(day) if isinstance(day, float) else day
        print(f"  {day_mapping[day_int]}: {count}")

    # Close the connection
    conn.close()

if __name__ == "__main__":
    analyze_chats_db()
