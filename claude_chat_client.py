#!/usr/bin/env python3
"""
WhatsApp MCP Client - A comprehensive client for interacting with WhatsApp MCP Remote Server
Provides easy-to-use functions for all WhatsApp operations through the MCP protocol.
"""

import json
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WhatsAppMCPClient:
    """Client for WhatsApp MCP Remote Server"""
    
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        """
        Initialize the WhatsApp MCP client
        
        Args:
            base_url: Base URL of the MCP server (e.g., "https://ab9889ab3f65.ngrok-free.app")
            auth_token: Optional authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token or os.getenv("MCP_AUTH_TOKEN")
        self.headers = {
            "Content-Type": "application/json"
        }
        
        if self.auth_token and self.auth_token != "your-secret-token-here":
            self.headers["Authorization"] = f"Bearer {self.auth_token}"
    
    def _make_mcp_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an MCP JSON-RPC 2.0 request
        
        Args:
            method: MCP method name
            params: Optional parameters
            
        Returns:
            Response data
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1
        }
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                raise Exception(f"MCP Error: {result['error'].get('message', 'Unknown error')}")
            
            return result.get("result", {})
            
        except requests.RequestException as e:
            raise Exception(f"Request failed: {str(e)}")
    
    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a WhatsApp MCP tool
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool result
        """
        result = self._make_mcp_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
            "server_name": "whatsapp-mcp-remote"
        })
        
        # Extract content from MCP response
        if "content" in result and result["content"]:
            content_text = result["content"][0].get("text", "")
            try:
                return json.loads(content_text)
            except json.JSONDecodeError:
                return content_text
        
        return result
    
    def search_contacts(self, query: str) -> List[Dict[str, Any]]:
        """
        Search WhatsApp contacts by name or phone number
        
        Args:
            query: Search term to match against contact names or phone numbers
            
        Returns:
            List of matching contacts
        """
        return self._call_tool("search_contacts", {"query": query})
    
    def list_messages(self, 
                     after: Optional[str] = None,
                     before: Optional[str] = None,
                     sender_phone_number: Optional[str] = None,
                     chat_jid: Optional[str] = None,
                     query: Optional[str] = None,
                     limit: int = 20,
                     page: int = 0) -> List[Dict[str, Any]]:
        """
        Get WhatsApp messages matching specified criteria
        
        Args:
            after: ISO-8601 formatted string to only return messages after this date
            before: ISO-8601 formatted string to only return messages before this date
            sender_phone_number: Phone number to filter messages by sender
            chat_jid: Chat JID to filter messages by chat
            query: Search term to filter messages by content
            limit: Maximum number of messages to return (default: 20)
            page: Page number for pagination (default: 0)
            
        Returns:
            List of messages
        """
        params = {
            "limit": limit,
            "page": page
        }
        
        if after:
            params["after"] = after
        if before:
            params["before"] = before
        if sender_phone_number:
            params["sender_phone_number"] = sender_phone_number
        if chat_jid:
            params["chat_jid"] = chat_jid
        if query:
            params["query"] = query
            
        return self._call_tool("list_messages", params)
    
    def list_chats(self,
                   query: Optional[str] = None,
                   limit: int = 20,
                   page: int = 0,
                   include_last_message: bool = True,
                   sort_by: str = "last_active") -> List[Dict[str, Any]]:
        """
        Get WhatsApp chats matching specified criteria
        
        Args:
            query: Search term to filter chats by name or JID
            limit: Maximum number of chats to return (default: 20)
            page: Page number for pagination (default: 0)
            include_last_message: Whether to include the last message in each chat (default: True)
            sort_by: Field to sort results by (default: "last_active")
            
        Returns:
            List of chats
        """
        params = {
            "limit": limit,
            "page": page,
            "include_last_message": include_last_message,
            "sort_by": sort_by
        }
        
        if query:
            params["query"] = query
            
        return self._call_tool("list_chats", params)
    
    def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """
        Send a WhatsApp message to a person or group
        
        Args:
            recipient: Phone number with country code (e.g., "51959823646") or JID
            message: The message text to send
            
        Returns:
            Dict with success status and message
        """
        return self._call_tool("send_message", {
            "recipient": recipient,
            "message": message
        })
    
    def send_file(self, recipient: str, media_path: str) -> Dict[str, Any]:
        """
        Send a file via WhatsApp
        
        Args:
            recipient: Phone number with country code or JID
            media_path: Absolute path to the media file
            
        Returns:
            Dict with success status and message
        """
        return self._call_tool("send_file", {
            "recipient": recipient,
            "media_path": media_path
        })
    
    def download_media(self, message_id: str, chat_jid: str) -> Dict[str, Any]:
        """
        Download media from a WhatsApp message
        
        Args:
            message_id: ID of the message containing the media
            chat_jid: JID of the chat containing the message
            
        Returns:
            Dict with success status, message, and file_path if successful
        """
        return self._call_tool("download_media", {
            "message_id": message_id,
            "chat_jid": chat_jid
        })
    
    def check_new_messages(self, mark_as_seen: bool = True) -> List[Dict[str, Any]]:
        """
        Check for new WhatsApp messages since the last check. This enables message notifications.
        
        Args:
            mark_as_seen: Whether to mark the returned messages as seen (default: True)
            
        Returns:
            List of new messages that arrived since the last check
        """
        return self._call_tool("check_new_messages", {
            "mark_as_seen": mark_as_seen
        })
    
    def mark_messages_as_seen(self) -> Dict[str, Any]:
        """
        Mark all current messages as seen, so they won't appear in future new message checks.
        
        Returns:
            Dict with success status and message
        """
        return self._call_tool("mark_messages_as_seen", {})
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information and status
        
        Returns:
            Server information dict
        """
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to get server info: {str(e)}")
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get list of available MCP tools
        
        Returns:
            List of available tools with their schemas
        """
        result = self._make_mcp_request("tools/list")
        return result.get("tools", [])


def create_whatsapp_client(base_url: str, auth_token: Optional[str] = None) -> WhatsAppMCPClient:
    """
    Create a WhatsApp MCP client instance
    
    Args:
        base_url: Base URL of the MCP server
        auth_token: Optional authentication token
        
    Returns:
        WhatsAppMCPClient instance
    """
    return WhatsAppMCPClient(base_url, auth_token)