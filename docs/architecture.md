# LangGraph Agent System - Architecture Documentation

## 🏗️ System Overview

The LangGraph Agent System is a comprehensive AI assistant platform built with a modular, layered architecture that supports both command-line and web-based interactions. The system intelligently routes user requests through different processing paths while maintaining state and providing real-time feedback.

## 📐 Architecture Layers

### 1. 🌐 User Interface Layer

**Components:**
- **Web Browser Interface**: Modern, responsive web UI with real-time chat
- **Command Line Interface**: Direct Python script execution for testing and automation

**Key Features:**
- Real-time WebSocket communication
- Responsive design for desktop and mobile
- Interactive chat interface with status indicators
- Direct command-line access for developers

### 2. ⚡ Web Interface Layer

**Components:**
- **FastAPI Server** (`web_interface/main.py`): ASGI web server with WebSocket support
- **Session Manager**: Multi-user session isolation and management
- **WebSocket Handler**: Real-time bidirectional communication
- **Health & Status Monitoring**: System health checks and metrics

**Key Features:**
- **Session Isolation**: Each user gets their own agent instance
- **Real-time Streaming**: Live updates of agent processing steps
- **Concurrent Users**: Support for multiple simultaneous users
- **Error Handling**: Graceful error recovery and user feedback
- **Health Monitoring**: Built-in endpoints for system monitoring

**Endpoints:**
- `GET /`: Main web interface
- `WS /ws`: WebSocket endpoint for real-time communication
- `GET /health`: System health check
- `GET /sessions`: Active session information
- `GET /session-count`: Current user count

### 3. 🤖 Core Agent System (LangGraph)

**Components:**
- **Route Analysis**: Intelligent request classification using GPT-4o
- **Processing Paths**: Three distinct workflows based on request type
- **State Management**: Conversation history and processing context
- **Node Orchestration**: LangGraph-powered workflow management

**Processing Paths:**

#### ❓ Clarification Path
- **Trigger**: Vague or unclear requests
- **Process**: Multi-turn clarification conversations
- **Output**: Refined, actionable requests
- **Components**:
  - Clarify Loop: Interactive question generation
  - Refine Prompt: Polish clarified requests

#### 💻 Code Generation Path  
- **Trigger**: Requests for code creation or modification
- **Process**: Prompt refinement → Claude Code execution
- **Output**: Live code generation with streaming feedback
- **Components**:
  - Refine Prompt: Prepare code-ready prompts
  - Claude Code CLI: Live code execution with full permissions

#### 💬 Direct Answer Path
- **Trigger**: Informational questions or explanations
- **Process**: Direct LLM response generation
- **Output**: Comprehensive answers using GPT-4o
- **Components**:
  - Answer with LLM: Direct response generation

### 4. 🌍 External Services Layer

**Services:**
- **OpenAI API (GPT-4o)**: Powers routing, clarification, refinement, and direct answers
- **Anthropic API (Claude)**: Used by Claude Code CLI for code generation
- **NPM/Claude CLI**: Command-line tool for live code execution

**Integration Features:**
- **API Key Management**: Secure credential handling
- **Error Handling**: Graceful API failure recovery
- **Rate Limiting**: Automatic retry and backoff mechanisms
- **Streaming Support**: Real-time response streaming where available

### 5. 💾 State & Data Layer

**Components:**
- **Agent State**: Per-session conversation history and processing context
- **Session Store**: Multi-user session data isolation
- **Processing Steps**: Detailed execution logs for debugging
- **Message History**: Complete conversation tracking

**State Features:**
- **Persistence**: Maintains context throughout conversations
- **Isolation**: Separate state per user session
- **History Tracking**: Complete conversation and processing logs
- **Debug Information**: Detailed step-by-step execution traces

## 🔄 Data Flow

### 1. Web Interface Flow
```
User Browser → WebSocket → FastAPI Server → Session Manager → Agent Instance
```

### 2. Agent Processing Flow
```
User Input → Route Analysis → [Clarify|Code|Answer] Path → External APIs → Response
```

### 3. State Management Flow
```
Request → Update State → Process → Update State → Response → Store History
```

## 🔌 Communication Protocols

### WebSocket Message Types

#### Client → Server
```json
{
  "type": "user_message",
  "data": {
    "message": "User's request"
  }
}
```

#### Server → Client
```json
{
  "type": "status|agent_step|final_result",
  "data": { /* Type-specific data */ },
  "session_id": "uuid",
  "timestamp": "iso_datetime"
}
```

### HTTP Endpoints
- **RESTful APIs**: Standard HTTP methods for health checks and session info
- **Static Files**: Web interface assets served via FastAPI
- **Error Responses**: Standardized error format with helpful messages

## 🛡️ Security & Reliability

### Security Features
- **Session Isolation**: Complete separation between user sessions
- **API Key Protection**: Secure credential management
- **Input Validation**: Request sanitization and validation
- **Error Handling**: No sensitive data in error messages

### Reliability Features
- **Graceful Degradation**: Fallback mechanisms for API failures
- **Connection Recovery**: Automatic WebSocket reconnection
- **Session Cleanup**: Automatic cleanup of inactive sessions
- **Health Monitoring**: Proactive system health checks

## 📊 Performance Characteristics

### Scalability
- **Concurrent Users**: Supports multiple simultaneous sessions
- **Memory Management**: Efficient session lifecycle management
- **Connection Pooling**: Optimized API connection handling
- **Async Processing**: Non-blocking I/O for better performance

### Response Times
- **WebSocket Communication**: Real-time, sub-second updates
- **API Response Times**: Dependent on external service performance
- **Session Management**: Optimized for quick session creation/retrieval
- **State Updates**: Minimal overhead for state persistence

## 🔮 Extension Points

### Adding New Processing Paths
1. Create new LangGraph nodes
2. Update routing logic
3. Add corresponding WebSocket message types
4. Update web interface handlers

### Custom Integrations
1. Extend external services layer
2. Add new API clients
3. Update state management for new data types
4. Add monitoring and health checks

### UI Enhancements
1. Extend FastAPI endpoints
2. Add new WebSocket message types
3. Update session management for new features
4. Enhance web interface components

## 📚 Related Documentation

- **Main README**: `../README.md` - Project overview and setup
- **Web Interface Guide**: `web_interface_guide.md` - Detailed web interface documentation
- **LangGraph Implementation**: `../langgraph_agent_system.py` - Core agent code
- **Web Interface Code**: `../web_interface/main.py` - FastAPI server implementation

---

This architecture provides a robust, scalable foundation for AI-powered assistance with excellent separation of concerns, real-time capabilities, and extensibility for future enhancements. 