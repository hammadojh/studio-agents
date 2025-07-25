# LangGraph Agent System - Web Interface

A real-time web interface for the LangGraph Agent System with WebSocket streaming, session management, and interactive client support.

## 🌟 Features

- **Real-time Communication**: WebSocket-based streaming for instant updates
- **Session Management**: Multiple concurrent users with isolated sessions
- **Live Processing**: Watch the agent's thinking process in real-time
- **Beautiful UI**: Modern, responsive interface with status indicators
- **Mobile Responsive**: Works seamlessly on desktop and mobile devices
- **Health Monitoring**: Built-in health checks and session management endpoints

## 🚀 Quick Start

### From Root Directory
```bash
# Start the web interface (recommended)
python start_web_interface.py
```

### From Web Interface Directory
```bash
# Navigate to web interface directory
cd web_interface

# Start the server directly
python run_server.py
```

### Manual Start
```bash
# From web_interface directory
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📡 Endpoints

Once running, the web interface provides these endpoints:

### Web Interface
- **Main Interface**: http://localhost:8000
- **WebSocket**: ws://localhost:8000/ws

### API Endpoints
- **Health Check**: http://localhost:8000/health
- **Sessions Info**: http://localhost:8000/sessions
- **Session Count**: http://localhost:8000/session-count

## 🔧 Architecture

### Core Components

#### `main.py`
The FastAPI server with WebSocket support including:
- **SessionManager**: Handles multiple user sessions with isolated agent instances
- **WebSocket Handler**: Manages real-time communication with clients
- **LangGraph Integration**: Streams agent execution in real-time
- **Error Handling**: Comprehensive error management and user feedback

#### `run_server.py`
Server launcher with:
- **Dependency Checking**: Validates required packages
- **Environment Validation**: Checks API keys and configuration
- **Server Configuration**: Optimized uvicorn settings
- **User-friendly Output**: Clear status messages and instructions

### Session Management

Each user gets:
- **Unique Session ID**: UUID-based session identification
- **Isolated Agent Instance**: Separate LangGraphAgentSystem per user
- **Message History**: Tracked conversation history
- **WebSocket Connection**: Persistent real-time connection

## 🔌 WebSocket Protocol

### Message Format
```json
{
  "type": "message_type",
  "data": { ... },
  "session_id": "uuid",
  "timestamp": "iso_datetime"
}
```

### Client → Server Messages
```json
{
  "type": "user_message",
  "data": {
    "message": "User's request"
  }
}
```

### Server → Client Messages

#### Status Updates
```json
{
  "type": "status",
  "data": {
    "status": "processing|completed|error",
    "message": "Status description"
  }
}
```

#### Agent Steps
```json
{
  "type": "agent_step", 
  "data": {
    "step": "route_analysis|clarification|code_execution|...",
    "content": "Step details",
    "thinking": "Agent's reasoning process"
  }
}
```

#### Final Results
```json
{
  "type": "final_result",
  "data": {
    "route_taken": "clarify|code|answer",
    "result": "Final agent response",
    "processing_steps": [...],
    "session_stats": { ... }
  }
}
```

## 🛠️ Development

### Dependencies
```bash
pip install fastapi uvicorn websockets
```

### Environment Variables
```bash
export OPENAI_API_KEY=your_openai_api_key_here
export ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Optional
```

### Running in Development Mode
```bash
# With auto-reload
python run_server.py

# Or manually with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Session Monitoring

### Session Information Endpoint
`GET /sessions` returns:
```json
{
  "active_sessions": 3,
  "sessions": {
    "session_id_1": {
      "created_at": "2024-01-01T12:00:00",
      "message_count": 5,
      "last_activity": "2024-01-01T12:05:00"
    }
  }
}
```

### Health Check
`GET /health` returns server status and configuration.

## 🔄 Integration with LangGraph Agent

The web interface integrates seamlessly with the main LangGraph Agent System:

1. **Agent Initialization**: Each session creates a fresh `LangGraphAgentSystem` instance
2. **Streaming Execution**: Real-time streaming of agent processing steps
3. **State Management**: Maintains conversation history and processing context
4. **Error Handling**: Graceful error handling with user-friendly messages

## 🎨 UI Features

- **Real-time Chat Interface**: Messages appear instantly via WebSocket
- **Processing Indicators**: Visual feedback during agent thinking
- **Status Updates**: Clear indication of current processing step
- **Responsive Design**: Works on all device sizes
- **Session Persistence**: Maintains conversation history per session

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill process using port 8000
   lsof -ti:8000 | xargs kill -9
   ```

2. **Missing Dependencies**
   ```bash
   pip install -r ../requirements.txt
   ```

3. **Environment Variables**
   ```bash
   # Check if variables are set
   echo $OPENAI_API_KEY
   ```

### Debug Mode
- Check `/health` endpoint for server status
- Monitor `/sessions` for active connections
- Review console output for detailed error messages

## 📈 Performance

- **Concurrent Users**: Supports multiple simultaneous sessions
- **Memory Management**: Automatic session cleanup for inactive connections
- **Streaming**: Real-time updates without polling
- **Error Recovery**: Graceful handling of connection failures

## 🔮 Future Enhancements

- [ ] Authentication and user management
- [ ] Conversation history persistence
- [ ] File upload support for Claude Code
- [ ] Advanced UI with syntax highlighting
- [ ] Session sharing and collaboration
- [ ] Custom themes and preferences

## 📚 Related Documentation

- **Main Project**: See `../README.md` for full system overview
- **Web Interface Guide**: See `../docs/web_interface_guide.md`
- **LangGraph Agent**: See `../langgraph_agent_system.py`

---

**🌐 Access the Web Interface**: http://localhost:8000 