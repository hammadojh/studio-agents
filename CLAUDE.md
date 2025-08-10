# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LangGraph-powered AI assistant system that intelligently routes user requests through clarification, code generation, or direct answering workflows. The system integrates multiple AI models (OpenAI GPT-4o and Anthropic Claude) through a sophisticated routing mechanism.

## Key Commands

### Setup and Dependencies
```bash
pip install -r requirements.txt
export OPENAI_API_KEY=your_openai_api_key_here
export ANTHROPIC_API_KEY=your_anthropic_api_key_here
npm install -g @anthropic-ai/claude-code  # Claude Code CLI integration
```

### Running the System
```bash
# Main agent system (CLI interface with examples)
python langgraph_agent_system.py

# Web interface with WebSocket streaming
python start_web_interface.py
# or
python web_interface/run_server.py

# Generate workflow visualizations
python visualize_graph.py

# Demo Claude Code integration
python demo_claude_code.py
```

### Development and Testing
The system doesn't include specific test commands - testing is done through the interactive CLI mode and web interface.

## Architecture Overview

### Core System Components

**LangGraph Agent System** (`langgraph_agent_system.py`):
- Main orchestrator using LangGraph state management
- Routes requests through three paths: CLARIFY → CODE → ANSWER
- Uses `AgentState` TypedDict for conversation tracking
- Integrates directly with Claude Code CLI for live code generation

**Web Interface** (`web_interface/`):
- FastAPI server with WebSocket streaming support
- Session management for concurrent users
- Real-time updates during agent processing
- Modern responsive HTML/CSS/JS frontend

**Processing Workflows**:
1. **Route Analysis**: GPT-4o classifies incoming requests
2. **Clarification Path**: Multi-turn conversations for vague requests
3. **Code Generation Path**: Direct Claude Code CLI integration with streaming
4. **Direct Answer Path**: GPT-4o responses for informational queries

### Key Files and Structure

- `langgraph_agent_system.py` - Core LangGraph agent implementation
- `web_interface/main.py` - FastAPI web server with WebSocket support
- `web_interface/run_server.py` - Server launcher
- `start_web_interface.py` - Web interface starter script
- `docs/` - Comprehensive architecture documentation
- `*.mmd` files - Mermaid diagrams for system visualization

### State Management

The system uses `AgentState` TypedDict with:
- `messages`: Conversation history
- `processing_steps`: Debug/monitoring information  
- `route_taken`: Which processing path was used
- `clarification_complete`: Multi-turn conversation status
- `final_result`: Output from processing

### External Integrations

**OpenAI GPT-4o**: Route analysis, clarification questions, prompt refinement, direct answers
**Claude Code CLI**: Live code generation with full permissions (`--dangerously-skip-permissions`)
**LangSmith**: Optional observability and monitoring

### Claude Code Integration Details

The system includes sophisticated Claude Code CLI integration with:
- Streaming output parsing for real-time updates
- Human-readable tool action descriptions
- Progress indicators for thinking vs. action phases
- Complete permissions for file system access
- Performance metrics (duration, cost, turns)

### Web Interface Protocol

WebSocket endpoints at `/ws/{session_id}` for real-time communication:
- Session-based isolation for concurrent users
- Streaming agent processing updates
- JSON message protocol for request/response handling

## Development Notes

### Adding New Processing Paths
Extend the routing logic in `route_prompt` node and add corresponding processing nodes to the LangGraph workflow.

### Modifying LLM Interactions
The `LLMManager` class centralizes all model interactions with error handling and retry logic.

### Web Interface Extensions
FastAPI server supports standard REST endpoints alongside WebSocket streaming - both use the same core agent system.

### Configuration Options
- Model selection in `LLMManager` class
- Clarification loop limits  
- Token limits for responses
- System prompts for each processing node

The system is designed for modularity and extensibility, with clear separation between routing logic, processing workflows, and external service integrations.