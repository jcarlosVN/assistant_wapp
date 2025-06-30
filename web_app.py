from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
from simple_client_requests2 import send_whatsapp_message

app = FastAPI(title="WhatsApp Web Sender")

# Configurar templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    """Mostrar el formulario para enviar mensajes"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/send", response_class=HTMLResponse)
async def send_message(request: Request, phone_number: str = Form(...), message: str = Form(...)):
    """Procesar el envío del mensaje"""
    
    # Validar inputs
    if not phone_number.strip():
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "El número de teléfono es requerido",
            "phone_number": phone_number,
            "message": message
        })
    
    if not message.strip():
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "El mensaje es requerido",
            "phone_number": phone_number,
            "message": message
        })
    
    # Enviar mensaje
    result = send_whatsapp_message(phone_number.strip(), message.strip())
    
    if result["success"]:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "success": result["message"],
            "phone_number": "",
            "message": ""
        })
    else:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": result["message"],
            "phone_number": phone_number,
            "message": message
        })

if __name__ == "__main__":
    uvicorn.run("web_app:app", host="0.0.0.0", port=5002, reload=True)
