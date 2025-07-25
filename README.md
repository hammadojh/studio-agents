# LangGraph Agent System

A comprehensive LangGraph-powered AI assistant that intelligently routes user requests through clarification, code generation, or direct answering workflows.

## 🚀 Features

- **Intelligent Routing**: Automatically classifies requests as needing clarification, code generation, or direct answers
- **Multi-turn Clarification**: Engages in conversation to understand vague requests
- **Prompt Refinement**: Polishes clarified requests into actionable prompts
- **Claude Code Integration**: Full Claude Code CLI integration with streaming output and complete permissions
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
│     ↓       │  Code CLI   │             │
│ Claude Code │ (LIVE)      │             │
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

### 4. Install Claude Code CLI
```bash
# Option 1: Use our helper script
python install_claude_code.py

# Option 2: Manual installation
npm install -g @anthropic-ai/claude-code
```

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
4. **`run_claude_code`**: Executes code generation with Claude Code CLI and streaming output
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

### Claude Code Integration ✅ 
The system now includes full Claude Code CLI integration with:

- **Streaming Output**: Real-time display of Claude's thinking process
- **Full Permissions**: Uses `--dangerously-skip-permissions` for complete access
- **Human-Readable Tool Parsing**: Clear descriptions of what Claude is doing (e.g., "📝 Creating file: app.js" instead of raw tool IDs)
- **Smart Result Parsing**: Converts tool results into meaningful messages (e.g., "✅ File created successfully")
- **Enhanced Progress Visibility**: Shows thinking vs. action phases with appropriate emojis
- **Error Handling**: Comprehensive error handling with helpful messages
- **Performance Metrics**: Displays execution time, cost, and turns used

**Example Output:**
```bash
🟢 Claude Code initialized - Model: claude-sonnet-4-20250514
   Working directory: /Users/user/project
   Permission mode: bypassPermissions

🧠 Claude thinking: I need to create a todo app with HTML, CSS, and JavaScript...
📝 Creating file: index.html
✅ File created successfully
📋 Updating todo list
📝 Creating file: style.css  
✅ File created successfully
📄 Writing file: script.js
✅ File written successfully
🤖 Claude: I've created a complete todo application with...

✅ Claude Code completed successfully!
   Duration: 12.34s | Cost: $0.0234 | Turns: 3
```

**Key Features:**
- 🧠 **Thinking Display**: Shows Claude's reasoning process
- 📝 **Tool Actions**: Human-readable descriptions of file operations
- ✅ **Result Parsing**: Clear success/error messages
- 📋 **Progress Updates**: Real-time feedback on what's happening

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
- ✅ Claude Code Integration (Full Implementation)
- 🔄 Vector Memory (Future)
- 🔄 Web Interface (Future)

## 📚 Documentation

Each component is thoroughly documented with:
- Purpose and functionality
- Input/output specifications  
- Error handling approaches
- Integration points for extensions

The system is designed to be modular and extensible, making it easy to add new routing categories, processing nodes, or integration points as needed. 