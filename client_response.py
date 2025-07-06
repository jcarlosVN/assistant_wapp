#!/usr/bin/env python3
"""
Cliente simple mejorado para leer mensajes de WhatsApp usando el servidor MCP.
Versión con mejor manejo de codificación UTF-8 y errores.
"""

import subprocess
import json
import time
import sys
import os
from datetime import datetime


def read_whatsapp_messages(phone_number: str, limit: int = 10) -> bool:
    """
    Lee mensajes de WhatsApp de un número específico usando el servidor MCP.
    
    Args:
        phone_number: Número de teléfono del cual leer mensajes (ej: "51959812636")
        limit: Número máximo de mensajes a leer (default: 10)
        
    Returns:
        True si se pudieron leer los mensajes exitosamente, False en caso contrario
    """
    
    # Comando para iniciar el servidor MCP (mismo que funciona en simple_client.py)
    server_command = [
        r"C:\Users\jeanc\iCloudDrive\Python\Wapp_mcp_test3\whatsapp-mcp\wapp_env\Scripts\uv.exe",
        "--directory",
        r"C:\Users\jeanc\iCloudDrive\Python\Wapp_mcp_test3\whatsapp-mcp\whatsapp-mcp-server",
        "run",
        "main.py"
    ]
    
    process = None
    try:
        print(f"Leyendo mensajes del número: {phone_number}")
        print("Iniciando servidor MCP...")
        
        # Configurar variables de entorno para UTF-8
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Iniciar el servidor MCP con codificación UTF-8
        process = subprocess.Popen(
            server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=0,
            env=env
        )
        
        # Esperar a que el servidor se inicialice
        time.sleep(3)
        
        # Verificar que el servidor esté ejecutándose
        if process.poll() is not None:
            print("✗ El servidor MCP no se pudo iniciar")
            stderr_output = ""
            try:
                stderr_output = process.stderr.read() if process.stderr else ""
            except:
                pass
            if stderr_output:
                print(f"Error: {stderr_output}")
            return False
        
        print("✓ Servidor MCP iniciado")
        
        # 1. Inicializar la conexión
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "simple-client", "version": "1.0.0"}
            }
        }
        
        try:
            process.stdin.write(json.dumps(init_request, ensure_ascii=False) + '\n')
            process.stdin.flush()
            response = process.stdout.readline()
            
            if not response:
                print("✗ No se recibió respuesta de inicialización")
                return False
            
            init_response = json.loads(response.strip())
            if "error" in init_response:
                print(f"✗ Error en inicialización: {init_response['error']}")
                return False
                
        except Exception as e:
            print(f"✗ Error en inicialización: {e}")
            return False
        
        # 2. Enviar notificación de inicialización completa
        try:
            initialized_request = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            
            process.stdin.write(json.dumps(initialized_request, ensure_ascii=False) + '\n')
            process.stdin.flush()
            
        except Exception as e:
            print(f"✗ Error enviando notificación: {e}")
            return False
        
        # 3. Buscar mensajes del número específico
        try:
            messages_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "list_messages",
                    "arguments": {
                        "sender_phone_number": phone_number,
                        "limit": limit,
                        "include_context": True
                    }
                }
            }
            
            process.stdin.write(json.dumps(messages_request, ensure_ascii=False) + '\n')
            process.stdin.flush()
            
            # Leer respuesta con timeout
            response = process.stdout.readline()
            if not response:
                print("✗ No se recibió respuesta de la búsqueda de mensajes")
                return False
            
            messages_response = json.loads(response.strip())
            
        except json.JSONDecodeError as e:
            print(f"✗ Error decodificando JSON: {e}")
            print(f"Respuesta recibida: {repr(response[:200])}")
            return False
        except Exception as e:
            print(f"✗ Error buscando mensajes: {e}")
            return False
        
        # Procesar resultado
        if "result" in messages_response:
            result = messages_response["result"]
            # FastMCP devuelve una lista con el resultado
            if isinstance(result, list) and len(result) > 0:
                messages = result[0]
                if isinstance(messages, list):
                    print(f"\n✓ Encontrados {len(messages)} mensajes del número {phone_number}:")
                    print("=" * 60)
                    
                    for i, msg in enumerate(messages, 1):
                        try:
                            timestamp = msg.get('timestamp', 'Sin fecha')
                            sender = msg.get('sender', 'Desconocido')
                            content = msg.get('content', '')
                            is_from_me = msg.get('is_from_me', False)
                            media_type = msg.get('media_type', '')
                            
                            # Formatear timestamp si está disponible
                            try:
                                if timestamp and timestamp != 'Sin fecha':
                                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                                else:
                                    formatted_time = timestamp
                            except:
                                formatted_time = timestamp
                            
                            # Indicar quién envió el mensaje
                            direction = "→ Tú enviaste" if is_from_me else f"← {sender} envió"
                            
                            print(f"\n[{i}] {formatted_time}")
                            print(f"    {direction}:")
                            
                            if media_type:
                                print(f"    📎 Media: {media_type}")
                            
                            if content:
                                # Limpiar contenido de caracteres problemáticos
                                clean_content = content.encode('utf-8', errors='replace').decode('utf-8')
                                # Limitar contenido muy largo
                                if len(clean_content) > 200:
                                    print(f"    💬 {clean_content[:200]}...")
                                else:
                                    print(f"    💬 {clean_content}")
                            
                            if not content and not media_type:
                                print(f"    (Mensaje sin contenido)")
                                
                        except Exception as e:
                            print(f"    ✗ Error procesando mensaje {i}: {e}")
                            continue
                    
                    print("=" * 60)
                    return True
                else:
                    print(f"✗ No se encontraron mensajes del número {phone_number}")
                    return False
            
            print(f"✓ Respuesta: {result}")
            return True
            
        elif "error" in messages_response:
            print(f"✗ Error: {messages_response['error']}")
            return False
        else:
            print(f"✗ Respuesta inesperada: {messages_response}")
            return False
            
    except Exception as e:
        print(f"✗ Error general: {e}")
        return False
    finally:
        if process:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
            print("\n✓ Servidor MCP detenido")


def main():
    """Función principal para leer mensajes del número específico."""
    phone_number = "51959812636"
    
    print("=== Cliente Simple WhatsApp MCP - Lector de Mensajes (Mejorado) ===")
    
    # Leer los mensajes
    print(f"\n--- Mensajes Recientes ---")
    success = read_whatsapp_messages(phone_number, limit=15)
    
    if success:
        print("\n✓ Proceso completado exitosamente")
        sys.exit(0)
    else:
        print("\n✗ El proceso falló")
        sys.exit(1)


if __name__ == "__main__":
    main()
