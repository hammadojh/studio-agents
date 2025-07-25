Here's a complete **implementation guide** for integrating **WebSockets** between a **LangGraph backend** and a **web client** to stream LangGraph output in real time.

---

## ✅ GOAL

Create a **real-time chat interface** where:

* The frontend sends user input via WebSocket.
* The server streams back LangGraph steps using `graph.stream(...)`.
* The client renders each streamed update (e.g., thoughts, tool use, assistant replies) as they arrive.

---

## 🧩 STACK

* **Backend**: FastAPI + LangGraph
* **Frontend**: Vanilla JS (can adapt to React, Next.js later)
* **Transport**: WebSocket

---

## 1️⃣ BACKEND (FastAPI + LangGraph WebSocket Server)

### 📁 `main.py`

```python
from fastapi import FastAPI, WebSocket
from langgraph.graph import Graph
import json

app = FastAPI()

# 1. Create a simple LangGraph (replace with yours)
graph = Graph(state={"messages": list})  # define your LangGraph properly

# 2. Store session states (use Redis for production)
state_store = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    while True:
        try:
            data = await websocket.receive_text()
            payload = json.loads(data)
            session_id = payload["session_id"]
            user_msg = payload["message"]

            # Load or create state
            state = state_store.get(session_id, {"messages": []})
            state["messages"].append({"role": "user", "content": user_msg})

            # 3. Stream LangGraph output
            async for step in graph.stream(state):
                await websocket.send_text(json.dumps(step))

            # Save updated state
            state_store[session_id] = step  # step contains the new state
        except Exception as e:
            print(f"Error: {e}")
            await websocket.close()
            break
```

### ✅ Run with:

```bash
uvicorn main:app --reload
```

---

## 2️⃣ FRONTEND (Vanilla HTML + JS WebSocket)

### 📁 `index.html`

```html
<!DOCTYPE html>
<html>
<head>
  <title>LangGraph Chat</title>
</head>
<body>
  <h1>LangGraph Chat</h1>
  <div id="chat"></div>
  <input type="text" id="input" placeholder="Type a message..." />
  <button onclick="sendMessage()">Send</button>

  <script>
    const ws = new WebSocket("ws://localhost:8000/ws");

    ws.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const chat = document.getElementById("chat");
      const latest = JSON.stringify(data, null, 2);
      chat.innerHTML += `<pre>${latest}</pre>`;
    };

    function sendMessage() {
      const input = document.getElementById("input");
      const msg = input.value;
      input.value = "";

      ws.send(JSON.stringify({
        session_id: "user-123",  // Use unique ID per user
        message: msg
      }));
    }
  </script>
</body>
</html>
```

---

## 🔄 Streaming Output Format

Each message from the backend is a **LangGraph step**, e.g.:

```json
{
  "messages": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello!"}
  ],
  "state": {...},
  "next": "choose_tool"
}
```

You can:

* Display assistant response (`role: assistant`)
* Show reasoning steps (`next`, internal state)
* Animate thinking or tool usage

---

## 🔒 PRODUCTION TIPS

* Use `uuid` or JWTs for secure session IDs.
* Use **Redis** or **PostgreSQL** to persist session state.
* Add **timeout handling** and **ping/pong** to keep WebSocket alive.

---

## ✅ Summary

| Component     | Tech             | Description                         |
| ------------- | ---------------- | ----------------------------------- |
| Backend       | FastAPI          | Hosts WebSocket and LangGraph logic |
| Frontend      | HTML + JS        | WebSocket client to send/receive    |
| State storage | Dict / Redis     | Keeps per-session chat history      |
| Stream logic  | `graph.stream()` | Sends steps in real-time            |

---

Let me know if you want a **React** version or to deploy this to **Vercel + Backend**!
