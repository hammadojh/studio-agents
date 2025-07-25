#!/usr/bin/env python3
"""
Simple script to visualize the LangGraph agent system using built-in LangGraph methods.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path so we can import our agent system
sys.path.append(str(Path(__file__).parent))

try:
    from langgraph_agent_system import build_agent_graph
except ImportError:
    print("❌ Could not import langgraph_agent_system.py")
    print("Make sure the script is in the same directory as langgraph_agent_system.py")
    sys.exit(1)

def visualize_graph():
    """Create and visualize the LangGraph agent system."""
    print("🚀 Building LangGraph agent system...")
    
    # Build the compiled graph
    compiled_graph = build_agent_graph()
    
    # Get the graph structure for visualization
    graph = compiled_graph.get_graph()
    
    print("\n📊 Generating Mermaid diagram...")
    
    # Generate Mermaid syntax using LangGraph's built-in method
    mermaid_syntax = graph.draw_mermaid(
        with_styles=True,
        wrap_label_n_words=6
    )
    
    # Save to file
    output_file = "langgraph_agent_diagram.mmd"
    with open(output_file, 'w') as f:
        f.write(mermaid_syntax)
    
    print(f"✅ Mermaid diagram saved to: {output_file}")
    print("\n📋 Mermaid syntax:")
    print("=" * 50)
    print(mermaid_syntax)
    print("=" * 50)
    
    # Optional: Generate PNG if requested
    generate_png = input("\n🖼️  Generate PNG image? (y/n): ").lower().strip() == 'y'
    
    if generate_png:
        try:
            print("🎨 Generating PNG...")
            png_bytes = graph.draw_mermaid_png(
                output_file_path="langgraph_agent_diagram.png"
            )
            print("✅ PNG diagram saved to: langgraph_agent_diagram.png")
        except Exception as e:
            print(f"❌ Failed to generate PNG: {e}")
            print("💡 Tip: PNG generation requires internet connection or additional dependencies")
    
    # Display helpful information
    print("\n🔗 You can also:")
    print(f"1. Copy the Mermaid syntax and paste it at: https://mermaid.live/")
    print(f"2. Use the generated .mmd file with Mermaid CLI or VS Code extensions")
    print(f"3. View the .png file if generated successfully")

if __name__ == "__main__":
    try:
        visualize_graph()
    except KeyboardInterrupt:
        print("\n👋 Visualization cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1) 