#!/usr/bin/env python3
"""
Demo script to test Claude Code integration in the LangGraph Agent System

This script demonstrates the new Claude Code integration with:
- Full permissions (--dangerously-skip-permissions)
- Streaming output to show Claude's thinking
- Real-time terminal feedback
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langgraph_agent_system import LangGraphAgentSystem

def demo_claude_code():
    """Demonstrate Claude Code integration with sample requests"""
    
    print("🎯 Claude Code Integration Demo")
    print("="*60)
    print("This demo showcases the new Claude Code integration with:")
    print("✅ Full permissions (--dangerously-skip-permissions)")
    print("✅ Streaming output showing Claude's thinking")  
    print("✅ Real-time terminal feedback")
    print("✅ Human-readable tool usage parsing")
    print("✅ Enhanced progress visibility")
    print("✅ Performance metrics")
    print("="*60)
    
    # Check if Claude Code is available
    import subprocess
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Claude Code CLI not found!")
            print("   Please run: python install_claude_code.py")
            return
        else:
            print(f"✅ Claude Code CLI found: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Claude Code CLI not found!")
        print("   Please run: python install_claude_code.py")
        return
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set!")
        print("   Please set: export ANTHROPIC_API_KEY=your_key_here")
        return
    else:
        print(f"✅ API key configured: {api_key[:8]}...{api_key[-4:]}")
    
    print("\n🚀 Initializing LangGraph Agent System...")
    agent = LangGraphAgentSystem()
    
    # Test cases for Claude Code integration
    test_cases = [
        {
            "name": "Simple Python Function",
            "prompt": "Create a Python function that calculates the factorial of a number with error handling",
            "description": "Basic code generation task"
        },
        {
            "name": "Web Component", 
            "prompt": "Build a React component for a simple todo list with add/delete functionality",
            "description": "Frontend development task"
        },
        {
            "name": "CLI Script",
            "prompt": "Create a command-line script that processes CSV files and generates summary statistics",
            "description": "Data processing task"
        }
    ]
    
    print(f"\n📋 Running {len(test_cases)} test cases...")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🧪 Test Case {i}: {test_case['name']}")
        print(f"📝 Description: {test_case['description']}")
        print(f"💬 Prompt: {test_case['prompt']}")
        print(f"{'='*60}")
        
        try:
            # Execute the request through the agent system
            result = agent.process_request(test_case["prompt"])
            
            print(f"\n📊 RESULTS for Test Case {i}:")
            print(f"   Route taken: {result.get('route_taken', 'unknown')}")
            print(f"   Processing steps: {len(result.get('processing_steps', []))}")
            
            if result.get('error_message'):
                print(f"   ❌ Error: {result['error_message']}")
            else:
                final_result = result.get('final_result', '')
                print(f"   ✅ Success: {len(final_result)} characters generated")
                
                # Show a preview of the result
                if final_result:
                    preview = final_result[:300] + "..." if len(final_result) > 300 else final_result
                    print(f"   📄 Preview: {preview}")
            
        except Exception as e:
            print(f"   💥 Unexpected error: {e}")
        
        if i < len(test_cases):
            input("\n⏸️  Press Enter to continue to next test case...")
    
    print(f"\n🎉 Demo completed!")
    print("="*60)
    print("Key features demonstrated:")
    print("✅ Intelligent routing to Claude Code for development tasks")
    print("✅ Streaming output showing Claude's thinking process")
    print("✅ Full permissions for complete tool access")
    print("✅ Human-readable tool usage and result parsing")
    print("✅ Real-time progress feedback with meaningful descriptions")
    print("✅ Comprehensive error handling and metrics")
    print("\n🔗 Ready for production use!")

def interactive_mode():
    """Run interactive mode for custom testing"""
    print("\n🎮 Interactive Mode")
    print("="*30)
    print("Enter your own prompts to test Claude Code integration.")
    print("Type 'quit' to exit.")
    
    agent = LangGraphAgentSystem()
    
    while True:
        try:
            prompt = input("\n💬 Your prompt: ").strip()
            
            if prompt.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if not prompt:
                print("⚠️  Please enter a prompt.")
                continue
            
            print(f"\n🚀 Processing: {prompt}")
            print("="*50)
            
            result = agent.process_request(prompt)
            
            print(f"\n📊 RESULT:")
            print(f"   Route: {result.get('route_taken', 'unknown')}")
            
            if result.get('error_message'):
                print(f"   ❌ Error: {result['error_message']}")
            else:
                final_result = result.get('final_result', '')
                print(f"   ✅ Success: {len(final_result)} characters")
                
                if final_result:
                    print(f"   📄 Result: {final_result[:500]}...")
                    
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"💥 Error: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Demo Claude Code integration")
    parser.add_argument("--interactive", "-i", action="store_true", 
                      help="Run in interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    else:
        demo_claude_code() 