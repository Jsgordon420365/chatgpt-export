from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import dateparser
from datetime import datetime, timedelta
import re

app = Flask(__name__)

def parse_query(query):
    # Simple date extraction using dateparser
    dates = []
    words = query.split()
    current_phrase = []
    
    for word in words:
        current_phrase.append(word)
        phrase = ' '.join(current_phrase)
        parsed_date = dateparser.parse(phrase)
        if parsed_date:
            dates.append(parsed_date)
            current_phrase = []
    
    # Extract keywords (everything that's not part of a date)
    keywords = []
    for word in words:
        # Skip words that are part of a date phrase
        if not any(word in phrase for phrase in current_phrase):
            # Add the word as a keyword if it's not empty and not just whitespace
            if word.strip():
                keywords.append(word.strip())
    
    # If no dates were found, use all words as keywords
    if not dates and not keywords:
        keywords = [word.strip() for word in words if word.strip()]
    
    return dates, keywords

def construct_sql_query(dates, keywords):
    query_parts = []
    params = []
    
    # Add keyword search if keywords exist
    if keywords:
        # Create conditions for each keyword with word boundaries
        word_conditions = []
        for keyword in keywords:
            # Use word boundaries to ensure exact word matches
            # The pattern matches:
            # 1. Word at start of text
            # 2. Word in middle of text
            # 3. Word at end of text
            # 4. Word followed by punctuation
            word_conditions.append("""
                (LOWER(m.text) LIKE LOWER(?) OR
                 LOWER(m.text) LIKE LOWER(?) OR
                 LOWER(m.text) LIKE LOWER(?) OR
                 LOWER(m.text) LIKE LOWER(?) OR
                 LOWER(m.text) LIKE LOWER(?) OR
                 LOWER(m.text) LIKE LOWER(?) OR
                 LOWER(m.text) LIKE LOWER(?) OR
                 LOWER(m.text) LIKE LOWER(?))
            """)
            params.extend([
                f'{keyword} %',  # word at start
                f'% {keyword} %',  # word in middle
                f'% {keyword}',  # word at end
                f'% {keyword}.%',  # word followed by period
                f'% {keyword},%',  # word followed by comma
                f'% {keyword};%',  # word followed by semicolon
                f'% {keyword}:%',  # word followed by colon
                f'% {keyword}?%'   # word followed by question mark
            ])
        query_parts.append('(' + ' AND '.join(word_conditions) + ')')
    
    # Add date filtering if dates exist
    if dates:
        # Use the first date as a reference point
        date = dates[0]
        query_parts.append("timestamp BETWEEN ? AND ?")
        params.extend([
            (date - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            (date + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
        ])
    
    # Construct final query
    where_clause = ' WHERE ' + ' AND '.join(query_parts) if query_parts else ''
    
    # First get the count
    count_query = f'''
    SELECT COUNT(*) as total_count
    FROM messages m
    {where_clause}
    '''
    
    # Then get the messages
    messages_query = f'''
    SELECT id, conversation_id, timestamp, sender, text
    FROM messages m
    {where_clause}
    ORDER BY timestamp DESC
    '''
    
    print(f"Debug - SQL Query: {count_query}")
    print(f"Debug - Parameters: {params}")
    
    return count_query, messages_query, params

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    limit = request.args.get('limit', '10')
    
    if not query:
        return jsonify({'total_count': 0, 'messages': []})
    
    # Parse query
    dates, keywords = parse_query(query)
    print(f"Debug - Parsed keywords: {keywords}")
    print(f"Debug - Parsed dates: {dates}")
    
    # Construct and execute SQL queries
    count_query, messages_query, params = construct_sql_query(dates, keywords)
    
    try:
        conn = sqlite3.connect('chatgpt_export.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First get the count
        if params:
            cursor.execute(count_query, params)
        else:
            cursor.execute(count_query)
        count_result = cursor.fetchone()
        total_count = count_result['total_count']
        print(f"Debug - Total count: {total_count}")
        
        # Then get the messages with limit
        if limit != 'all':
            try:
                limit_num = int(limit)
                messages_query += ' LIMIT ?'
                if params:
                    cursor.execute(messages_query, params + [limit_num])
                else:
                    cursor.execute(messages_query, [limit_num])
            except ValueError:
                return jsonify({'error': 'Invalid limit parameter'}), 400
        else:
            if params:
                cursor.execute(messages_query, params)
            else:
                cursor.execute(messages_query)
        
        rows = cursor.fetchall()
        messages = [dict(row) for row in rows]
        
        return jsonify({
            'total_count': total_count,
            'messages': messages
        })
    except Exception as e:
        print(f"Search error: {e}")  # Add error logging
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001) 