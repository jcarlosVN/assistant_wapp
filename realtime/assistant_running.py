import os
import openai
import json
import time
from typing import Dict, Any
from dotenv import load_dotenv
from claude_chat_client import create_whatsapp_client

load_dotenv()

# Initialize clients
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
whatsapp_client = create_whatsapp_client("https://3319c2e6b9bd.ngrok-free.app")

# Load assistant configuration
try:
    with open("assistant_config.json", "r") as f:
        config = json.load(f)
    assistant_id = config["assistant_id"]
    print(f" Loaded assistant: {config['name']} ({config['model']})")
except FileNotFoundError:
    print("L Assistant config not found. Please run assistant_creator.py first.")
    exit(1)

# Create a new thread for this conversation
thread = openai_client.beta.threads.create()
print(f">� Created conversation thread: {thread.id}")

def execute_whatsapp_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute WhatsApp tool and return result as string"""
    try:
        if tool_name == "send_message":
            result = whatsapp_client.send_message(arguments["recipient"], arguments["message"])
        elif tool_name == "search_contacts":
            result = whatsapp_client.search_contacts(arguments["query"])
        elif tool_name == "list_messages":
            result = whatsapp_client.list_messages(**arguments)
        elif tool_name == "list_chats":
            result = whatsapp_client.list_chats(**arguments)
        elif tool_name == "send_file":
            result = whatsapp_client.send_file(arguments["recipient"], arguments["media_path"])
        elif tool_name == "download_media":
            result = whatsapp_client.download_media(arguments["message_id"], arguments["chat_jid"])
        elif tool_name == "check_new_messages":
            mark_as_seen = arguments.get("mark_as_seen", True)
            result = whatsapp_client.check_new_messages(mark_as_seen)
        elif tool_name == "mark_messages_as_seen":
            result = whatsapp_client.mark_messages_as_seen()
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {str(e)}"})

def wait_for_completion(thread_id: str, run_id: str) -> Dict[str, Any]:
    """Wait for assistant run completion with tool handling"""
    while True:
        try:
            run_status = openai_client.beta.threads.runs.retrieve(
                thread_id=thread_id, 
                run_id=run_id
            )
            
            if run_status.status == "completed":
                return {"status": "completed"}
                
            elif run_status.status == "requires_action":
                tool_outputs = []
                
                for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                    try:
                        if tool_call.type == "function":
                            # Handle WhatsApp function calls
                            args = json.loads(tool_call.function.arguments)
                            print(f"🔧 Executing WhatsApp tool: {tool_call.function.name}")
                            
                            result = execute_whatsapp_tool(tool_call.function.name, args)
                            tool_outputs.append({
                                "tool_call_id": tool_call.id,
                                "output": result
                            })
                        elif tool_call.type == "file_search":
                            # file_search is handled automatically by OpenAI
                            print(f"📄 File search operation in progress...")
                            # No output needed for file_search - it's handled internally
                            pass
                        else:
                            print(f"⚠️ Unknown tool type: {tool_call.type}")
                            
                    except Exception as e:
                        print(f"❌ Tool error: {e}")
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"error": str(e)})
                        })
                
                # Submit tool outputs (only if there are WhatsApp tool outputs)
                if tool_outputs:
                    openai_client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run_id,
                        tool_outputs=tool_outputs
                    )
                    
            elif run_status.status in ["failed", "cancelled", "expired"]:
                error_msg = f"Run {run_status.status}"
                if hasattr(run_status, 'last_error') and run_status.last_error:
                    error_msg += f": {run_status.last_error.message}"
                return {"status": "failed", "error": error_msg}
            
            time.sleep(1)
            
        except Exception as e:
            print(f"L Polling error: {e}")
            time.sleep(2)

def get_assistant_response(thread_id: str) -> str:
    """Get the latest assistant response"""
    messages = openai_client.beta.threads.messages.list(thread_id=thread_id, limit=1)
    
    for msg in messages.data:
        if msg.role == "assistant" and msg.content:
            content = msg.content[0]
            if hasattr(content, 'text') and content.text:
                return content.text.value
    
    return "No response received."

print("\n> WhatsApp Assistant is ready!")
print("=� Type your messages below (type 'quit' to exit):")
print("=� You can ask me to send messages, search contacts, list chats, etc.\n")

while True:
    try:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("=K Goodbye!")
            break
        
        if not user_input:
            continue
        
        # Add user message to thread
        openai_client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )
        
        # Run the assistant
        run = openai_client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )
        
        print("> Assistant is thinking...")
        
        # Wait for completion
        result = wait_for_completion(thread.id, run.id)
        
        if result["status"] == "completed":
            response = get_assistant_response(thread.id)
            print(f"> Assistant: {response}\n")
        else:
            print(f"L Error: {result.get('error', 'Unknown error')}\n")
            
    except KeyboardInterrupt:
        print("\n=K Goodbye!")
        break
    except Exception as e:
        print(f"L Error: {e}\n")