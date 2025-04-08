import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

def convert_timestamp(ts):
    if not ts:
        return None
    try:
        return datetime.fromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')
    except:
        return None

def create_database(json_path, db_path):
    print(f"Starting database creation...")
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY,
        conversation_id TEXT,
        timestamp TEXT,
        sender TEXT,
        text TEXT
    )
    ''')

    # Read and process JSON file
    try:
        print(f"Opening JSON file: {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            print("Loading JSON data...")
            conversations = json.load(f)
            print(f"Loaded {len(conversations)} conversations")
            
            message_count = 0
            for i, conversation in enumerate(conversations):
                conversation_id = conversation.get('id')
                mapping = conversation.get('mapping', {})
                
                for msg_id, msg_data in mapping.items():
                    if not msg_data or not isinstance(msg_data, dict):
                        continue
                        
                    message = msg_data.get('message', {})
                    if not message:
                        continue
                        
                    author = message.get('author', {})
                    content = message.get('content', {})
                    
                    # Get the text from content.parts if it exists
                    text = ''
                    if isinstance(content, dict):
                        parts = content.get('parts', [])
                        if parts and isinstance(parts, list):
                            text = ' '.join(str(part) for part in parts if part)
                    
                    # Only insert if we have text content
                    if text:
                        timestamp = convert_timestamp(message.get('create_time'))
                        sender = author.get('role', '')
                        
                        cursor.execute('''
                        INSERT INTO messages (conversation_id, timestamp, sender, text)
                        VALUES (?, ?, ?, ?)
                        ''', (
                            conversation_id,
                            timestamp,
                            sender,
                            text
                        ))
                        message_count += 1
                
                if i % 100 == 0:  # Log progress every 100 conversations
                    print(f"Processed {i} conversations, {message_count} messages so far...")
                    conn.commit()  # Periodic commits to avoid memory issues
            
            conn.commit()
            print(f"Successfully created database at {db_path}")
            print(f"Total messages processed: {message_count}")
            
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON file: {e}")
        print(f"Error occurred at position {e.pos}")
        conn.rollback()
    except Exception as e:
        print(f"Error processing JSON file: {e}")
        print(f"Error location:", sys.exc_info()[2].tb_lineno)
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_database.py <json_file_path> <db_file_path>")
        sys.exit(1)
        
    json_path = sys.argv[1]
    db_path = sys.argv[2]
    
    if not Path(json_path).exists():
        print(f"Error: JSON file not found at {json_path}")
        sys.exit(1)
        
    create_database(json_path, db_path) 