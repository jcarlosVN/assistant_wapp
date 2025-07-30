#!/usr/bin/env python3
"""
Simple Claude Chat API client with WhatsApp MCP connector integration.
Uses Anthropic Messages API to interact with WhatsApp via MCP server.

Usage:
1. Activate wapp_env: wapp_env\\Scripts\\activate.bat
2. Run: python claude_chat_api.py

Dependencies are installed in wapp_env virtual environment.
"""

import os
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# MCP Server configuration
MCP_SERVER_CONFIG = {
    "type": "url",
    "url": "https://ab9889ab3f65.ngrok-free.app/",  # Authenticated ngrok URL
    "name": "whatsapp-mcp-remote",
    "authorization_token": "microniii"  # From whatsapp-mcp-server/.env
}

def chat_with_whatsapp_access(user_message: str):
    """
    Send a message to Claude with WhatsApp MCP server access.
    
    Args:
        user_message: The message to send to Claude
        
    Returns:
        Claude's response with access to WhatsApp tools
    """
    try:
        print(f"🔗 Connecting to MCP server: {MCP_SERVER_CONFIG['url']}")
        response = client.beta.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user", 
                "content": user_message
            }],
            mcp_servers=[MCP_SERVER_CONFIG],
            betas=["mcp-client-2025-04-04"]
        )
        
        return response.content[0].text
        
    except anthropic.APIError as e:
        return f"API Error: {e.status_code} - {e.message}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    """
    Simple interactive chat loop
    """
    print("🤖 Claude Chat with WhatsApp MCP Access")
    print("📱 You can ask Claude to interact with your WhatsApp")
    print("💡 Try: 'List my recent WhatsApp chats' or 'Send a message to [contact]'")
    print("🚪 Type 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
                
            if not user_input:
                continue
                
            print("🤔 Claude is thinking...")
            response = chat_with_whatsapp_access(user_input)
            print(f"\n🤖 Claude: {response}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    # Test connection first
    print("🔧 Testing connection to Claude with WhatsApp MCP...")
    
    # Try a simple test message first
    test_response = chat_with_whatsapp_access("Hello, can you see this message?")
    if "Error:" in test_response or "API Error:" in test_response:
        print(f"❌ Connection failed: {test_response}")
        print("🔍 Make sure:")
        print("   1. Your ngrok server is running")
        print("   2. main_mcp_remote.py is running")
        print("   3. Your API key is correct in .env")
        print("   4. Try restarting ngrok if URL changed")
        
        # Try alternative approach without MCP
        print("\n🔄 Testing without MCP server...")
        try:
            simple_response = client.beta.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": "Hello, are you open ai or anthropic team?"}],
                betas=["mcp-client-2025-04-04"]
            )
            print(f"✅ Basic API working: {simple_response.content[0].text}")
            print("❌ Issue is specifically with MCP server connection")
        except Exception as e:
            print(f"❌ Basic API also failing: {e}")
    else:
        print("✅ Connection successful!")
        print(f"🤖 Claude says: {test_response}\n")
        
        # Start interactive chat
        main()