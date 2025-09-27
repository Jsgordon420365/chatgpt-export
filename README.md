# ChatGPT Export Search Tool

A web-based search interface for exploring your ChatGPT conversation exports. This tool allows you to search through your exported ChatGPT conversations using keywords and date filters, with an intuitive web interface.

## Features

- **Smart Search**: Search by keywords with intelligent word boundary matching
- **Date Filtering**: Natural language date parsing (e.g., "last week", "yesterday", "January 2024")
- **Web Interface**: Clean, modern web UI for easy searching and browsing
- **Message Selection**: Select and export individual or multiple messages
- **SQLite Database**: Fast, local database storage for your conversations
- **Export Support**: Export selected messages (functionality ready for implementation)

## Prerequisites

- Python 3.7 or higher
- A ChatGPT export JSON file from your account

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd chatgpt-export
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Export your ChatGPT data**
   - Go to [ChatGPT Settings](https://chat.openai.com/settings)
   - Navigate to "Data controls" → "Export data"
   - Download your data as JSON format
   - Save the file (e.g., `chatgpt_export.json`)

## Setup

1. **Create the database from your export**
   ```bash
   python create_database.py chatgpt_export.json chatgpt_export.db
   ```
   
   This will:
   - Parse your ChatGPT export JSON file
   - Extract all messages from conversations
   - Create a SQLite database with searchable message data
   - Show progress as it processes your conversations

2. **Start the web server**
   ```bash
   python app.py
   ```

3. **Open your browser**
   Navigate to `http://localhost:5001`

## Usage

### Basic Search

1. **Enter your search query** in the search box
   - Use keywords: `python async programming`
   - Include dates: `machine learning from last month`
   - Combine both: `react hooks yesterday`

2. **Select result limit** (10, 25, 50, 100, or all)

3. **Click Search** or press Enter

### Advanced Search Examples

- **Keyword search**: `javascript promises`
- **Date-specific**: `from last week`
- **Combined**: `python debugging from January 2024`
- **Natural language dates**: 
  - `yesterday`
  - `last month`
  - `January 15th`
  - `3 days ago`

### Message Management

- **Select messages**: Use checkboxes to select multiple messages
- **Export individual**: Click "Export" button on any message
- **Export selected**: Select multiple messages and use "Export Selected"

## File Structure

```
chatgpt-export/
├── app.py                 # Flask web application
├── create_database.py     # Database creation script
├── requirements.txt       # Python dependencies
├── static/
│   └── index.html        # Web interface
├── chatgpt_export.db     # SQLite database (created after setup)
└── README.md            # This file
```

## Database Schema

The tool creates a SQLite database with the following structure:

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id TEXT,
    timestamp TEXT,
    sender TEXT,           -- 'user' or 'assistant'
    text TEXT             -- Message content
);
```

## API Endpoints

- `GET /` - Main search interface
- `GET /search?query=<query>&limit=<limit>` - Search API
  - `query`: Search terms (keywords and/or dates)
  - `limit`: Number of results (10, 25, 50, 100, or 'all')

## Troubleshooting

### Common Issues

1. **"Database not found" error**
   - Make sure you've run `create_database.py` first
   - Check that `chatgpt_export.db` exists in the project directory

2. **"No results found" for valid searches**
   - Check that your JSON export file was processed correctly
   - Verify the database contains messages by checking the console output during database creation

3. **Date parsing issues**
   - The tool uses natural language date parsing
   - Try different date formats: "last week", "January 2024", "yesterday"

4. **Port already in use**
   - The app runs on port 5001 by default
   - Change the port in `app.py` if needed: `app.run(debug=True, port=5002)`

### Performance Tips

- For large exports (10,000+ messages), the initial database creation may take several minutes
- Use result limits for faster searches on large datasets
- The database is optimized for text search with word boundary matching

## Development

### Adding New Features

The codebase is structured for easy extension:

- **Backend**: Modify `app.py` for new API endpoints
- **Frontend**: Update `static/index.html` for UI changes
- **Database**: Extend `create_database.py` for new data fields

### Dependencies

- **Flask**: Web framework
- **SQLite3**: Database (built into Python)
- **dateparser**: Natural language date parsing
- **python-dateutil**: Date utilities

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests for improvements.

---

**Note**: This tool processes your ChatGPT data locally. Your conversations are never sent to external servers, ensuring your privacy and data security.
