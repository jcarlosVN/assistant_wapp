import asyncio
import sys
import os
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class WhatsAppMCPClient:
    def __init__(self):
        """Inicializar el cliente MCP para WhatsApp."""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        
        # Inicializar cliente de Anthropic
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY no encontrada en variables de entorno")
        
        self.anthropic = Anthropic(api_key=api_key)
        print("✓ Cliente Anthropic inicializado")

    async def connect_to_whatsapp_server(self):
        """Conectar al servidor MCP de WhatsApp."""
        
        # Configuración específica para tu servidor de WhatsApp
        # Usando la misma configuración que tienes en Claude Desktop
        server_params = StdioServerParameters(
            command=r"C:\Users\jeanc\iCloudDrive\Python\Wapp_mcp_test3\whatsapp-mcp - copia\wapp_env\Scripts\uv.exe",
            args=[
                "--directory",
                r"C:\Users\jeanc\iCloudDrive\Python\Wapp_mcp_test3\whatsapp-mcp - copia\whatsapp-mcp-server",
                "run",
                "main.py"
            ],
            env=None
        )
        
        try:
            # Conectar al servidor
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            
            # Inicializar sesión
            await self.session.initialize()
            
            # Listar herramientas disponibles
            response = await self.session.list_tools()
            tools = response.tools
            
            print("✓ Conectado al servidor de WhatsApp MCP")
            print(f"📱 Herramientas disponibles ({len(tools)}):")
            for tool in tools:
                print(f"  • {tool.name}: {tool.description}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error conectando al servidor: {e}")
            return False

    async def process_query(self, query: str) -> str:
        """Procesar una consulta usando Claude y las herramientas de WhatsApp."""
        
        if not self.session:
            return "❌ No hay conexión al servidor MCP"
        
        try:
            # Obtener herramientas disponibles
            response = await self.session.list_tools()
            available_tools = [{ 
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            } for tool in response.tools]

            # Mensaje inicial al usuario
            messages = [
                {
                    "role": "user",
                    "content": query
                }
            ]

            # Llamada inicial a Claude
            response = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=messages,
                tools=available_tools
            )

            final_text = []

            # Separar texto inicial de las herramientas
            initial_text = ""
            tools_to_execute = []
            
            for content in response.content:
                if content.type == 'text':
                    initial_text = content.text
                    final_text.append(content.text)
                elif content.type == 'tool_use':
                    tools_to_execute.append(content)
            
            # Ejecutar cada herramienta
            for tool_content in tools_to_execute:
                tool_name = tool_content.name
                tool_args = tool_content.input
                
                print(f"🔧 Ejecutando: {tool_name}")
                
                try:
                    result = await self.session.call_tool(tool_name, tool_args)
                    
                    # Construir mensaje del assistant correctamente
                    assistant_content = []
                    
                    # Solo agregar texto si existió en la respuesta inicial
                    if initial_text and initial_text.strip():
                        assistant_content.append({
                            "type": "text",
                            "text": initial_text
                        })
                    
                    # Agregar la herramienta usada
                    assistant_content.append({
                        "type": "tool_use",
                        "id": tool_content.id,
                        "name": tool_name,
                        "input": tool_args
                    })
                    
                    # Validar que tenemos contenido válido antes de agregar
                    if assistant_content and len(assistant_content) > 0:
                        # Verificar que no tengamos solo bloques de texto vacíos
                        has_valid_content = False
                        for block in assistant_content:
                            if block["type"] == "tool_use":
                                has_valid_content = True
                                break
                            elif block["type"] == "text" and block.get("text", "").strip():
                                has_valid_content = True
                                break
                        
                        if has_valid_content:
                            messages.append({
                                "role": "assistant", 
                                "content": assistant_content
                            })
                    
                    # Agregar resultado de la herramienta
                    messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_content.id,
                                "content": str(result.content)
                            }
                        ]
                    })

                    # Obtener respuesta final de Claude
                    final_response = self.anthropic.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=2000,
                        messages=messages,
                    )

                    for final_content in final_response.content:
                        if final_content.type == 'text':
                            final_text.append(final_content.text)
                            
                except Exception as e:
                    final_text.append(f"❌ Error ejecutando {tool_name}: {str(e)}")

            return "\n".join(final_text) if final_text else "No se obtuvo respuesta."
            
        except Exception as e:
            return f"❌ Error procesando consulta: {str(e)}"

    async def chat_loop(self):
        """Ejecutar bucle de chat interactivo."""
        print("\n" + "="*60)
        print("🚀 Cliente WhatsApp MCP iniciado!")
        print("💬 Puedes hacer preguntas sobre tus mensajes de WhatsApp")
        print("📝 Ejemplos:")
        print("  • 'busca contactos con el nombre Juan'")
        print("  • 'muestra mis últimos mensajes'")
        print("  • 'envía un mensaje a +1234567890 diciendo Hola'")
        print("  • 'descarga la imagen del mensaje ID xxx'")
        print("❌ Escribe 'quit' para salir")
        print("="*60)
        
        while True:
            try:
                print("\n" + "-"*40)
                query = input("🎤 Tu consulta: ").strip()
                
                if query.lower() in ['quit', 'exit', 'salir']:
                    print("👋 ¡Hasta luego!")
                    break
                
                if not query:
                    continue
                    
                print("\n🤔 Procesando...")
                response = await self.process_query(query)
                print(f"\n🤖 Respuesta:\n{response}")
                    
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                print(f"\n❌ Error inesperado: {str(e)}")
    
    async def cleanup(self):
        """Limpiar recursos."""
        await self.exit_stack.aclose()
        print("🧹 Recursos liberados")

async def main():
    """Función principal."""
    
    # Verificar que el servidor Go esté corriendo
    print("⚠️  IMPORTANTE: Asegúrate de que el servidor Go esté corriendo:")
    print("   cd whatsapp-bridge && go run main.go")
    
    input("\n⏳ Presiona Enter cuando el servidor Go esté listo...")
    
    client = WhatsAppMCPClient()
    
    try:
        # Conectar al servidor
        connected = await client.connect_to_whatsapp_server()
        
        if not connected:
            print("❌ No se pudo conectar al servidor MCP")
            return
        
        # Iniciar bucle de chat
        await client.chat_loop()
        
    except Exception as e:
        print(f"❌ Error en el cliente: {str(e)}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())