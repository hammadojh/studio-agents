# LangGraph Agent System - Web Interface Guide

A real-time web interface for the LangGraph Agent System with WebSocket streaming and beautiful UI.

## 🌟 Features

- **Real-time Communication**: WebSocket-based streaming for instant updates
- **Session Management**: Multiple concurrent users with isolated sessions
- **Beautiful UI**: Modern, responsive interface with real-time status indicators
- **Smart Routing**: Visual feedback for different processing routes (Code, Answer, Clarify)
- **Processing Visibility**: Live updates showing agent's thinking process
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Mobile Responsive**: Works seamlessly on desktop and mobile devices

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Required
export OPENAI_API_KEY=your_openai_api_key_here

# Optional but recommended
export ANTHROPIC_API_KEY=your_anthropic_api_key_here
export LANGCHAIN_API_KEY=your_langsmith_api_key_here
```

### 3. Start the Server

```bash
# Using the runner script (recommended)
python web_interface/run_server.py

# Or directly with uvicorn
cd web_interface
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Open the Web Interface

Navigate to: **http://localhost:8000**

## 📡 API Endpoints

### HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web interface (HTML client) |
| `/health` | GET | Health check and server status |
| `/sessions` | GET | Active sessions information |

### WebSocket Endpoint

- **URL**: `ws://localhost:8000/ws`
- **Protocol**: JSON message exchange
- **Features**: Real-time bidirectional communication

## 💬 WebSocket Message Protocol

### Client to Server

```json
{
  "session_id": "uuid-string",
  "message": "user message text"
}
```

### Server to Client

#### Session Created
```json
{
  "type": "session_created",
  "data": {"session_id": "uuid-string"},
  "timestamp": "ISO-8601-datetime"
}
```

#### User Message Confirmation
```json
{
  "type": "user_message", 
  "data": {"content": "user message"},
  "timestamp": "ISO-8601-datetime"
}
```

#### Processing Updates
```json
{
  "type": "processing_update",
  "data": {"update": "status message"},
  "timestamp": "ISO-8601-datetime"
}
```

#### Processing Steps
```json
{
  "type": "processing_step",
  "data": {"step": "detailed step description"},
  "timestamp": "ISO-8601-datetime"
}
```

#### Route Decision
```json
{
  "type": "route_decision",
  "data": {"route": "code|answer|clarify"},
  "timestamp": "ISO-8601-datetime"
}
```

#### Final Result
```json
{
  "type": "final_result",
  "data": {"result": "agent response"},
  "timestamp": "ISO-8601-datetime"
}
```

#### Clarification Needed
```json
{
  "type": "clarification_needed",
  "data": {"question": "clarification question"},
  "timestamp": "ISO-8601-datetime"
}
```

#### Error
```json
{
  "type": "error",
  "data": {"error": "error message"},
  "timestamp": "ISO-8601-datetime"
}
```

## 🧪 Testing

### Automated Testing

```bash
# Run full test suite
python web_interface/test_api.py

# Run quick tests only
python web_interface/test_api.py --quick

# Test different host/port
python web_interface/test_api.py --host localhost --port 8000
```

### Manual Testing

1. **Basic Functionality**
   - Open http://localhost:8000
   - Send message: "What is Python?"
   - Verify you get a response

2. **Code Generation**
   - Send: "Build a Python web scraper for news articles"
   - Verify routing shows "CODE"
   - Check for detailed response

3. **Clarification**
   - Send: "I want to create something cool"
   - Verify routing shows "CLARIFY"
   - Check for clarification question

## 🏗️ Architecture

### Components

```
┌─────────────────────┐
│   HTML/JS Client    │ ← Browser interface
└─────────┬───────────┘
          │ WebSocket
┌─────────▼───────────┐
│   FastAPI Server    │ ← Web server + WebSocket handler
└─────────┬───────────┘
          │ Direct calls
┌─────────▼───────────┐
│ LangGraph Agent     │ ← Core agent system
└─────────────────────┘
```

### Session Management

- **SessionManager**: Handles multiple concurrent users
- **WebSocketStreamer**: Manages real-time updates
- **Agent Isolation**: Each session has its own agent instance
- **Memory Persistence**: Conversation history maintained per session

### File Structure

```
web_interface/
├── main.py              # FastAPI server with embedded HTML client
├── run_server.py        # Server launcher with dependency checks
├── test_api.py          # Comprehensive testing suite
└── README.md           # This documentation
```

## 🎨 UI Features

### Visual Elements

- **Status Indicators**: Real-time connection and processing status
- **Route Badges**: Color-coded routing decisions
- **Processing Steps**: Live updates of agent's thinking process
- **Message Types**: Distinct styling for user, assistant, and system messages
- **Timestamps**: All messages include timestamps
- **Auto-scroll**: Chat automatically scrolls to latest messages

### User Experience

- **Responsive Design**: Works on desktop and mobile
- **Keyboard Shortcuts**: Enter to send, Shift+Enter for new line
- **Example Prompts**: Click-to-send example messages
- **Session Info**: Current session status and statistics
- **Error Handling**: User-friendly error messages
- **Reconnection**: Automatic reconnection on connection loss

## ⚙️ Configuration

### Environment Variables

```bash
# Required for agent functionality
OPENAI_API_KEY=your_key_here

# Optional for Claude integration  
ANTHROPIC_API_KEY=your_key_here

# Optional for LangSmith tracing
LANGCHAIN_API_KEY=your_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=langraph-agent-system
```

### Server Configuration

The server can be configured by modifying `web_interface/main.py`:

```python
# Change host/port
uvicorn.run(app, host="0.0.0.0", port=8080)

# Enable/disable reload
uvicorn.run(app, reload=False)  # For production

# Adjust log level
uvicorn.run(app, log_level="warning")
```

## 🔧 Troubleshooting

### Common Issues

1. **"Connection failed" error**
   - Check if server is running: `ps aux | grep uvicorn`
   - Verify port is not in use: `lsof -i :8000`
   - Check firewall settings

2. **"Missing dependencies" error**
   - Run: `pip install -r requirements.txt`
   - Check Python version: `python --version` (3.8+ required)

3. **"OpenAI API key not set" error**
   - Set environment variable: `export OPENAI_API_KEY=your_key`
   - Verify key is correct: `echo $OPENAI_API_KEY`

4. **WebSocket connection drops**
   - Check network stability
   - Verify no proxy blocking WebSocket connections
   - Try different browser

### Debug Mode

Enable debug mode for detailed logging:

```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with debug
uvicorn.run(app, debug=True, log_level="debug")
```

## 🚀 Deployment

### Local Development
```bash
python web_interface/run_server.py
```

### Production Deployment

1. **Using Docker** (recommended)
```dockerfile
FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "web_interface.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Using systemd**
```ini
[Unit]
Description=LangGraph Agent Web Interface
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/studio-agents
Environment=OPENAI_API_KEY=your_key
ExecStart=/usr/bin/python web_interface/run_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. **Using reverse proxy (nginx)**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 📚 API Usage Examples

### Python WebSocket Client

```python
import asyncio
import json
import websockets

async def test_client():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        # Wait for session
        session_msg = await websocket.recv()
        session_data = json.loads(session_msg)
        session_id = session_data["data"]["session_id"]
        
        # Send message
        message = {
            "session_id": session_id,
            "message": "What is machine learning?"
        }
        await websocket.send(json.dumps(message))
        
        # Receive responses
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received: {data['type']}")
            
            if data["type"] in ["final_result", "error"]:
                break

# Run the client
asyncio.run(test_client())
```

### JavaScript WebSocket Client

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
    console.log('Connected to LangGraph Agent');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'session_created') {
        // Send a message
        ws.send(JSON.stringify({
            session_id: data.data.session_id,
            message: 'Hello, agent!'
        }));
    } else if (data.type === 'final_result') {
        console.log('Response:', data.data.result);
    }
};
```

### cURL Examples

```bash
# Health check
curl http://localhost:8000/health

# Sessions info
curl http://localhost:8000/sessions

# Get HTML client
curl http://localhost:8000
```

## 🔍 Monitoring and Observability

### Built-in Metrics

- **Active Sessions**: Number of concurrent WebSocket connections
- **Message Count**: Messages processed per session
- **Processing Time**: How long each request takes
- **Error Rates**: Failed requests and error types

### LangSmith Integration

If configured, all agent interactions are automatically traced in LangSmith:

- View traces at: https://smith.langchain.com/
- Project: `langraph-agent-system`
- Detailed execution flows and performance metrics

### Health Monitoring

```bash
# Check server health
curl http://localhost:8000/health

# Monitor active sessions
curl http://localhost:8000/sessions

# Server logs
tail -f /var/log/langraph-agent.log
```

## 🤝 Contributing

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment variables
4. Run tests: `python web_interface/test_api.py`
5. Start development server: `python web_interface/run_server.py`

### Adding Features

1. **New WebSocket message types**: Add to `handleWebSocketMessage()` in the client
2. **New endpoints**: Add to `main.py` with proper error handling
3. **UI improvements**: Modify the embedded HTML/CSS/JS in `get_client()`
4. **Agent enhancements**: Modify the core system in `langgraph_agent_system.py`

### Testing

- Run full test suite before submitting changes
- Add tests for new features
- Verify mobile responsiveness
- Test with multiple concurrent users

---

## 📞 Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: This guide and inline code comments
- **Examples**: Check `test_api.py` for usage examples

Happy coding! 🚀 