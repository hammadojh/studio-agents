# LangGraph Agent System — Implementation Guide

This guide helps you implement a LangGraph-powered AI assistant that:
- Accepts vague user prompts
- Engages in multi-turn clarification (if needed)
- Refines the clarified prompt
- Routes the task to either a Claude Code agent (for code actions) or an LLM (for answers)
- Returns the final result

---

## 1. Project Structure

```
my-langgraph-app/
├── main.py
├── graph.yaml              # Optional YAML graph definition
├── nodes/
│   ├── clarify.py          # Clarifier agent (multi-turn)
│   ├── route.py            # Prompt router
│   ├── refine.py           # Refine clarified prompt
│   ├── run_claude.py       # Claude Code SDK runner
│   └── answer.py           # Direct answer agent
├── utils/
│   ├── state.py            # State management helpers
│   └── tools.py            # Tool call functions
└── requirements.txt
```

---

## 2. Setup

### Dependencies
```bash
pip install langgraph langchain openai anthropic
```

Add Claude Code CLI SDK to your machine and ensure it's available via the `claude` command.

Set env vars:
```bash
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
```

---

## 3. Graph Logic Overview

### Nodes:
- `get_user_input` (input node)
- `clarify_loop` (LLM node with memory loop)
- `route_prompt` (LLM or rule-based)
- `refine_prompt` (LLM to polish task)
- `run_claude_code` (tool node)
- `answer_with_llm` (LLM node)
- `display_result` (output node)

### State:
```json
{
  "user_input": "...",
  "clarified": false,
  "conversation_history": [],
  "refined_prompt": "...",
  "route": "clarify" / "code" / "answer"
}
```

---

## 4. Key Implementation Files

### clarify.py
Uses GPT-4o to ask follow-up questions and track clarification state.

### route.py
Uses GPT-4o to classify the prompt as either:
- Clarify (unclear)
- Code action (Claude Code)
- Answer (send to LLM)

### refine.py
Takes clarified idea and turns it into a Claude Code-compatible task prompt.

### run_claude.py
Runs the Claude Code CLI via subprocess with the given prompt file.
Parses JSON result or returns fallback text.

### answer.py
Uses GPT-4o or Claude 3.5 to answer the user directly.

---

## 5. Running the Graph (Python API)

```python
from langgraph.graph import StateGraph
from nodes import clarify, route, refine, run_claude, answer

builder = StateGraph()
builder.add_node("clarify_loop", clarify)
builder.add_node("route_prompt", route)
builder.add_node("refine_prompt", refine)
builder.add_node("run_claude_code", run_claude)
builder.add_node("answer_with_llm", answer)

builder.set_entry_node("route_prompt")
builder.add_conditional_edges("route_prompt", lambda s: s["route"], {
    "clarify": "clarify_loop",
    "code": "run_claude_code",
    "answer": "answer_with_llm"
})

builder.add_conditional_edges("clarify_loop", lambda s: s["clarified"], {
    False: "clarify_loop",
    True: "refine_prompt"
})

builder.add_edge("refine_prompt", "run_claude_code")
builder.set_finish_node("run_claude_code")
builder.set_finish_node("answer_with_llm")

graph = builder.compile()
result = graph.invoke({"user_input": "I want to build an app for shops"})
```

---

## 6. Defining the Graph in YAML (Optional)

LangGraph also supports defining the graph in YAML and loading it in Python. Example:

### graph.yaml
```yaml
nodes:
  route_prompt:
    type: llm
    model: gpt-4o
  clarify_loop:
    type: llm
    model: gpt-4o
  refine_prompt:
    type: llm
    model: gpt-4o
  run_claude_code:
    type: tool
    function: run_claude_code
  answer_with_llm:
    type: llm
    model: gpt-4o

edges:
  - from: route_prompt
    to: clarify_loop
    condition: "{{ route == 'clarify' }}"
  - from: route_prompt
    to: run_claude_code
    condition: "{{ route == 'code' }}"
  - from: route_prompt
    to: answer_with_llm
    condition: "{{ route == 'answer' }}"
  - from: clarify_loop
    to: clarify_loop
    condition: "{{ clarified == false }}"
  - from: clarify_loop
    to: refine_prompt
    condition: "{{ clarified == true }}"
  - from: refine_prompt
    to: run_claude_code
```

### Python to load YAML graph
```python
from langgraph.graph import Graph

with open("graph.yaml") as f:
    yaml_graph = f.read()

graph = Graph.load_yaml(yaml_graph, functions={"run_claude_code": run_claude})
result = graph.invoke({"user_input": "I want to build a finance app"})
```

---

## 7. Logging, Error Handling, Versioning
- Add `try/except` blocks around Claude Code execution.
- Store conversation history, route decisions, and outputs in a database for each user/project.
- Add Git commit calls before/after Claude edits.
- Tie user ID to graph state.

---

## 8. Next Steps
- Add vector memory or summaries to reduce token use
- Integrate with project dashboards
- Add agents for testing, deployment, design feedback

---

Let me know if you want this scaffold exported as a GitHub repo or zipped starter project.

