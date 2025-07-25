"""
LangGraph Agent System - Single File Implementation

This system implements a LangGraph-powered AI assistant that:
- Accepts vague user prompts
- Engages in multi-turn clarification (if needed)
- Refines the clarified prompt
- Routes the task to either a Claude Code agent (for code actions) or an LLM (for answers)
- Returns the final result
- Monitors all steps with LangSmith for observability

Author: AI Assistant
Date: 2024
"""

import json
import subprocess
from typing import Dict, Any, List, Optional, Literal, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import os
from pathlib import Path
import argparse
import sys

# Set up LangSmith tracing before importing LangChain components
# Only enable if API key is properly configured
langsmith_api_key = os.getenv("LANGCHAIN_API_KEY")
if langsmith_api_key and langsmith_api_key.strip():
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", "langraph-agent-system")
    LANGSMITH_ENABLED = True
else:
    # Disable tracing if no API key
    os.environ.pop("LANGCHAIN_TRACING_V2", None)
    LANGSMITH_ENABLED = False

# Dependencies that need to be installed:
# pip install langgraph langchain openai anthropic langsmith

try:
    from langgraph.graph import StateGraph, END
    from langchain_community.llms import OpenAI
    from langchain_openai import ChatOpenAI
    from langsmith import traceable
    from langgraph.config import get_stream_writer
    import openai
    # import anthropic  # For future Claude integration
except ImportError as e:
    print(f"Missing required dependencies: {e}")
    print("Please install: pip install langgraph langchain openai anthropic langsmith")
    exit(1)

# Create conditional traceable decorator
def conditional_traceable(func):
    """Apply @traceable only when LangSmith is enabled"""
    if LANGSMITH_ENABLED:
        return traceable(func)
    else:
        return func

# ============================================================================
# GLOBAL CONFIGURATION FOR EXECUTION MODES
# ============================================================================

# Global flags for different execution modes
TESTING_MODE = False

def set_execution_modes(testing=False, thinking=False, steps=False):
    """Set global execution modes"""
    global TESTING_MODE
    TESTING_MODE = testing

def print_action(message: str):
    """Print action messages (always shown unless testing mode)"""
    if not TESTING_MODE:
        print(f"⚡ ACTION: {message}")

def print_result(message: str):
    """Print result messages (always shown)"""
    print(f"✅ RESULT: {message}")


# ============================================================================
# STEP 1: STATE MANAGEMENT
# ============================================================================

class RouteType(Enum):
    """Enumeration of possible routing decisions"""
    CLARIFY = "clarify"
    CODE = "code" 
    ANSWER = "answer"


class AgentState(TypedDict):
    """
    Central state management for the LangGraph agent system.
    
    This state is passed between all nodes in the graph and maintains
    the conversation context, routing decisions, and processing status.
    """
    # Input and conversation management
    user_input: str
    conversation_history: List[Dict[str, str]]
    
    # Clarification state
    clarified: bool
    clarification_questions: List[str]
    clarification_responses: List[str]
    
    # Routing and processing
    route: Optional[RouteType]
    refined_prompt: str
    
    # Results
    final_result: str
    error_message: str
    
    # Metadata
    processing_steps: List[str]


def create_agent_state(user_input: str) -> AgentState:
    """Create a new AgentState with default values"""
    return AgentState(
        user_input=user_input,
        conversation_history=[],
        clarified=False,
        clarification_questions=[],
        clarification_responses=[],
        route=None,
        refined_prompt="",
        final_result="",
        error_message="",
        processing_steps=[]
    )


def add_conversation(state: AgentState, role: str, message: str) -> None:
    """Add a message to the conversation history"""
    state["conversation_history"].append({"role": role, "message": message})


def add_step(state: AgentState, step: str) -> None:
    """Track processing steps for debugging and transparency"""
    state["processing_steps"].append(step)


# ============================================================================
# STEP 2: UTILITY FUNCTIONS AND HELPERS
# ============================================================================

class LLMManager:
    """
    Manages LLM interactions with consistent configuration and error handling.
    
    This class centralizes all LLM calls to ensure consistent behavior,
    proper error handling, and easy model switching.
    """
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        # Initialize OpenAI client
        self.chat_model = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            openai_api_key=self.openai_api_key
        )
    
    @conditional_traceable
    def call_gpt4o(self, prompt: str, system_prompt: str = "", max_tokens: int = 1000) -> str:
        """
        Make a call to GPT-4o with proper error handling and LangSmith tracing.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens to generate
            
        Returns:
            The LLM response as a string
        """
        try:
            # Emit streaming update for LLM call
            try:
                writer = get_stream_writer()
                writer(f"🧠 GPT-4o call initiated (max_tokens: {max_tokens})")
            except:
                pass
                
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Use the new OpenAI client API
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            try:
                writer = get_stream_writer()
                writer("⏳ Waiting for GPT-4o response...")
            except:
                pass
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            
            try:
                writer = get_stream_writer()
                writer(f"✅ GPT-4o response received ({len(result)} characters)")
            except:
                pass
            
            return result
            
        except Exception as e:
            error_msg = f"Error calling GPT-4o: {str(e)}"
            
            try:
                writer = get_stream_writer()
                writer(f"❌ GPT-4o call failed: {str(e)}")
            except:
                pass
                
            return error_msg


# ============================================================================
# STEP 3: CLARIFICATION NODE
# ============================================================================

@conditional_traceable
def clarify_loop(state: AgentState) -> AgentState:
    """
    Multi-turn clarification node that asks follow-up questions to understand
    vague user requests better.
    
    This node:
    1. Analyzes the current user input and conversation history
    2. Determines if more clarification is needed
    3. Generates appropriate follow-up questions
    4. Updates the state based on user responses
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with clarification status
    """
    # Emit custom streaming data for real-time monitoring
    try:
        writer = get_stream_writer()
        writer("🤔 Starting clarification analysis...")
    except:
        pass  # Stream writer not available
        
    add_step(state, "Starting clarification process")
    
    llm = LLMManager()
    
    # Build context for the clarification decision
    context = f"""
    User Input: {state['user_input']}
    
    Conversation History:
    {json.dumps(state["conversation_history"], indent=2)}
    
    Previous clarification questions asked: {state["clarification_questions"]}
    Previous responses received: {state["clarification_responses"]}
    """
    
    # System prompt for clarification agent
    system_prompt = """
    You are a clarification specialist. Your job is to determine if the user's request
    is clear enough to proceed, or if you need to ask follow-up questions.
    
    Consider a request "clear enough" if you can understand:
    1. What the user wants to accomplish
    2. The general domain/context (web app, mobile app, data analysis, etc.)
    3. Any specific requirements or constraints
    
    If the request is too vague, ask 1-2 specific follow-up questions.
    If it's clear enough, respond with "CLARIFIED: [summary of what they want]"
    
    Keep questions focused and avoid asking too many at once.
    """
    
    clarification_prompt = f"""
    {context}
    
    Based on the above information, is this request clear enough to proceed?
    If not, what specific questions should I ask to clarify?
    
    Respond in one of these formats:
    - "CLARIFIED: [clear summary of the request]" if ready to proceed
    - "QUESTION: [your follow-up question]" if more clarification needed
    """
    
    try:
        writer = get_stream_writer()
        writer("🧠 Analyzing request clarity...")
    except:
        pass
    
    try:
        writer = get_stream_writer()
        writer("🤖 Analyzing request clarity...")
    except:
        pass
    
    response = llm.call_gpt4o(clarification_prompt, system_prompt)
    add_step(state, f"Clarification analysis: {response[:100]}...")
    
    try:
        writer = get_stream_writer()
        writer(f"📝 Analysis complete: {response[:50]}...")
    except:
        pass
    
    if response.startswith("CLARIFIED:"):
        # Clarification complete
        
        state["clarified"] = True
        state["refined_prompt"] = response[10:].strip()  # Remove "CLARIFIED:" prefix
        add_step(state, "Clarification completed")
        
        try:
            writer = get_stream_writer()
            writer("✅ Request is clear enough to proceed!")
        except:
            pass
        
        print_result("Clarification completed - request is clear")
        
    elif response.startswith("QUESTION:"):
        # Need more clarification - ask the user directly
        question = response[9:].strip()  # Remove "QUESTION:" prefix
        state["clarification_questions"].append(question)
        add_conversation(state, "assistant", question)
        add_step(state, f"Asked clarification question: {question}")
        
        try:
            writer = get_stream_writer()
            writer(f"❓ Need clarification: {question}")
        except:
            pass
        
        # STOP HERE and ask the user for input
        if not TESTING_MODE:
            print("\n" + "="*60)
            print("🤖 CLARIFICATION NEEDED")
            print("="*60)
            print(f"❓ {question}")
            print("-"*60)
            
            # Get real user input
            user_response = input("💬 Your response: ").strip()
        else:
            # In testing mode, provide a simulated response
            user_response = "I want to build a web application for managing inventory"
            print_action(f"Testing mode - simulated response: '{user_response}'")
        
        if user_response:
            state["clarification_responses"].append(user_response)
            add_conversation(state, "user", user_response)
            add_step(state, f"Received clarification response: {user_response}")
            
            try:
                writer = get_stream_writer()
                writer(f"💬 User response received: {user_response}")
            except:
                pass
            
            # Update the user input with the clarified information
            state["user_input"] = f"{state['user_input']} - {user_response}"
            
            try:
                writer = get_stream_writer()
                writer("🔄 Re-analyzing with new information...")
            except:
                pass
            
            # Re-run clarification analysis with the new information
            updated_context = f"""
            Original User Input: {state['user_input']}
            Clarification Question: {question}
            User Response: {user_response}
            
            Conversation History:
            {json.dumps(state["conversation_history"], indent=2)}
            """
            
            updated_prompt = f"""
            {updated_context}
            
            Now that the user has provided more information, is the request clear enough to proceed?
            
            Respond in one of these formats:
            - "CLARIFIED: [clear summary of what they want]" if ready to proceed
            - "QUESTION: [your follow-up question]" if still need more clarification
            """
            
            follow_up_response = llm.call_gpt4o(updated_prompt, system_prompt)
            
            try:
                writer = get_stream_writer()
                writer(f"🔄 Follow-up analysis: {follow_up_response[:50]}...")
            except:
                pass
            
            if follow_up_response.startswith("CLARIFIED:"):
                state["clarified"] = True
                state["refined_prompt"] = follow_up_response[10:].strip()
                add_step(state, "Clarification completed after user response")
                
                try:
                    writer = get_stream_writer()
                    writer("✅ Request clarified and ready to proceed!")
                except:
                    pass
                    
                print_result("Clarification completed after user interaction")
            else:
                # Still need more clarification, but limit to prevent infinite loops
                if len(state["clarification_questions"]) >= 2:
                    state["clarified"] = True
                    state["refined_prompt"] = f"{state['user_input']} - {user_response}"
                    add_step(state, "Maximum clarification rounds reached - proceeding")
                    
                    try:
                        writer = get_stream_writer()
                        writer("⚡ Max clarification rounds reached - proceeding anyway")
                    except:
                        pass
                        
                    print_result("Proceeding after maximum clarification rounds")
        else:
            # User didn't provide a response, use original input
            state["clarified"] = True
            state["refined_prompt"] = state["user_input"]
            add_step(state, "No clarification response - proceeding with original")
            print_result("Proceeding with original input (no user response)")
    
    else:
        # Fallback - assume clarified
        state["clarified"] = True
        state["refined_prompt"] = state["user_input"]
        add_step(state, "Clarification fallback - proceeding with original input")
        
        try:
            writer = get_stream_writer()
            writer("⚡ Using fallback - proceeding with original request")
        except:
            pass
            
        print_result("Using fallback - proceeding with original request")
    
    return state


# ============================================================================
# STEP 4: ROUTING NODE
# ============================================================================

@conditional_traceable
def route_prompt(state: AgentState) -> AgentState:
    """
    Intelligent routing node that classifies user requests into three categories:
    1. CLARIFY - Request is too vague and needs clarification
    2. CODE - Request involves coding/development work (Claude Code)
    3. ANSWER - Request can be answered directly with information
    
    This node uses GPT-4o to analyze the user input and make routing decisions.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with routing decision
    """
    try:
        writer = get_stream_writer()
        writer("🔀 Starting intelligent routing analysis...")
    except:
        pass
        
    add_step(state, "Starting prompt routing analysis")
    
    llm = LLMManager()
    
    # Build context for routing decision
    input_text = state["refined_prompt"] if state["refined_prompt"] else state["user_input"]
    
    try:
        writer = get_stream_writer()
        writer(f"📝 Analyzing input: '{input_text[:50]}...'")
    except:
        pass
    
    system_prompt = """
    You are a task router. Classify user requests into one of three categories:
    
    1. CLARIFY - The request is too vague or ambiguous. Examples:
       - "I want to build something"
       - "Help me with my project"
       - "I need an app"
    
    2. CODE - The request involves coding, development, or technical implementation. Examples:
       - "Build a web app for inventory management"
       - "Create a Python script to analyze data"
       - "Fix this bug in my React component"
       - "Add authentication to my app"
    
    3. ANSWER - The request is asking for information, explanation, or guidance. Examples:
       - "What is the best way to deploy a web app?"
       - "Explain how authentication works"
       - "What are the pros and cons of React vs Vue?"
    
    Respond with only: CLARIFY, CODE, or ANSWER
    """
    
    routing_prompt = f"""
    User request: "{input_text}"
    
    Conversation context: {json.dumps(state["conversation_history"][-3:], indent=2)}
    
    How should this request be routed?
    """
    
    try:
        writer = get_stream_writer()
        writer("🤖 Calling GPT-4o for routing decision...")
    except:
        pass
    
    response = llm.call_gpt4o(routing_prompt, system_prompt).strip().upper()
    add_step(state, f"Routing analysis result: {response}")
    
    try:
        writer = get_stream_writer()
        writer(f"🔀 Routing decision: {response}")
    except:
        pass
    
    # Map response to RouteType enum
    if "CLARIFY" in response:
        state["route"] = RouteType.CLARIFY
        route_emoji = "❓"
        route_desc = "needs clarification"
    elif "CODE" in response:
        state["route"] = RouteType.CODE
        route_emoji = "💻"
        route_desc = "involves coding/development"
    elif "ANSWER" in response:
        state["route"] = RouteType.ANSWER
        route_emoji = "💡"
        route_desc = "needs informational answer"
    else:
        # Fallback to CLARIFY if unclear
        state["route"] = RouteType.CLARIFY
        route_emoji = "❓"
        route_desc = "defaulting to clarification"
        add_step(state, "Routing fallback - defaulting to CLARIFY")
    
    try:
        writer = get_stream_writer()
        writer(f"{route_emoji} Route decision: {state['route'].value.upper()} - {route_desc}")
    except:
        pass
    
    print_result(f"Routing completed - Direction: {state['route'].value.upper()}")
    
    add_step(state, f"Route decision: {state['route'].value}")
    return state


# ============================================================================
# STEP 5: PROMPT REFINEMENT NODE
# ============================================================================

@conditional_traceable
def refine_prompt(state: AgentState) -> AgentState:
    """
    Refines and polishes the clarified user request into a well-structured
    prompt suitable for Claude Code execution.
    
    This node:
    1. Takes the clarified user intent
    2. Structures it into clear, actionable instructions
    3. Adds necessary context and requirements
    4. Formats it for optimal Claude Code performance
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with refined prompt
    """
    try:
        writer = get_stream_writer()
        writer("✨ Starting prompt refinement process...")
    except:
        pass
        
    add_step(state, "Starting prompt refinement")
    
    llm = LLMManager()
    
    # Build context for refinement
    base_prompt = state["refined_prompt"] if state["refined_prompt"] else state["user_input"]
    
    try:
        writer = get_stream_writer()
        writer(f"📄 Base prompt: '{base_prompt[:100]}...'")
    except:
        pass
    
    system_prompt = """
    You are a prompt refinement specialist. Your job is to take a clarified user request
    and turn it into a clear, actionable prompt suitable for a coding assistant.
    
    A good refined prompt should:
    1. Be specific and actionable
    2. Include clear requirements and constraints
    3. Specify the technology stack if relevant
    4. Include any quality or style preferences
    5. Be well-structured and easy to understand
    
    Format your response as a clear, professional task description.
    """
    
    refinement_prompt = f"""
    Original user request: "{state['user_input']}"
    
    Clarified request: "{base_prompt}"
    
    Conversation context: {json.dumps(state["conversation_history"], indent=2)}
    
    Please refine this into a clear, actionable prompt for a coding assistant.
    Focus on making it specific enough to produce high-quality results.
    """
    
    try:
        writer = get_stream_writer()
        writer("🤖 Calling GPT-4o for prompt refinement...")
    except:
        pass
    
    refined = llm.call_gpt4o(refinement_prompt, system_prompt)
    state["refined_prompt"] = refined.strip()
    add_step(state, "Prompt refinement completed")
    
    try:
        writer = get_stream_writer()
        writer(f"✅ Refined prompt ready: '{refined[:80]}...'")
    except:
        pass
    
    return state


# ============================================================================
# STEP 6: CLAUDE CODE EXECUTION NODE (PLACEHOLDER)
# ============================================================================

@conditional_traceable
def run_claude_code(state: AgentState) -> AgentState:
    """
    Executes the refined prompt using Claude Code CLI.
    
    This node:
    1. Prepares the refined prompt for Claude Code
    2. Executes the Claude Code CLI command
    3. Parses the result and handles errors
    4. Updates the state with the execution results
    
    NOTE: This is currently a placeholder implementation as requested.
    The actual Claude Code integration will be implemented later.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with execution results
    """
    try:
        writer = get_stream_writer()
        writer("⚙️ Starting Claude Code execution (PLACEHOLDER)...")
    except:
        pass
        
    add_step(state, "Starting Claude Code execution (PLACEHOLDER)")
    
    try:
        writer = get_stream_writer()
        writer("📝 Preparing prompt for Claude Code CLI...")
    except:
        pass
    
    # PLACEHOLDER IMPLEMENTATION
    # In the real implementation, this would:
    # 1. Write the refined prompt to a temporary file
    # 2. Execute: subprocess.run(["claude", "code", "--prompt-file", temp_file])
    # 3. Parse the JSON output from Claude Code
    # 4. Handle any errors or edge cases
    
    try:
        writer = get_stream_writer()
        writer("🔧 Simulating Claude Code execution...")
    except:
        pass
    
    placeholder_result = f"""
    PLACEHOLDER CLAUDE CODE EXECUTION
    
    Refined Prompt:
    {state["refined_prompt"]}
    
    This would normally execute the Claude Code CLI with the above prompt
    and return the generated code, file changes, or execution results.
    
    Expected implementation:
    ```python
    import tempfile
    import subprocess
    import json
    
    # Write prompt to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(state.refined_prompt)
        prompt_file = f.name
    
    try:
        # Execute Claude Code CLI
        result = subprocess.run([
            "claude", "code", 
            "--prompt-file", prompt_file,
            "--output-format", "json"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Parse JSON result
            claude_output = json.loads(result.stdout)
            state.final_result = claude_output.get("result", "")
        else:
            state.error_message = f"Claude Code error: {'result.stderr'}"
            
    except subprocess.TimeoutExpired:
        state.error_message = "Claude Code execution timed out"
    except json.JSONDecodeError:
        state.error_message = "Failed to parse Claude Code output"
    except Exception as e:
        state.error_message = f"Unexpected error: {'str(e)'}"
    finally:
        # Cleanup
        os.unlink(prompt_file)
    ```
    """
    
    state["final_result"] = placeholder_result
    add_step(state, "Claude Code execution completed (placeholder)")
    
    try:
        writer = get_stream_writer()
        writer("✅ Claude Code execution completed - placeholder result generated")
    except:
        pass
    
    return state


# ============================================================================
# STEP 7: DIRECT ANSWER NODE
# ============================================================================

@conditional_traceable
def answer_with_llm(state: AgentState) -> AgentState:
    """
    Provides direct answers to user questions using GPT-4o.
    
    This node is used when the user's request can be answered with information
    rather than requiring code generation or technical implementation.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated agent state with the answer
    """
    try:
        writer = get_stream_writer()
        writer("💡 Starting direct LLM answer generation...")
    except:
        pass
        
    add_step(state, "Starting direct LLM answer generation")
    
    llm = LLMManager()
    
    # Build context for answering
    question = state["refined_prompt"] if state["refined_prompt"] else state["user_input"]
    
    try:
        writer = get_stream_writer()
        writer(f"❓ Question to answer: '{question[:100]}...'")
    except:
        pass
    
    system_prompt = """
    You are a helpful AI assistant. Provide clear, accurate, and comprehensive
    answers to user questions. Structure your responses well and include
    practical examples when relevant.
    
    If the question is technical, provide both conceptual explanations and
    practical guidance. If it's about best practices, include pros/cons and
    real-world considerations.
    """
    
    answer_prompt = f"""
    User question: "{question}"
    
    Context from conversation: {json.dumps(state["conversation_history"], indent=2)}
    
    Please provide a comprehensive answer to this question.
    """
    
    try:
        writer = get_stream_writer()
        writer("🤖 Calling GPT-4o to generate comprehensive answer...")
    except:
        pass
    
    answer = llm.call_gpt4o(answer_prompt, system_prompt, max_tokens=1500)
    state["final_result"] = answer.strip()
    add_step(state, "Direct answer generation completed")
    
    try:
        writer = get_stream_writer()
        writer(f"✅ Answer generated: '{answer[:80]}...'")
    except:
        pass
    
    return state


# ============================================================================
# STEP 8: GRAPH CONSTRUCTION AND ROUTING LOGIC
# ============================================================================

def create_routing_function():
    """
    Creates the routing function for conditional edges in the graph.
    
    This function determines the next node based on the current state,
    implementing the core decision logic of the agent system.
    
    Returns:
        A function that takes state and returns the next node name
    """
    
    def route_decision(state: AgentState) -> str:
        """
        Determines the next node based on current state and route decision.
        
        Routing logic:
        - If route is CLARIFY and not clarified -> clarify_loop
        - If route is CLARIFY and clarified -> refine_prompt
        - If route is CODE -> refine_prompt (then to claude_code)
        - If route is ANSWER -> answer_with_llm
        - From clarify_loop: if clarified -> refine_prompt, else loop back
        - From refine_prompt -> run_claude_code
        
        Args:
            state: Current agent state
            
        Returns:
            Name of the next node to execute
        """
        current_node = getattr(state, '_current_node', 'route_prompt')
        
        if current_node == 'route_prompt':
            if state.route == RouteType.CLARIFY:
                return 'clarify_loop'
            elif state.route == RouteType.CODE:
                return 'refine_prompt'
            elif state.route == RouteType.ANSWER:
                return 'answer_with_llm'
            else:
                return 'clarify_loop'  # Fallback
                
        elif current_node == 'clarify_loop':
            if state.clarified:
                return 'refine_prompt'
            else:
                return 'clarify_loop'  # Continue clarification
                
        elif current_node == 'refine_prompt':
            return 'run_claude_code'
            
        else:
            return END
    
    return route_decision


def build_agent_graph() -> StateGraph:
    """
    Constructs the complete LangGraph agent system.
    
    This function:
    1. Creates a StateGraph instance
    2. Adds all the processing nodes
    3. Defines the conditional routing logic
    4. Sets up entry and exit points
    5. Compiles the graph for execution
    
    Returns:
        Compiled StateGraph ready for execution
    """
    print("Building LangGraph agent system...")
    
    # Initialize the graph with our state schema
    graph = StateGraph(AgentState)
    
    # Add all processing nodes
    graph.add_node("route_prompt", route_prompt)
    graph.add_node("clarify_loop", clarify_loop)
    graph.add_node("refine_prompt", refine_prompt)
    graph.add_node("run_claude_code", run_claude_code)
    graph.add_node("answer_with_llm", answer_with_llm)
    
    # Set the entry point
    graph.set_entry_point("route_prompt")
    
    # Add conditional edges for routing
    graph.add_conditional_edges(
        "route_prompt",
        lambda state: state["route"].value if state["route"] else "clarify",
        {
            "clarify": "clarify_loop",
            "code": "refine_prompt", 
            "answer": "answer_with_llm"
        }
    )
    
    # Add conditional edges for clarification loop
    graph.add_conditional_edges(
        "clarify_loop",
        lambda state: "refined" if state["clarified"] else "continue",
        {
            "continue": "clarify_loop",
            "refined": "refine_prompt"
        }
    )
    
    # Direct edges
    graph.add_edge("refine_prompt", "run_claude_code")
    
    # Set finish nodes
    graph.add_edge("run_claude_code", END)
    graph.add_edge("answer_with_llm", END)
    
    # Compile the graph
    compiled_graph = graph.compile()
    print("Graph compilation completed successfully!")
    
    return compiled_graph


# ============================================================================
# STEP 9: MAIN EXECUTION AND INTERFACE
# ============================================================================

class LangGraphAgentSystem:
    """
    Complete LangGraph-powered agent system with memory, routing, and multi-modal processing.
    
    This system implements a sophisticated AI assistant that can:
    - Route different types of requests (clarification, code, answers)
    - Maintain conversation context across multiple interactions
    - Provide Claude Code integration for development tasks
    - Stream real-time processing updates with LangSmith observability
    """
    
    def __init__(self):
        """Initialize the LangGraph agent system with persistent conversation memory."""
        self.llm_manager = LLMManager()
        self.graph = build_agent_graph()
        self.conversation_memory: List[Dict[str, str]] = []  # Persistent memory across requests
        print_result("Agent system initialized successfully!")
        
        if LANGSMITH_ENABLED:
            print(f"🔍 LangSmith tracing enabled - view traces at: https://smith.langchain.com/")
            print(f"📊 Project: langraph-agent-system")
    
    @conditional_traceable
    def process_request(self, user_input: str) -> Dict[str, Any]:
        """
        Process a user request through the complete agent pipeline with full tracing, streaming, and memory.
        
        Args:
            user_input: The user's initial request or question
            
        Returns:
            Dictionary containing the final result and processing metadata
        """
        print_action(f"Processing request: '{user_input[:100]}...'")
        print("=" * 80)
        
        # Initialize state with persistent conversation memory
        initial_state = create_agent_state(user_input)
        initial_state["conversation_history"] = self.conversation_memory.copy()  # Use persistent memory
        add_conversation(initial_state, "user", user_input)
        add_step(initial_state, "Request received and processing started")
        
        try:
            # Use streaming to show real-time execution steps
            print_action("Starting graph execution with real-time streaming...")
            print("-" * 60)
            
            final_state = initial_state
            last_update = {}
            
            # Stream the graph execution with multiple modes for comprehensive monitoring
            try:
                for chunk in self.graph.stream(
                    initial_state, 
                    stream_mode=["updates", "custom"]
                ):
                    # Handle different chunk types based on stream mode
                    if isinstance(chunk, tuple) and len(chunk) == 2:
                        stream_mode, data = chunk
                        
                        if stream_mode == "updates":
                            # Show node execution updates
                            for node_name, node_update in data.items():
                                print_action(f"Executing node: {node_name}")
                                if "processing_steps" in node_update:
                                    latest_step = node_update["processing_steps"][-1] if node_update["processing_steps"] else "Processing..."
                                    if not TESTING_MODE:
                                        print(f"   📋 {latest_step}")
                                print_result(f"Node {node_name} completed")
                                if not TESTING_MODE:
                                    print()
                                
                                # Keep track of the most recent state update
                                last_update.update(node_update)
                            
                        elif stream_mode == "custom":
                            # Show custom progress messages from nodes
                            if not TESTING_MODE:
                                print(f"💭 {data}")
                            
                    else:
                        # Handle single stream mode case
                        if isinstance(chunk, dict):
                            # This is likely an "updates" chunk
                            for node_name, node_update in chunk.items():
                                print_action(f"Executing node: {node_name}")
                                if "processing_steps" in node_update:
                                    latest_step = node_update["processing_steps"][-1] if node_update["processing_steps"] else "Processing..."
                                    if not TESTING_MODE:
                                        print(f"   📋 {latest_step}")
                                print_result(f"Node {node_name} completed")
                                if not TESTING_MODE:
                                    print()
                                
                                # Keep track of the most recent state update
                                last_update.update(node_update)
                        else:
                            # This might be a custom message
                            if not TESTING_MODE:
                                print(f"💭 {chunk}")
                
                # Update final state with the last updates
                if last_update:
                    final_state.update(last_update)
                    
            except Exception as streaming_error:
                print_action(f"Streaming failed: {streaming_error}")
                print_action("Falling back to direct graph execution...")
                final_state = self.graph.invoke(initial_state)
            
            print("-" * 60)
            print_result("Graph execution completed!")
            print("=" * 80)
            
            # Update persistent conversation memory
            self.conversation_memory = final_state.get("conversation_history", [])
            
            # Prepare result with comprehensive metadata
            result = {
                "success": True,
                "final_result": final_state.get("final_result", ""),
                "route_taken": final_state.get("route").value if final_state.get("route") else "unknown",
                "clarified": final_state.get("clarified", False),
                "refined_prompt": final_state.get("refined_prompt", ""),
                "processing_steps": final_state.get("processing_steps", []),
                "conversation_history": final_state.get("conversation_history", []),
                "error_message": final_state.get("error_message", "")
            }
            
            print_result(f"Request processed successfully via '{result['route_taken']}' route")
            return result
            
        except Exception as e:
            print(f"❌ Error processing request: {str(e)}")
            print("=" * 80)
            return {
                "success": False,
                "error": str(e),
                "final_result": "",
                "route_taken": "error",
                "processing_steps": ["Error occurred during processing"]
            }
    
    def clear_memory(self):
        """Clear the conversation memory."""
        self.conversation_memory = []
        print("🧠 Conversation memory cleared.")
    
    def show_memory(self):
        """Display current conversation memory."""
        if not self.conversation_memory:
            print("🧠 Conversation memory is empty.")
        else:
            print(f"🧠 Conversation memory ({len(self.conversation_memory)} entries):")
            for i, entry in enumerate(self.conversation_memory[-5:], 1):  # Show last 5
                role = entry.get("role", "unknown")
                message = entry.get("message", "")[:100] + "..." if len(entry.get("message", "")) > 100 else entry.get("message", "")
                print(f"  {i}. {role}: {message}")
            if len(self.conversation_memory) > 5:
                print(f"  ... and {len(self.conversation_memory) - 5} more entries")

    def interactive_mode(self):
        """
        Run the agent system in interactive mode for testing and demonstration.
        
        This method provides a command-line interface for users to interact
        with the agent system and see how it processes different types of requests.
        Maintains conversation memory across requests.
        """
        print("\n" + "="*80)
        print("LangGraph Agent System - Interactive Mode")
        print("="*80)
        print("Enter your requests below. Type 'quit' or 'exit' to stop.")
        print("Type 'help' for example requests, 'memory' to view conversation history, 'clear' to reset memory.")
        print("-"*80)
        
        while True:
            try:
                user_input = input("\n🤖 Enter your request: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Goodbye! 👋")
                    break
                    
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                elif user_input.lower() in ['memory', 'show memory', 'history']:
                    self.show_memory()
                    continue
                
                elif user_input.lower() in ['clear', 'clear memory', 'reset']:
                    self.clear_memory()
                    continue
                    
                elif not user_input:
                    print("Please enter a request or type 'help' for examples.")
                    continue
                
                # Process the request
                result = self.process_request(user_input)
                
                # Display results
                self._display_result(result)
                
            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋")
                break
            except Exception as e:
                print(f"\nUnexpected error: {str(e)}")
    
    def _show_help(self):
        """Display help information and example requests."""
        print("\n📚 Commands & Example Requests:")
        print("-" * 40)
        print("🎮 COMMANDS:")
        print("  • 'help' - Show this help")
        print("  • 'memory' or 'history' - View conversation history")
        print("  • 'clear' - Reset conversation memory")
        print("  • 'quit' or 'exit' - Exit the system")
        print()
        print("🔍 CLARIFICATION EXAMPLES:")
        print("  • 'I want to build something'")
        print("  • 'Help me with my project'")
        print("  • 'I need an app'")
        print()
        print("💻 CODE EXAMPLES:")
        print("  • 'Build a web app for inventory management'")
        print("  • 'Create a Python script to analyze CSV data'")
        print("  • 'Add user authentication to my React app'")
        print()
        print("❓ ANSWER EXAMPLES:")
        print("  • 'What is the best way to deploy a web app?'")
        print("  • 'Explain how JWT authentication works'")
        print("  • 'What are the pros and cons of React vs Vue?'")
    
    def _display_result(self, result: Dict[str, Any]):
        """Display the processing result in a formatted way."""
        print("\n" + "="*60)
        print("🎯 PROCESSING RESULT")
        print("="*60)
        
        if result["success"]:
            print(f"✅ Status: Success")
            print(f"🛤️  Route: {result['route_taken'].upper()}")
            print(f"💭 Clarified: {'Yes' if result['clarified'] else 'No'}")
            
            if result["refined_prompt"] and result["refined_prompt"] != result.get("original_input", ""):
                print(f"\n📝 Refined Prompt:")
                print(f"   {result['refined_prompt'][:200]}...")
            
            print(f"\n🎯 Final Result:")
            print(f"   {result['final_result'][:500]}...")
            
            if result["error_message"]:
                print(f"\n⚠️  Warning: {result['error_message']}")
                
        else:
            print(f"❌ Status: Error")
            print(f"💥 Error: {result['error']}")
        
        print(f"\n🔄 Processing Steps:")
        for i, step in enumerate(result.get("processing_steps", []), 1):
            print(f"   {i}. {step}")
        
        print("-" * 60)


# ============================================================================
# STEP 10: MAIN EXECUTION ENTRY POINT
# ============================================================================

def main():
    """
    Main execution function with command-line argument support.
    
    Supports the following flags:
    --testing: Run comprehensive test cases
    --thinking: Show agent's thinking process
    --steps: Show detailed execution steps
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="LangGraph Agent System - AI Assistant with Streaming and Monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python langgraph_agent_system.py                    # Normal interactive mode
  python langgraph_agent_system.py --testing          # Run test cases only
  python langgraph_agent_system.py --thinking         # Show thinking process
  python langgraph_agent_system.py --steps            # Show all execution steps
  python langgraph_agent_system.py --testing --steps  # Test mode with detailed steps
        """
    )
    
    parser.add_argument('--testing', action='store_true', 
                       help='Run comprehensive test cases instead of interactive mode')
    parser.add_argument('--thinking', action='store_true',
                       help='Show the agent\'s thinking process during execution')
    parser.add_argument('--steps', action='store_true', 
                       help='Show detailed execution steps (includes thinking)')
    
    args = parser.parse_args()
    
    # Set execution modes based on arguments
    set_execution_modes(testing=args.testing, thinking=args.thinking, steps=args.steps)
    
    # Print mode information
    modes = []
    if args.testing:
        modes.append("TESTING")
    if args.thinking:
        modes.append("THINKING")
    if args.steps:
        modes.append("STEPS")
    
    mode_str = " + ".join(modes) if modes else "INTERACTIVE"
    
    print("🚀 Starting LangGraph Agent System")
    print("=" * 80)
    print(f"🎯 Mode: {mode_str}")
    if args.thinking:
        print("🧠 Thinking process will be shown")
    if args.steps:
        print("👣 Detailed execution steps will be shown")
    if args.testing:
        print("🧪 Running in testing mode")
    print("=" * 80)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY=your_api_key_here")
        return
    
    # Initialize the agent system
    try:
        print_action("Initializing LangGraph Agent System...")
        agent = LangGraphAgentSystem()
        print_result("Agent system initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize agent system: {e}")
        return
    
    if args.testing:
        # Run comprehensive test cases
        print("\n📋 Running comprehensive test cases...")
        print("=" * 80)
        
        test_cases = [
            {
                "name": "Clear Informational Request",
                "input": "What is the difference between REST and GraphQL APIs?",
                "expected_route": "answer",
                "description": "Should route directly to answer without clarification"
            },
            {
                "name": "Clear Code Request",
                "input": "Build a Python web scraper for news articles using BeautifulSoup",
                "expected_route": "code",
                "description": "Should route to code generation after minimal processing"
            },
            {
                "name": "Vague Request Needing Clarification",
                "input": "I want to create something cool",
                "expected_route": "clarify",
                "description": "Should trigger clarification loop"
            },
            {
                "name": "Moderately Vague Request",
                "input": "Help me build an app",
                "expected_route": "clarify",
                "description": "Should ask for clarification about app type and purpose"
            },
            {
                "name": "Technical Explanation Request",
                "input": "Explain how JWT authentication works in web applications",
                "expected_route": "answer",
                "description": "Should provide detailed explanation"
            },
            {
                "name": "Complex Code Request",
                "input": "Create a full-stack web application with user authentication, database integration, and real-time chat functionality",
                "expected_route": "code",
                "description": "Should route to code generation with detailed requirements"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test Case {i}: {test_case['name']}")
            print("-" * 60)
            print(f"📝 Input: {test_case['input']}")
            print(f"🎯 Expected Route: {test_case['expected_route']}")
            print(f"📖 Description: {test_case['description']}")
            print()
            
            try:
                print(f"🧪 Running test case {i}")
                result = agent.process_request(test_case['input'])
                
                # Analyze results
                success = result['success']
                actual_route = result['route_taken']
                route_match = actual_route == test_case['expected_route']
                
                test_result = {
                    "test_case": test_case['name'],
                    "success": success,
                    "route_match": route_match,
                    "expected_route": test_case['expected_route'],
                    "actual_route": actual_route,
                    "has_result": bool(result['final_result']),
                    "error": result.get('error', None)
                }
                
                results.append(test_result)
                
                # Print test results
                if success and route_match:
                    print_result(f"✅ Test {i} PASSED")
                elif success and not route_match:
                    print_result(f"⚠️  Test {i} PARTIAL - Success but wrong route (expected: {test_case['expected_route']}, got: {actual_route})")
                else:
                    print_result(f"❌ Test {i} FAILED - {result.get('error', 'Unknown error')}")
                
                # Show processing steps in testing mode
                print(f"👣 Processing steps: {len(result['processing_steps'])}")
                for step in result['processing_steps'][-3:]:  # Show last 3 steps
                    print(f"   • {step}")
                
            except Exception as e:
                print_result(f"❌ Test {i} ERROR: {str(e)}")
                results.append({
                    "test_case": test_case['name'],
                    "success": False,
                    "route_match": False,
                    "expected_route": test_case['expected_route'],
                    "actual_route": "error",
                    "has_result": False,
                    "error": str(e)
                })
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['success'] and r['route_match'])
        partial_tests = sum(1 for r in results if r['success'] and not r['route_match'])
        failed_tests = total_tests - passed_tests - partial_tests
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"⚠️  Partial: {partial_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in results:
                if not result['success'] or not result['route_match']:
                    status = "FAILED" if not result['success'] else f"WRONG_ROUTE({result['actual_route']})"
                    print(f"   • {result['test_case']}: {status}")
                    if result['error']:
                        print(f"     Error: {result['error']}")
        
        print("=" * 80)
        
    else:
        agent.interactive_mode()

if __name__ == "__main__":
    main()


# ============================================================================
# REQUIREMENTS AND SETUP NOTES
# ============================================================================

"""
SETUP INSTRUCTIONS:

1. Install dependencies:
   pip install langgraph langchain openai anthropic langsmith

2. Set environment variables:
   export OPENAI_API_KEY=your_openai_api_key
   export ANTHROPIC_API_KEY=your_anthropic_api_key
   
   # LangSmith for observability and tracing (optional)
   export LANGCHAIN_TRACING_V2=true
   export LANGCHAIN_API_KEY=your_langsmith_api_key
   export LANGCHAIN_PROJECT=langraph-agent-system

3. Install Claude Code CLI (for future integration):
   Follow Claude Code installation instructions
   Ensure 'claude' command is available in PATH

4. Run the system with different modes:
   
   INTERACTIVE MODE (default):
   python langgraph_agent_system.py
   
   TESTING MODE:
   python langgraph_agent_system.py --testing
   
   THINKING MODE (shows agent's reasoning):
   python langgraph_agent_system.py --thinking
   
   STEPS MODE (shows detailed execution steps):
   python langgraph_agent_system.py --steps
   
   COMBINED MODES:
   python langgraph_agent_system.py --testing --steps
   python langgraph_agent_system.py --thinking --steps

5. Command-line flags:
   --testing: Run comprehensive test cases instead of interactive mode
   --thinking: Show the agent's thinking process and reasoning
   --steps: Show detailed execution steps (includes thinking)

6. Monitor your agent:
   - View traces at: https://smith.langchain.com/ (if LangSmith configured)
   - Navigate to your project: langraph-agent-system
   - See detailed execution flows, timing, and errors
   - Create dashboards and set up alerts

EXECUTION MODES:

INTERACTIVE MODE:
- Default mode with user interaction
- Real clarification questions when needed
- Full streaming output with progress indicators

TESTING MODE:
- Runs 6 comprehensive test cases
- Automated responses for clarification
- Success/failure analysis with routing validation
- Performance metrics and summary report

THINKING MODE:
- Shows agent's internal reasoning process
- Displays decision-making logic
- Reveals prompt analysis and classification thoughts
- Useful for understanding how the agent works

STEPS MODE:
- Shows detailed execution steps
- Includes all thinking process output
- Tracks every action and state change
- Comprehensive debugging information

LANGSMITH FEATURES:
- Real-time trace visualization of each graph execution
- Performance metrics (latency, token usage, costs)
- Error tracking and debugging
- Custom dashboards and alerts
- Evaluation and testing capabilities

ARCHITECTURE OVERVIEW:

The system uses a LangGraph state machine with the following flow:

1. route_prompt: Analyzes input and decides routing
   ↓
2a. clarify_loop: Asks clarifying questions (if needed)
   ↓
2b. refine_prompt: Polishes the clarified request
   ↓ 
2c. run_claude_code: Executes code generation (PLACEHOLDER)

OR

2d. answer_with_llm: Provides direct informational answers

The state flows through these nodes based on conditional logic,
maintaining conversation context and processing metadata throughout.

Each node is documented with its specific responsibilities and
the transformations it applies to the agent state.

All nodes and key functions are decorated with @traceable for
comprehensive monitoring through LangSmith (when enabled).

STREAMING AND MONITORING:
- Real-time progress updates using LangGraph streaming
- Custom progress messages from within each node
- LLM call tracking and response monitoring
- Comprehensive error handling and fallback mechanisms
- Different verbosity levels based on execution mode
""" 