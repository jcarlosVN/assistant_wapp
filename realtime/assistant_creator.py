# -*- coding: utf-8 -*-
import os
import openai
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get vector store ID from environment
vector_store_id_raw = os.getenv("VECTOR_STORE_IDS")

# Parse single vector store ID (remove array brackets if present)
vector_store_id = None
if vector_store_id_raw:
    if vector_store_id_raw.startswith('[') and vector_store_id_raw.endswith(']'):
        # Extract first ID from array format: [vs_123] or [vs_123, vs_456]
        ids_content = vector_store_id_raw.strip('[]')
        first_id = ids_content.split(',')[0].strip()
        vector_store_id = first_id
    else:
        # Single ID format
        vector_store_id = vector_store_id_raw.strip()

# Define WhatsApp tools based on claude_chat_client.py
whatsapp_tools = [
    {
        "type": "function",
        "function": {
            "name": "send_message",
            "description": "Send a WhatsApp message to a person or group",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "Phone number with country code (e.g. '51959812636') or JID"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message text to send"
                    }
                },
                "required": ["recipient", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_contacts",
            "description": "Search WhatsApp contacts by name or phone number",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term to match against contact names or phone numbers"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_messages",
            "description": "Get WhatsApp messages with filtering options",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of messages to return",
                        "default": 20
                    },
                    "sender_phone_number": {
                        "type": "string",
                        "description": "Phone number to filter messages by sender"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search term to filter messages by content"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_chats",
            "description": "Get WhatsApp chats list",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of chats to return",
                        "default": 20
                    },
                    "query": {
                        "type": "string",
                        "description": "Search term to filter chats by name"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_file",
            "description": "Send a file via WhatsApp",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "Phone number with country code or JID"
                    },
                    "media_path": {
                        "type": "string",
                        "description": "Absolute path to the media file"
                    }
                },
                "required": ["recipient", "media_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_media",
            "description": "Download media from a WhatsApp message",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {
                        "type": "string",
                        "description": "ID of the message containing the media"
                    },
                    "chat_jid": {
                        "type": "string",
                        "description": "JID of the chat containing the message"
                    }
                },
                "required": ["message_id", "chat_jid"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_new_messages",
            "description": "Check for new WhatsApp messages since the last check. This enables message notifications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mark_as_seen": {
                        "type": "boolean",
                        "description": "Whether to mark the returned messages as seen (default: True)",
                        "default": True
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mark_messages_as_seen",
            "description": "Mark all current messages as seen, so they won't appear in future new message checks.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# Combine WhatsApp tools with file_search
tools = whatsapp_tools.copy()
tools.append({"type": "file_search"})

# Configure tool_resources for file_search
tool_resources = {}
if vector_store_id:
    tool_resources["file_search"] = {"vector_store_ids": [vector_store_id]}

# Create the Hybrid WhatsApp Assistant
assistant = client.beta.assistants.create(
    name="Hybrid WhatsApp Assistant",
    instructions="""You are a hybrid WhatsApp assistant that can:
1. Manage WhatsApp operations: send messages, search contacts, list messages and chats, send files, download media, and check for new messages
2. Search through uploaded documents using file_search to find relevant information
3. Combine information from both WhatsApp and documents when needed

Use WhatsApp tools for messaging operations and file_search for document queries. Always be helpful and clear in your responses.""",
    tools=tools,
    tool_resources=tool_resources if tool_resources else None,
    model="gpt-4o-mini",
    temperature=0.7,
    response_format={"type": "text"}
)

# Save assistant and thread IDs to a file for the runner
config = {
    "assistant_id": assistant.id,
    "model": assistant.model,
    "name": assistant.name
}

with open("assistant_config.json", "w") as f:
    json.dump(config, f, indent=2)

print("Hybrid WhatsApp Assistant created successfully!")
print(f"Assistant ID: {assistant.id}")
print(f"Model: {assistant.model}")
print(f"Vector Store ID: {vector_store_id if vector_store_id else 'None'}")
print(f"Tools: WhatsApp functions + {'File Search' if vector_store_id else 'No File Search'}")
print(f"Configuration saved to: assistant_config.json")
print("\nYou can now run assistant_running.py to start chatting!")