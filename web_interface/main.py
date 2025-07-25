"""
FastAPI WebSocket Server for LangGraph Agent System

This server provides a web interface for the LangGraph agent system with:
- Real-time WebSocket communication
- Session management for multiple users
- Streaming LangGraph execution
- Interactive web client support
"""

import asyncio
import json
import uuid
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import the agent system
sys.path.append(str(Path(__file__).parent.parent))

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse
    import uvicorn
except ImportError as e:
    print(f"Missing FastAPI dependencies: {e}")
    print("Please install: pip install fastapi uvicorn websockets")
    sys.exit(1)

# Import the existing LangGraph agent system
from langgraph_agent_system import LangGraphAgentSystem, set_execution_modes

app = FastAPI(title="LangGraph Agent System Web Interface", version="1.0.0")

# Global session store for managing multiple users
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.active_connections: Dict[str, WebSocket] = {}
    
    def create_session(self, websocket: WebSocket) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "agent": LangGraphAgentSystem(),
            "created_at": datetime.now(),
            "message_count": 0
        }
        self.active_connections[session_id] = websocket
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions.get(session_id)
    
    def remove_session(self, session_id: str):
        self.sessions.pop(session_id, None)
        self.active_connections.pop(session_id, None)
    
    def get_connection(self, session_id: str) -> Optional[WebSocket]:
        return self.active_connections.get(session_id)

# Global session manager
session_manager = SessionManager()

class WebSocketStreamer:
    """Custom streamer that sends updates via WebSocket"""
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
    
    async def send_update(self, update_type: str, data: Any):
        """Send a real-time update to the client"""
        try:
            message = {
                "type": update_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            await self.websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"Failed to send WebSocket update: {e}")

@app.get("/")
async def get_client():
    """Serve the HTML client interface"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LangGraph Agent System</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            height: calc(100vh - 40px);
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1em;
        }
        
        .main-content {
            display: flex;
            flex: 1;
            min-height: 0;
        }
        
        .chat-section {
            flex: 2;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #eee;
            min-height: 0;
            overflow: hidden;
        }
        
        .info-section {
            flex: 1;
            padding: 20px;
            background: #f8f9fa;
            overflow-y: auto;
        }
        
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
            min-height: 0;
            height: 100%;
        }
        
        .status-bar {
            padding: 10px 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #eee;
            font-size: 0.9em;
            color: #666;
        }
        
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 8px;
        }
        
        .status-connected { background: #28a745; }
        .status-disconnected { background: #dc3545; }
        .status-processing { background: #ffc107; }
        
        #chat {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 10px;
            margin-bottom: 20px;
            background: #fafafa;
            height: 0; /* Forces flex child to respect flex: 1 */
            scroll-behavior: smooth;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px 16px;
            border-radius: 12px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .message.user {
            background: #007bff;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .message.assistant {
            background: white;
            border: 1px solid #ddd;
            margin-right: auto;
        }
        
        .message.system {
            background: #e9ecef;
            color: #495057;
            font-size: 0.9em;
            font-style: italic;
            text-align: center;
            margin: 10px auto;
            max-width: 60%;
        }
        
        .message.update {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            font-size: 0.85em;
            text-align: center;
            margin: 5px auto;
            max-width: 70%;
        }

        .processing-indicator {
            display: flex;
            align-items: center;
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-left: 4px solid #6c757d;
            border-radius: 8px;
            opacity: 1;
            transition: opacity 0.3s ease;
            animation: pulse 2s infinite;
        }

        .processing-content {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            width: 100%;
        }

        .processing-dots {
            display: flex;
            gap: 0.25rem;
        }

        .processing-dots span {
            width: 6px;
            height: 6px;
            background: #6c757d;
            border-radius: 50%;
            animation: dot-bounce 1.4s infinite ease-in-out both;
        }

        .processing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .processing-dots span:nth-child(2) { animation-delay: -0.16s; }
        .processing-dots span:nth-child(3) { animation-delay: 0s; }

        .processing-text {
            flex: 1;
            color: #495057;
            font-size: 0.9rem;
            transition: opacity 0.15s ease;
        }

        @keyframes dot-bounce {
            0%, 80%, 100% {
                transform: scale(0.8);
                opacity: 0.5;
            }
            40% {
                transform: scale(1);
                opacity: 1;
            }
        }

        @keyframes pulse {
            0% {
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            50% {
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            100% {
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        }
        
        .input-section {
            display: flex;
            gap: 10px;
        }
        
        #messageInput {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            outline: none;
        }
        
        #messageInput:focus {
            border-color: #007bff;
            box-shadow: 0 0 0 3px rgba(0,123,255,0.1);
        }
        
        #sendButton {
            padding: 12px 24px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.2s;
        }
        
        #sendButton:hover:not(:disabled) {
            background: #0056b3;
        }
        
        #sendButton:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        
        .info-card {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #007bff;
        }
        
        .info-card h3 {
            color: #007bff;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .info-card ul {
            list-style: none;
            padding-left: 0;
        }
        
        .info-card li {
            padding: 5px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .info-card li:last-child {
            border-bottom: none;
        }
        
        .route-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .route-code { background: #d4edda; color: #155724; }
        .route-answer { background: #cce5ff; color: #004085; }
        .route-clarify { background: #fff3cd; color: #856404; }
        
        .processing-steps {
            font-size: 0.85em;
            color: #666;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .examples {
            margin-top: 20px;
        }
        
        .example-item {
            background: #f8f9fa;
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .example-item:hover {
            background: #e9ecef;
        }
        
        @media (max-width: 768px) {
            .main-content {
                flex-direction: column;
                height: auto;
            }
            
            .chat-section {
                border-right: none;
                border-bottom: 1px solid #eee;
            }
            
            .info-section {
                max-height: 300px;
            }
        }
        
        .timestamp {
            font-size: 0.7em;
            opacity: 0.7;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 LangGraph Agent System</h1>
            <p>AI Assistant with Real-time Streaming and Smart Routing</p>
        </div>
        
        <div class="status-bar">
            <span class="status-indicator status-disconnected" id="statusIndicator"></span>
            <span id="statusText">Connecting...</span>
            <span style="float: right;" id="sessionInfo">Session: Initializing...</span>
        </div>
        
        <div class="main-content">
            <div class="chat-section">
                <div class="chat-container">
                    <div id="chat"></div>
                    <div class="input-section">
                        <input type="text" id="messageInput" placeholder="Ask me anything..." disabled>
                        <button id="sendButton" disabled>Send</button>
                    </div>
                </div>
            </div>
            
            <div class="info-section">
                <div class="info-card">
                    <h3>🎯 Current Session</h3>
                    <ul>
                        <li><strong>Route:</strong> <span id="currentRoute">None</span></li>
                        <li><strong>Status:</strong> <span id="currentStatus">Ready</span></li>
                        <li><strong>Messages:</strong> <span id="messageCount">0</span></li>
                    </ul>
                </div>
                

                
                <div class="info-card">
                    <h3>💡 How it Works</h3>
                    <ul>
                        <li><span class="route-badge route-clarify">Clarify</span> Vague requests</li>
                        <li><span class="route-badge route-code">Code</span> Development tasks</li>
                        <li><span class="route-badge route-answer">Answer</span> Information requests</li>
                    </ul>
                </div>
                
                <div class="info-card">
                    <h3>🚀 Try These Examples</h3>
                    <div class="examples">
                        <div class="example-item" onclick="sendExample('Build a Python web scraper for news articles')">
                            "Build a Python web scraper for news articles"
                        </div>
                        <div class="example-item" onclick="sendExample('What is the difference between REST and GraphQL?')">
                            "What is the difference between REST and GraphQL?"
                        </div>
                        <div class="example-item" onclick="sendExample('I want to create something cool')">
                            "I want to create something cool"
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let ws = null;
        let sessionId = null;
        let messageCount = 0;
        let isProcessing = false;
        
        const chatDiv = document.getElementById('chat');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        const sessionInfo = document.getElementById('sessionInfo');
        const currentRoute = document.getElementById('currentRoute');
        const currentStatus = document.getElementById('currentStatus');
        const messageCountSpan = document.getElementById('messageCount');

        
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                updateStatus('connected', 'Connected');
                messageInput.disabled = false;
                sendButton.disabled = false;
                addSystemMessage('Connected to LangGraph Agent System');
            };
            
            ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    handleWebSocketMessage(message);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };
            
            ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                updateStatus('disconnected', 'Disconnected');
                messageInput.disabled = true;
                sendButton.disabled = true;
                
                // Handle different close codes
                if (event.code === 1000) {
                    // Normal closure
                    addSystemMessage('Connection closed normally');
                } else if (event.code === 1012) {
                    // Service restart
                    addSystemMessage('Server restarting. Reconnecting...');
                    setTimeout(connectWebSocket, 1000);
                } else {
                    // Other errors
                    addSystemMessage('Connection lost. Attempting to reconnect...');
                    setTimeout(connectWebSocket, 3000);
                }
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                updateStatus('disconnected', 'Connection Error');
            };
        }
        
        function updateStatus(status, text) {
            statusIndicator.className = `status-indicator status-${status}`;
            statusText.textContent = text;
            
            if (status === 'connected') {
                currentStatus.textContent = 'Ready';
            } else if (status === 'processing') {
                currentStatus.textContent = 'Processing...';
            }
        }
        
        function handleWebSocketMessage(message) {
            console.log('Received message:', message);
            
            switch (message.type) {
                case 'session_created':
                    sessionId = message.data.session_id;
                    sessionInfo.textContent = `Session: ${sessionId.substring(0, 8)}...`;
                    break;
                    
                case 'user_message':
                    addUserMessage(message.data.content);
                    updateStatus('processing', 'Processing...');
                    isProcessing = true;
                    sendButton.disabled = true;
                    showProcessingStep('Starting to process your request...');
                    break;
                    
                case 'processing_update':
                    showProcessingStep(message.data.update || message.data);
                    break;
                    
                case 'processing_step':
                    showProcessingStep(message.data.step || message.data);
                    break;
                    
                case 'route_decision':
                    const route = message.data.route || message.data;
                    currentRoute.innerHTML = `<span class="route-badge route-${route}">${route.toUpperCase()}</span>`;
                    // Show route change visually as a processing step
                    showProcessingStep(`🔀 Route determined: ${route.toUpperCase()}`);
                    break;
                    
                case 'final_result':
                    hideProcessingIndicator();
                    addAssistantMessage(message.data.result || message.data);
                    updateStatus('connected', 'Connected');
                    isProcessing = false;
                    sendButton.disabled = false;
                    break;
                    
                case 'clarification_needed':
                    hideProcessingIndicator();
                    const question = message.data.question || message.data;
                    addAssistantMessage(question);
                    updateStatus('connected', 'Waiting for clarification');
                    isProcessing = false;
                    sendButton.disabled = false;
                    break;
                    
                case 'error':
                    hideProcessingIndicator();
                    addSystemMessage(`❌ Error: ${message.data.error || message.data}`, 'error');
                    updateStatus('connected', 'Error occurred');
                    isProcessing = false;
                    sendButton.disabled = false;
                    break;
                    
                default:
                    console.log('Unknown message type:', message.type);
                    addSystemMessage(`📥 Received: ${message.type}`, 'system');
            }
        }
        
        function addUserMessage(content) {
            messageCount++;
            messageCountSpan.textContent = messageCount;
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message user';
            messageDiv.innerHTML = `
                ${content}
                <div class="timestamp">${new Date().toLocaleTimeString()}</div>
            `;
            chatDiv.appendChild(messageDiv);
            scrollToBottom();
        }
        
        function addAssistantMessage(content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message assistant';
            messageDiv.innerHTML = `
                ${content.replace(/\\n/g, '<br>')}
                <div class="timestamp">${new Date().toLocaleTimeString()}</div>
            `;
            chatDiv.appendChild(messageDiv);
            scrollToBottom();
        }
        
        function addSystemMessage(content, type = 'system') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.innerHTML = `
                ${content}
                <div class="timestamp">${new Date().toLocaleTimeString()}</div>
            `;
            chatDiv.appendChild(messageDiv);
            scrollToBottom();
        }

        let processingIndicator = null;

        function showProcessingStep(step) {
            if (!processingIndicator) {
                // Create the processing indicator
                processingIndicator = document.createElement('div');
                processingIndicator.className = 'processing-indicator';
                processingIndicator.innerHTML = `
                    <div class="processing-content">
                        <div class="processing-dots">
                            <span></span><span></span><span></span>
                        </div>
                        <div class="processing-text"></div>
                    </div>
                `;
                chatDiv.appendChild(processingIndicator);
            }

            const textElement = processingIndicator.querySelector('.processing-text');
            
            // Fade out current text
            textElement.style.opacity = '0';
            
            setTimeout(() => {
                textElement.textContent = step;
                textElement.style.opacity = '1';
            }, 150);
            
            scrollToBottom();
        }

        function hideProcessingIndicator() {
            if (processingIndicator) {
                processingIndicator.style.opacity = '0';
                setTimeout(() => {
                    if (processingIndicator && processingIndicator.parentNode) {
                        processingIndicator.parentNode.removeChild(processingIndicator);
                    }
                    processingIndicator = null;
                }, 300);
            }
        }
        
        // Legacy function - kept for compatibility
        function addProcessingUpdate(update) {
            showProcessingStep(update);
        }
        

        
        function scrollToBottom() {
            // Multiple methods to ensure scrolling works reliably
            requestAnimationFrame(() => {
                chatDiv.scrollTop = chatDiv.scrollHeight;
                
                // Also scroll the last message into view
                const lastMessage = chatDiv.lastElementChild;
                if (lastMessage) {
                    lastMessage.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'nearest',
                        inline: 'nearest'
                    });
                }
            });
        }
        
        function sendMessage() {
            const message = messageInput.value.trim();
            if (!message || !ws || ws.readyState !== WebSocket.OPEN || isProcessing) {
                return;
            }
            
            const payload = {
                session_id: sessionId,
                message: message
            };
            
            ws.send(JSON.stringify(payload));
            messageInput.value = '';
        }
        
        function sendExample(example) {
            if (!isProcessing) {
                messageInput.value = example;
                sendMessage();
            }
        }
        
        // Event listeners
        sendButton.addEventListener('click', sendMessage);
        
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Auto-scroll observer to handle dynamic content
        const autoScrollObserver = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Always auto-scroll for new messages
                    scrollToBottom();
                }
            });
        });
        
        // Start observing chat div for changes
        autoScrollObserver.observe(chatDiv, {
            childList: true,
            subtree: true
        });
        
        // Handle page visibility changes for better reconnection
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && (!ws || ws.readyState === WebSocket.CLOSED)) {
                console.log('Page became visible, attempting reconnection...');
                connectWebSocket();
            }
        });
        
        // Initialize connection
        connectWebSocket();
        
        // Welcome message
        setTimeout(() => {
            addSystemMessage('Welcome! Ask me anything - I can help with coding, answer questions, or clarify complex requests.');
        }, 1000);
    </script>
</body>
</html>
    """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication with the LangGraph agent"""
    await websocket.accept()
    
    # Create new session
    session_id = session_manager.create_session(websocket)
    
    try:
        # Send session created message
        await websocket.send_text(json.dumps({
            "type": "session_created",
            "data": {"session_id": session_id},
            "timestamp": datetime.now().isoformat()
        }))
        
        print(f"New WebSocket connection established: {session_id}")
        
        # Set HTTP mode for the agent system to handle clarification differently
        set_execution_modes(http=True)
        
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                payload = json.loads(data)
                
                user_message = payload.get("message", "")
                client_session_id = payload.get("session_id", session_id)
                
                if not user_message:
                    continue
                
                # Get session
                session = session_manager.get_session(client_session_id)
                if not session:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {"error": "Invalid session"},
                        "timestamp": datetime.now().isoformat()
                    }))
                    continue
                
                # Send user message confirmation
                await websocket.send_text(json.dumps({
                    "type": "user_message",
                    "data": {"content": user_message},
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Create WebSocket streamer
                streamer = WebSocketStreamer(websocket)
                
                # Process the request with streaming
                agent = session["agent"]
                
                try:
                    # Send processing start update
                    await streamer.send_update("processing_update", "Starting to process your request...")
                    
                    # Process the request with enhanced streaming
                    result = await process_request_with_streaming(agent, user_message, streamer)
                    
                    # Send route decision immediately if available
                    if result.get("route_taken"):
                        await websocket.send_text(json.dumps({
                            "type": "route_decision",
                            "data": {"route": result["route_taken"]},
                            "timestamp": datetime.now().isoformat()
                        }))
                    
                    # Debug logging
                    print(f"🔍 DEBUG: Result keys: {list(result.keys())}")
                    print(f"🔍 DEBUG: Final result: {result.get('final_result', '')[:100]}...")
                    print(f"🔍 DEBUG: Route taken: {result.get('route_taken')}")
                    print(f"🔍 DEBUG: Has clarification_question: {'clarification_question' in result}")
                    
                    # Update session message count
                    session["message_count"] += 1
                    
                    # Send final result
                    if result.get("success"):
                        # Send route decision first
                        if result.get("route_taken"):
                            await websocket.send_text(json.dumps({
                                "type": "route_decision",
                                "data": {"route": result["route_taken"]},
                                "timestamp": datetime.now().isoformat()
                            }))
                        
                        # Check if this is a clarification request
                        clarification_question = result.get("clarification_question")
                        final_result = result.get("final_result", "")
                        
                        # Multiple ways to detect clarification is needed
                        is_clarification = (
                            clarification_question or
                            final_result.startswith("I need more information:") or
                            ("Could you please" in final_result and "?" in final_result) or
                            ("What kind of" in final_result and "?" in final_result) or
                            ("more details" in final_result.lower() and "?" in final_result)
                        )
                        
                        if is_clarification:
                            # Extract the clarification question
                            if clarification_question:
                                clarification_text = clarification_question
                            elif final_result.startswith("I need more information:"):
                                clarification_text = final_result.replace("I need more information: ", "")
                            else:
                                clarification_text = final_result
                            
                            await websocket.send_text(json.dumps({
                                "type": "clarification_needed",
                                "data": {"question": clarification_text},
                                "timestamp": datetime.now().isoformat()
                            }))
                            
                            print(f"🔍 DEBUG: Sent clarification request: {clarification_text[:50]}...")
                        else:
                            await websocket.send_text(json.dumps({
                                "type": "final_result",
                                "data": {"result": result["final_result"]},
                                "timestamp": datetime.now().isoformat()
                            }))
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "data": {"error": result.get("error", "Unknown error")},
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                except Exception as e:
                    print(f"Error processing request: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {"error": str(e)},
                        "timestamp": datetime.now().isoformat()
                    }))
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "data": {"error": "Invalid JSON format"},
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        # Clean up session
        session_manager.remove_session(session_id)
        print(f"WebSocket connection closed: {session_id}")

async def process_request_with_streaming(agent: LangGraphAgentSystem, user_input: str, streamer: WebSocketStreamer) -> Dict[str, Any]:
    """
    Process a request with real-time streaming updates to the WebSocket client
    """
    try:
        import threading
        import queue
        import time
        
        result_queue = queue.Queue()
        error_queue = queue.Queue()
        step_queue = queue.Queue()
        
        # Custom print function to capture outputs
        original_print = print
        def streaming_print(*args, **kwargs):
            message = " ".join(str(arg) for arg in args)
            step_queue.put(("print", message))
            return original_print(*args, **kwargs)
        
        def process_in_thread():
            try:
                # Replace print to capture outputs
                import builtins
                builtins.print = streaming_print
                
                # Process the request
                result = agent.process_request(user_input)
                result_queue.put(result)
                
                # Restore original print
                builtins.print = original_print
                
            except Exception as e:
                error_queue.put(e)
            finally:
                # Always restore print
                builtins.print = original_print
        
        # Start processing
        thread = threading.Thread(target=process_in_thread)
        thread.start()
        
        # Monitor outputs in real-time
        last_heartbeat = time.time()
        route_sent = False
        
        while thread.is_alive():
            # Process any captured outputs
            messages_sent = 0
            while not step_queue.empty() and messages_sent < 5:  # Limit messages per loop
                try:
                    msg_type, message = step_queue.get_nowait()
                    
                    # Filter and format messages for better Claude output visibility
                    if "🧠 Claude thinking:" in message:
                        clean_msg = message.replace("🧠 Claude thinking: ", "🧠 ")
                        await streamer.send_update("processing_step", clean_msg)
                    elif "🤖 Claude:" in message:
                        clean_msg = message.replace("🤖 Claude: ", "🤖 ")
                        await streamer.send_update("processing_step", clean_msg)
                    elif "📄 Writing file:" in message:
                        await streamer.send_update("processing_step", "📄 Creating file...")
                    elif "✅ File created successfully" in message:
                        await streamer.send_update("processing_step", "✅ File created successfully")
                    elif "📋 Updating todo list" in message:
                        await streamer.send_update("processing_step", "📋 Updating progress...")
                    elif "⚡ ACTION:" in message:
                        await streamer.send_update("processing_step", message.replace("⚡ ACTION: ", ""))
                    elif "💭" in message and any(keyword in message for keyword in ["Starting", "Executing", "Processing", "Completed"]):
                        clean_msg = message.replace("💭 ", "").strip()
                        if clean_msg:
                            await streamer.send_update("processing_step", clean_msg)
                    elif "Route decision:" in message:
                        # Extract route from message like "Route decision: clarify"
                        route = message.split("Route decision:")[-1].strip()
                        if not route_sent:
                            await streamer.send_update("route_decision", route)
                            route_sent = True
                    elif "✅ RESULT:" in message:
                        await streamer.send_update("processing_step", message.replace("✅ RESULT: ", ""))
                    
                    messages_sent += 1
                except:
                    break
            
            # Send heartbeat every 5 seconds
            if time.time() - last_heartbeat > 5:
                await streamer.send_update("processing_step", "Processing...")
                last_heartbeat = time.time()
            
            await asyncio.sleep(0.3)  # Check every 300ms
        
        # Get result
        if not error_queue.empty():
            error = error_queue.get()
            raise error
        
        if not result_queue.empty():
            result = result_queue.get()
            await streamer.send_update("processing_step", "Processing completed!")
            
            # Enhanced clarification detection
            final_result = result.get("final_result", "")
            clarification_indicators = [
                final_result.startswith("I need more information:"),
                "clarification_question" in result,
                ("Could you please" in final_result and "?" in final_result),
                ("What kind of" in final_result and "?" in final_result),
                ("more details" in final_result.lower() and "?" in final_result),
                ("please provide" in final_result.lower() and "?" in final_result)
            ]
            
            if any(clarification_indicators):
                if not result.get("clarification_question"):
                    if final_result.startswith("I need more information:"):
                        result["clarification_question"] = final_result.replace("I need more information: ", "")
                    else:
                        result["clarification_question"] = final_result
                
                print(f"🔍 DEBUG: Clarification detected: {result.get('clarification_question', '')[:50]}...")
            
            return result
        else:
            raise Exception("No result received from processing thread")
            
    except Exception as e:
        await streamer.send_update("processing_step", f"Error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "final_result": "",
            "route_taken": "error"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(session_manager.sessions),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/sessions")
async def get_sessions():
    """Get information about active sessions"""
    sessions_info = []
    for session_id, session_data in session_manager.sessions.items():
        sessions_info.append({
            "session_id": session_id,
            "created_at": session_data["created_at"].isoformat(),
            "message_count": session_data["message_count"]
        })
    
    return {
        "active_sessions": len(sessions_info),
        "sessions": sessions_info
    }

if __name__ == "__main__":
    print("🚀 Starting FastAPI WebSocket Server for LangGraph Agent System")
    print("=" * 60)
    print("📡 WebSocket endpoint: ws://localhost:8000/ws")
    print("🌐 Web interface: http://localhost:8000")
    print("📊 Health check: http://localhost:8000/health")
    print("📋 Sessions info: http://localhost:8000/sessions")
    print("=" * 60)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info",
        reload=True
    ) 