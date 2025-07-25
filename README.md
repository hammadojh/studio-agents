# LangGraph Agent System

A comprehensive LangGraph-powered AI assistant that intelligently routes user requests through clarification, code generation, or direct answering workflows.

## 🚀 Features

- **Intelligent Routing**: Automatically classifies requests as needing clarification, code generation, or direct answers
- **Multi-turn Clarification**: Engages in conversation to understand vague requests
- **Prompt Refinement**: Polishes clarified requests into actionable prompts
- **Claude Code Integration**: Ready for Claude Code CLI integration (placeholder implemented)
- **Direct LLM Answers**: Provides informational responses using GPT-4o
- **Interactive Mode**: Command-line interface for testing and demonstration

## 📋 System Architecture

```
User Input
    ↓
Route Analysis (GPT-4o)
    ↓
┌─────────────┬─────────────┬─────────────┐
│  CLARIFY    │    CODE     │   ANSWER    │
│     ↓       │     ↓       │     ↓       │
│ Multi-turn  │  Refine     │  Direct     │
│ Questions   │  Prompt     │  LLM        │
│     ↓       │     ↓       │  Answer     │
│ Refinement  │  Claude     │             │
│     ↓       │  Code       │             │
│ Claude Code │ (Placeholder)│             │
└─────────────┴─────────────┴─────────────┘
```

## 🛠️ Installation

### 1. Clone and Setup
```bash
git clone <your-repo>
cd studio-agents
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Environment Variables
```bash
export OPENAI_API_KEY=your_openai_api_key_here
export ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Optional for now
```

### 4. (Optional) Install Claude Code CLI
Follow the official Claude Code installation instructions to enable the code generation features.

## 🎮 Usage

### Quick Start
```bash
python langgraph_agent_system.py
```

This will:
1. Run example requests to demonstrate the system
2. Start interactive mode for hands-on testing

### Programmatic Usage
```python
from langgraph_agent_system import LangGraphAgentSystem

# Initialize the system
agent = LangGraphAgentSystem()

# Process a request
result = agent.process_request("Build a web app for inventory management")

print(f"Route taken: {result['route_taken']}")
print(f"Final result: {result['final_result']}")
```

## 📝 Example Requests

### Clarification Examples (→ Multi-turn Questions)
- "I want to build something"
- "Help me with my project" 
- "I need an app"

### Code Examples (→ Claude Code Integration)
- "Build a web app for inventory management"
- "Create a Python script to analyze CSV data"
- "Add user authentication to my React app"

### Answer Examples (→ Direct LLM Response)
- "What is the best way to deploy a web app?"
- "Explain how JWT authentication works"
- "What are the pros and cons of React vs Vue?"

## 🏗️ System Components

### Core Components
- **`AgentState`**: Central state management with conversation history and routing decisions
- **`LLMManager`**: Centralized LLM interactions with error handling
- **Routing Nodes**: Intelligent classification and workflow management

### Processing Nodes
1. **`route_prompt`**: Analyzes and classifies user requests
2. **`clarify_loop`**: Handles multi-turn clarification conversations
3. **`refine_prompt`**: Polishes requests into actionable prompts
4. **`run_claude_code`**: Executes code generation (placeholder)
5. **`answer_with_llm`**: Provides direct informational answers

### State Flow
Each request flows through the system maintaining:
- Conversation history
- Processing steps (for debugging)
- Route decisions
- Clarification status
- Final results and any errors

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for GPT-4o interactions
- `ANTHROPIC_API_KEY`: Optional, for future Claude integration

### Customization Options
- Model selection in `LLMManager`
- Clarification loop limits
- Token limits for responses
- System prompts for each node

## 🎯 Next Steps

### Claude Code Integration
The system is ready for Claude Code CLI integration. To implement:

1. Install Claude Code CLI
2. Uncomment the implementation in `run_claude_code()` function
3. Test with code generation requests

### Enhancements
- Vector memory for conversation context
- Database persistence for conversation history
- Web interface for easier interaction
- Additional routing categories
- Custom tool integrations

## 🐛 Troubleshooting

### Common Issues
1. **Missing API Keys**: Ensure environment variables are set correctly
2. **Import Errors**: Install all dependencies with `pip install -r requirements.txt`
3. **Model Errors**: Check API key permissions and quotas

### Debug Mode
The system tracks processing steps in `state.processing_steps` for debugging routing decisions and node execution.

## 📊 System Status

- ✅ State Management
- ✅ Intelligent Routing  
- ✅ Multi-turn Clarification
- ✅ Prompt Refinement
- ✅ Direct LLM Answers
- ✅ Interactive Interface
- 🔄 Claude Code Integration (Placeholder)
- 🔄 Vector Memory (Future)
- 🔄 Web Interface (Future)

## 📚 Documentation

Each component is thoroughly documented with:
- Purpose and functionality
- Input/output specifications  
- Error handling approaches
- Integration points for extensions

The system is designed to be modular and extensible, making it easy to add new routing categories, processing nodes, or integration points as needed. 