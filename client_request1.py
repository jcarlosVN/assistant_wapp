#!/usr/bin/env python3
"""
Cliente simple para enviar mensajes de WhatsApp usando el servidor MCP.
Ejemplo de uso básico.
"""

import subprocess
import json
import time
import sys


def send_whatsapp_message(phone_number: str, message: str) -> bool:
    """
    Envía un mensaje de WhatsApp usando el servidor MCP.
    
    Args:
        phone_number: Número de teléfono (ej: "959888222")
        message: Mensaje a enviar
        
    Returns:
        True si el mensaje se envió exitosamente, False en caso contrario
    """
    
    # Comando para iniciar el servidor MCP
    server_command = [
        r"C:\Users\jeanc\iCloudDrive\Python\Wapp_mcp_test3\whatsapp-mcp\wapp_env\Scripts\uv.exe",
        "--directory",
        r"C:\Users\jeanc\iCloudDrive\Python\Wapp_mcp_test3\whatsapp-mcp\whatsapp-mcp-server",
        "run",
        "main.py"
    ]
    
    process = None
    try:
        print(f"Enviando mensaje a {phone_number}: {message}")
        print("Iniciando servidor MCP...")
        
        # Iniciar el servidor MCP
        process = subprocess.Popen(
            server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Esperar a que el servidor se inicialice
        time.sleep(3)
        
        # Verificar que el servidor esté ejecutándose
        if process.poll() is not None:
            print("✗ El servidor MCP no se pudo iniciar")
            stderr_output = process.stderr.read() if process.stderr else ""
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
        
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        response = process.stdout.readline()
        
        if not response:
            print("✗ No se recibió respuesta de inicialización")
            return False
        
        init_response = json.loads(response.strip())
        if "error" in init_response:
            print(f"✗ Error en inicialización: {init_response['error']}")
            return False
        
        # 2. Enviar notificación de inicialización completa
        initialized_request = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        process.stdin.write(json.dumps(initialized_request) + '\n')
        process.stdin.flush()
        
        # 3. Enviar el mensaje
        send_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "send_message",
                "arguments": {
                    "recipient": phone_number,
                    "message": message
                }
            }
        }
        
        process.stdin.write(json.dumps(send_request) + '\n')
        process.stdin.flush()
        
        # Leer respuesta
        response = process.stdout.readline()
        if not response:
            print("✗ No se recibió respuesta del envío")
            return False
        
        send_response = json.loads(response.strip())
        
        # Procesar resultado
        if "result" in send_response:
            result = send_response["result"]
            # FastMCP devuelve una lista con el resultado
            if isinstance(result, list) and len(result) > 0:
                actual_result = result[0]
                if isinstance(actual_result, dict):
                    if actual_result.get("success"):
                        print(f"✓ {actual_result.get('message', 'Mensaje enviado')}")
                        return True
                    else:
                        print(f"✗ {actual_result.get('message', 'Error al enviar')}")
                        return False
            
            print(f"✓ Respuesta: {result}")
            return True
            
        elif "error" in send_response:
            print(f"✗ Error: {send_response['error']}")
            return False
        else:
            print(f"✗ Respuesta inesperada: {send_response}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        if process:
            process.terminate()
            process.wait()
            print("✓ Servidor MCP detenido")


def main():
    """Función principal para enviar el mensaje de prueba."""
    phone_number = "51959812636"
    message = "please response the message"
    
    print("=== Cliente Simple WhatsApp MCP ===")
    success = send_whatsapp_message(phone_number, message)
    
    if success:
        print("\n✓ Proceso completado exitosamente")
        sys.exit(0)
    else:
        print("\n✗ El proceso falló")
        sys.exit(1)


if __name__ == "__main__":
    main()
