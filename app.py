from flask import Flask, request, jsonify, send_from_directory, Response
import sqlite3
import dateparser
from datetime import datetime, timedelta
import re

app = Flask(__name__)

def parse_query(query, use_regex=False):
    """
    Parse search query with support for:
    - Exact phrases in quotes
    - Wildcard patterns with *
    - Negative keywords with -
    - Date extraction
    - Optional regex mode
    """
    dates = []
    exact_phrases = []
    wildcard_patterns = []
    negative_keywords = []
    positive_keywords = []
    
    # Extract quoted phrases first
    import re
    quoted_pattern = r'"([^"]*)"'
    quoted_matches = re.findall(quoted_pattern, query)
    for phrase in quoted_matches:
        exact_phrases.append(phrase.strip())
        # Remove quoted phrases from query for further processing
        query = query.replace(f'"{phrase}"', '')
    
    # Extract negative keywords (prefixed with -)
    negative_pattern = r'-(\S+)'
    negative_matches = re.findall(negative_pattern, query)
    for keyword in negative_matches:
        negative_keywords.append(keyword.strip())
        # Remove negative keywords from query
        query = query.replace(f'-{keyword}', '')
    
    # Extract wildcard patterns (containing *)
    wildcard_pattern = r'\S*\*\S*'
    wildcard_matches = re.findall(wildcard_pattern, query)
    for pattern in wildcard_matches:
        wildcard_patterns.append(pattern.strip())
        # Remove wildcard patterns from query
        query = query.replace(pattern, '')
    
    # Extract dates from remaining query
    words = query.split()
    current_phrase = []
    
    for word in words:
        current_phrase.append(word)
        phrase = ' '.join(current_phrase)
        parsed_date = dateparser.parse(phrase)
        if parsed_date:
            dates.append(parsed_date)
            current_phrase = []
    
    # Extract remaining positive keywords
    for word in words:
        if not any(word in phrase for phrase in current_phrase):
            if word.strip():
                positive_keywords.append(word.strip())
    
    # If no dates were found and no other keywords, use all remaining words
    if not dates and not positive_keywords and not exact_phrases and not wildcard_patterns:
        positive_keywords = [word.strip() for word in words if word.strip()]
    
    return {
        'dates': dates,
        'exact_phrases': exact_phrases,
        'wildcard_patterns': wildcard_patterns,
        'negative_keywords': negative_keywords,
        'positive_keywords': positive_keywords,
        'use_regex': use_regex
    }

def construct_sql_query(parsed_query):
    query_parts = []
    params = []
    
    # Handle exact phrases
    if parsed_query['exact_phrases']:
        phrase_conditions = []
        for phrase in parsed_query['exact_phrases']:
            if parsed_query['use_regex']:
                phrase_conditions.append("m.text REGEXP ?")
                params.append(re.escape(phrase))
            else:
                phrase_conditions.append("LOWER(m.text) LIKE LOWER(?)")
                params.append(f'%{phrase}%')
        query_parts.append('(' + ' AND '.join(phrase_conditions) + ')')
    
    # Handle wildcard patterns
    if parsed_query['wildcard_patterns']:
        wildcard_conditions = []
        for pattern in parsed_query['wildcard_patterns']:
            if parsed_query['use_regex']:
                # Convert wildcard to regex
                regex_pattern = pattern.replace('*', '.*')
                wildcard_conditions.append("m.text REGEXP ?")
                params.append(regex_pattern)
            else:
                # Convert wildcard to SQL LIKE
                like_pattern = pattern.replace('*', '%')
                wildcard_conditions.append("LOWER(m.text) LIKE LOWER(?)")
                params.append(like_pattern)
        query_parts.append('(' + ' AND '.join(wildcard_conditions) + ')')
    
    # Handle positive keywords
    if parsed_query['positive_keywords']:
        keyword_conditions = []
        for keyword in parsed_query['positive_keywords']:
            if parsed_query['use_regex']:
                keyword_conditions.append("m.text REGEXP ?")
                params.append(re.escape(keyword))
            else:
                # Use word boundaries for exact word matches
                keyword_conditions.append("""
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
        query_parts.append('(' + ' AND '.join(keyword_conditions) + ')')
    
    # Handle negative keywords (exclude)
    if parsed_query['negative_keywords']:
        negative_conditions = []
        for keyword in parsed_query['negative_keywords']:
            if parsed_query['use_regex']:
                negative_conditions.append("m.text NOT REGEXP ?")
                params.append(re.escape(keyword))
            else:
                negative_conditions.append("LOWER(m.text) NOT LIKE LOWER(?)")
                params.append(f'%{keyword}%')
        query_parts.append('(' + ' AND '.join(negative_conditions) + ')')
    
    # Handle date filtering
    if parsed_query['dates']:
        date = parsed_query['dates'][0]
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
    print(f"Debug - Parsed Query: {parsed_query}")
    
    return count_query, messages_query, params

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/thread/<conversation_id>/view')
def thread_view(conversation_id):
    """Serve the thread view page"""
    return send_from_directory('static', 'thread.html')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    limit = request.args.get('limit', '10')
    use_regex = request.args.get('regex', 'false').lower() == 'true'
    
    if not query:
        return jsonify({'total_count': 0, 'messages': []})
    
    # Parse query with new enhanced parser
    parsed_query = parse_query(query, use_regex)
    print(f"Debug - Parsed query: {parsed_query}")
    
    # Construct and execute SQL queries
    count_query, messages_query, params = construct_sql_query(parsed_query)
    
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

@app.route('/export')
def export_results():
    query = request.args.get('query', '')
    limit = request.args.get('limit', 'all')
    use_regex = request.args.get('regex', 'false').lower() == 'true'
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    # Parse query with new enhanced parser
    parsed_query = parse_query(query, use_regex)
    
    # Construct and execute SQL queries
    count_query, messages_query, params = construct_sql_query(parsed_query)
    
    try:
        conn = sqlite3.connect('chatgpt_export.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all messages (no limit for export)
        if params:
            cursor.execute(messages_query, params)
        else:
            cursor.execute(messages_query)
        
        rows = cursor.fetchall()
        messages = [dict(row) for row in rows]
        
        # Generate Markdown content
        markdown_content = generate_markdown_export(query, messages)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"chatgpt_search_results_{timestamp}.md"
        
        return Response(
            markdown_content,
            mimetype='text/markdown',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/markdown; charset=utf-8'
            }
        )
        
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

def generate_markdown_export(query, messages):
    """Generate Markdown content from search results"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    markdown = f"""# ChatGPT Search Results

**Search Query:** {query}  
**Export Date:** {timestamp}  
**Total Messages:** {len(messages)}

---

"""
    
    for i, msg in enumerate(messages, 1):
        # Format timestamp
        try:
            msg_time = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
            formatted_time = msg_time.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            formatted_time = msg['timestamp']
        
        # Determine sender display
        sender = "You" if msg['sender'] == 'user' else "Assistant"
        if msg['sender'] == 'tool':
            sender = "Tool"
        
        # Add message to markdown
        markdown += f"""## Message {i}

**Conversation ID:** `{msg['conversation_id']}`  
**Sender:** {sender}  
**Timestamp:** {formatted_time}

{msg['text']}

---

"""
    
    return markdown

@app.route('/thread/<conversation_id>')
def get_thread(conversation_id):
    """Get all messages in a specific conversation thread"""
    try:
        conn = sqlite3.connect('chatgpt_export.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all messages for this conversation, ordered by timestamp
        cursor.execute('''
        SELECT id, conversation_id, timestamp, sender, text
        FROM messages 
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
        ''', (conversation_id,))
        
        rows = cursor.fetchall()
        messages = [dict(row) for row in rows]
        
        if not messages:
            return jsonify({'error': 'Conversation not found'}), 404
        
        return jsonify({
            'conversation_id': conversation_id,
            'message_count': len(messages),
            'messages': messages
        })
        
    except Exception as e:
        print(f"Thread error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/thread/<conversation_id>/export')
def export_thread(conversation_id):
    """Export all messages in a conversation thread as Markdown"""
    try:
        conn = sqlite3.connect('chatgpt_export.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all messages for this conversation
        cursor.execute('''
        SELECT id, conversation_id, timestamp, sender, text
        FROM messages 
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
        ''', (conversation_id,))
        
        rows = cursor.fetchall()
        messages = [dict(row) for row in rows]
        
        if not messages:
            return jsonify({'error': 'Conversation not found'}), 404
        
        # Generate Markdown content
        markdown_content = generate_thread_markdown_export(conversation_id, messages)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"chatgpt_thread_{conversation_id[:8]}_{timestamp}.md"
        
        return Response(
            markdown_content,
            mimetype='text/markdown',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/markdown; charset=utf-8'
            }
        )
        
    except Exception as e:
        print(f"Thread export error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

def generate_thread_markdown_export(conversation_id, messages):
    """Generate Markdown content for a conversation thread"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    markdown = f"""# ChatGPT Conversation Thread

**Conversation ID:** `{conversation_id}`  
**Export Date:** {timestamp}  
**Total Messages:** {len(messages)}

---

"""
    
    for i, msg in enumerate(messages, 1):
        # Format timestamp
        try:
            msg_time = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
            formatted_time = msg_time.strftime('%Y-%m-%d %H:%M:%S UTC')
        except:
            formatted_time = msg['timestamp']
        
        # Determine sender display
        sender = "You" if msg['sender'] == 'user' else "Assistant"
        if msg['sender'] == 'tool':
            sender = "Tool"
        
        # Add message to markdown
        markdown += f"""## Message {i} - {sender}

**Timestamp:** {formatted_time}

{msg['text']}

---

"""
    
    return markdown

if __name__ == '__main__':
    app.run(debug=False, port=5001) 