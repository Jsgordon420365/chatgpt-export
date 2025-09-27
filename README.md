# ChatGPT Export Search Tool

A powerful web-based search interface for exploring your ChatGPT conversation exports. This tool allows you to search through your exported ChatGPT conversations using advanced search features, view complete conversation threads, and export results in various formats.

## ✨ Features

### 🔍 Advanced Search Capabilities
- **Smart Keyword Search** - Find messages containing specific words or phrases
- **Exact Phrase Matching** - Use quotes for precise phrase searches: `"exact phrase"`
- **Wildcard Search** - Use asterisks for pattern matching: `202509*` (matches 20250901, 20250927, etc.)
- **Negative Keywords** - Exclude messages with minus sign: `python -async`
- **Date Filtering** - Natural language date parsing: `from last week`, `yesterday`, `January 2024`
- **Regex Support** - Optional regex mode for advanced pattern matching
- **Combined Queries** - Mix and match all search features in one query

### 🧵 Thread View & Management
- **Complete Conversation Threads** - View entire conversations in chat-like interface
- **Thread Navigation** - Click "View Thread" on any message to see full conversation
- **Thread Filtering** - Search within specific conversation threads
- **Color-coded Messages** - Visual distinction between User, Assistant, and Tool messages
- **Thread Export** - Export complete conversations as Markdown files

### 📊 Export Capabilities
- **Search Results Export** - Download all search results as Markdown
- **Thread Export** - Export complete conversation threads
- **Timestamped Files** - Automatic filename generation with timestamps
- **Clean Formatting** - Well-structured Markdown output with metadata

### 🎨 User Interface
- **Modern Web Interface** - Clean, responsive design
- **Real-time Search** - Instant search results with loading indicators
- **Search Help** - Built-in examples and syntax guidance
- **Keyboard Shortcuts** - Enter key support for quick searching
- **Mobile Friendly** - Responsive design works on all devices

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- A ChatGPT export JSON file from your account

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Jsgordon420365/chatgpt-export.git
   cd chatgpt-export
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Export your ChatGPT data**
   - Go to [ChatGPT Settings](https://chat.openai.com/settings)
   - Navigate to "Data controls" → "Export data"
   - Download your data as JSON format
   - Save the file (e.g., `chatgpt_export.json`)

4. **Create the database**
   ```bash
   python create_database.py chatgpt_export.json chatgpt_export.db
   ```

5. **Start the web server**
   ```bash
   python app.py
   ```

6. **Open your browser**
   Navigate to `http://localhost:5001`

## 📖 Usage Guide

### Basic Search

1. **Enter your search query** in the search box
   - Keywords: `python async programming`
   - Exact phrases: `"machine learning algorithms"`
   - Wildcards: `202509*` (matches dates starting with 202509)
   - Exclusions: `python -tutorial` (finds python but excludes tutorial)

2. **Select result limit** (10, 25, 50, 100, or all)

3. **Click Search** or press Enter

### Advanced Search Examples

| Search Type | Example | What It Does |
|-------------|---------|--------------|
| **Basic** | `python` | Finds messages containing "python" |
| **Exact Phrase** | `"python programming"` | Finds exact phrase "python programming" |
| **Wildcard** | `202509*` | Finds messages with dates starting with "202509" |
| **Negative** | `python -async` | Finds "python" but excludes "async" |
| **Combined** | `"machine learning" 202509* -tutorial` | Exact phrase + wildcard + exclusion |
| **Date** | `from last week` | Finds messages from the past week |
| **Regex** | `^python.*async$` | Advanced pattern matching (enable regex mode) |

### Thread View

1. **Click "View Thread"** on any message in search results
2. **Browse the conversation** in chronological order
3. **Filter within thread** using the filter box
4. **Export the thread** using the "Export Thread" button

### Export Options

- **Export All Results** - Download all search results as Markdown
- **Export Selected** - Select specific messages and export them
- **Export Thread** - Export complete conversation threads
- **Individual Export** - Export single messages

## 🔧 API Endpoints

### Search API
- `GET /search?query=<query>&limit=<limit>&regex=<true/false>`
  - `query`: Search terms (supports all search features)
  - `limit`: Number of results (10, 25, 50, 100, or 'all')
  - `regex`: Enable regex mode (true/false)

### Export API
- `GET /export?query=<query>&limit=<limit>&regex=<true/false>`
  - Downloads search results as Markdown file

### Thread API
- `GET /thread/<conversation_id>` - Get all messages in a conversation
- `GET /thread/<conversation_id>/view` - Thread view page
- `GET /thread/<conversation_id>/export` - Export thread as Markdown

## 📁 File Structure

```
chatgpt-export/
├── app.py                 # Flask web application
├── create_database.py     # Database creation script
├── requirements.txt       # Python dependencies
├── static/
│   ├── index.html        # Main search interface
│   └── thread.html       # Thread view page
├── chatgpt_export.db     # SQLite database (created after setup)
└── README.md            # This file
```

## 🗄️ Database Schema

The tool creates a SQLite database with the following structure:

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    conversation_id TEXT,
    timestamp TEXT,
    sender TEXT,           -- 'user', 'assistant', or 'tool'
    text TEXT             -- Message content
);
```

## 🛠️ Configuration

### Environment Variables
- `FLASK_ENV` - Set to 'development' for debug mode
- `PORT` - Server port (default: 5001)

### Customization
- Modify `static/index.html` for UI changes
- Update `app.py` for backend functionality
- Adjust `create_database.py` for data processing

## 🐛 Troubleshooting

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
   - Change the port in `app.py` if needed: `app.run(debug=False, port=5002)`

5. **Thread view not loading**
   - Check browser console for JavaScript errors
   - Ensure the conversation ID is valid
   - Verify the thread API endpoint is working

### Performance Tips

- For large exports (10,000+ messages), the initial database creation may take several minutes
- Use result limits for faster searches on large datasets
- The database is optimized for text search with word boundary matching
- Consider using regex mode for complex pattern matching

## 🔒 Privacy & Security

- **Local Processing**: All data processing happens locally on your machine
- **No External Servers**: Your conversations are never sent to external servers
- **Secure Database**: SQLite database is stored locally and encrypted by default
- **No Data Collection**: The tool does not collect or store any usage data

## 🚀 Development

### Adding New Features

The codebase is structured for easy extension:

- **Backend**: Modify `app.py` for new API endpoints
- **Frontend**: Update `static/index.html` and `static/thread.html` for UI changes
- **Database**: Extend `create_database.py` for new data fields

### Dependencies

- **Flask**: Web framework
- **SQLite3**: Database (built into Python)
- **dateparser**: Natural language date parsing
- **python-dateutil**: Date utilities

### Running in Development

```bash
# Enable debug mode
export FLASK_ENV=development
python app.py
```

## 📝 License

This project is open source. Feel free to modify and distribute according to your needs.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests for improvements.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

If you encounter any issues or have questions:

1. Check the troubleshooting section above
2. Review the GitHub issues
3. Create a new issue with detailed information about your problem

## 🎯 Roadmap

- [ ] Full-text search indexing for better performance
- [ ] Conversation analytics and insights
- [ ] Bulk export options
- [ ] Advanced filtering options
- [ ] Conversation tagging system
- [ ] Search history and saved searches
- [ ] Dark mode theme
- [ ] Mobile app version

---

**Note**: This tool processes your ChatGPT data locally. Your conversations are never sent to external servers, ensuring your privacy and data security.