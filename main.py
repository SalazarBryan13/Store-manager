from fastapi import FastAPI, Request, Form, Depends, Query, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from database import get_db, engine
import models
from datetime import datetime, date
from typing import Optional, Dict, List, Any
import uvicorn
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
import openai

# Cargar variables de entorno
load_dotenv()

# Configurar OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Crear las tablas en la base de datos
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clínica Dental")

# Configuración de seguridad
security = HTTPBasic()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates configuration
templates = Jinja2Templates(directory="templates")

# Credenciales de administrador
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "P@ssw0rd"

def verify_admin(request: Request):
    is_authenticated = request.session.get("is_authenticated", False)
    if not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"},
        )
    return True

async def get_chatgpt_response(prompt: str, history: List[Dict[str, str]] = []) -> str:
    """
    Obtiene una respuesta de ChatGPT usando la API de OpenAI.
    """
    try:
        # Convertir el historial al formato que espera OpenAI
        messages = [
            {"role": "system", "content": """Eres un asistente virtual dental profesional y empático de la clínica DentalCare. 
            Tu tarea es ayudar a los pacientes respondiendo preguntas sobre salud dental, evaluando síntomas iniciales, 
            proporcionando información sobre tratamientos y ayudando a programar citas.

            Información importante de la clínica:
            - Horario: Lunes a Viernes 9:00-20:00, Sábados 10:00-15:00
            - Teléfono: +34 900 123 456
            - Servicios principales: Limpieza dental, empastes, extracciones, ortodoncia, blanqueamiento, implantes
            - Emergencias disponibles 24/7

            Directrices:
            1. Sé empático y profesional en tus respuestas
            2. Para emergencias, proporciona el número de emergencias y pide detalles de los síntomas
            3. Para consultas médicas, da información general pero recomienda una evaluación presencial
            4. Para citas, pregunta sobre el tipo de servicio necesario y horarios preferidos
            5. Mantén un tono conversacional pero profesional
            6. Si no estás seguro de algo, sugiere contactar directamente con la clínica"""}
        ]

        # Agregar el historial de conversación
        for msg in history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Agregar el mensaje actual del usuario
        messages.append({"role": "user", "content": prompt})

        # Llamar a la API de OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        # Extraer la respuesta
        return response.choices[0].message['content']

    except Exception as e:
        print(f"Error calling ChatGPT API: {str(e)}")
        return "Lo siento, estoy teniendo dificultades técnicas. Por favor, contacta directamente con la clínica al +34 900 123 456."

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/services")
def services(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/about")
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/assistant")
async def assistant(request: Request):
    return templates.TemplateResponse("assistant.html", {"request": request})

class ChatMessage(BaseModel):
    message: str
    history: List[Dict[str, str]] = []

@app.post("/chat")
async def chat(chat_data: ChatMessage):
    try:
        # Obtener respuesta de ChatGPT
        response = await get_chatgpt_response(chat_data.message, chat_data.history)
        
        # Guardar el historial de la conversación
        chat_history = chat_data.history
        chat_history.append({
            "role": "user",
            "content": chat_data.message
        })
        chat_history.append({
            "role": "assistant",
            "content": response
        })
        
        return JSONResponse(content={
            "response": response,
            "history": chat_history
        })
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": "Error procesando la consulta"}
        )

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["is_authenticated"] = True
        return RedirectResponse(url="/admin", status_code=303)
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuario o contraseña incorrectos"}
        )

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@app.post("/submit-contact")
async def submit_contact(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    service: str = Form(...),
    message: str = Form(...)
):
    # Crear nuevo registro en la base de datos
    new_contact = models.Formulario(
        name=name,
        email=email,
        phone=phone,
        service=service,
        message=message,
        created_at=datetime.now()
    )
    
    # Guardar en la base de datos
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    
    # Redireccionar con mensaje de éxito
    return RedirectResponse(url="/contact?success=true", status_code=303)

class StatusUpdate(BaseModel):
    status: str

class CitaUpdate(BaseModel):
    name: str
    created_at: str

@app.get("/admin")
async def admin_panel(
    request: Request,
    db: Session = Depends(get_db),
    date: Optional[str] = None,
    service: Optional[str] = None,
    search: Optional[str] = None,
    authenticated: bool = Depends(verify_admin)
):
    try:
        # Consulta base
        query = db.query(models.Formulario)
        
        # Aplicar filtros si existen
        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                query = query.filter(func.date(models.Formulario.created_at) >= date_obj.date())
            except ValueError as e:
                print(f"Error de formato de fecha: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail="Formato de fecha inválido. Use YYYY-MM-DD"
                )
        
        if service:
            query = query.filter(models.Formulario.service == service)
        
        if search:
            search_filter = or_(
                models.Formulario.name.ilike(f"%{search}%"),
                models.Formulario.email.ilike(f"%{search}%"),
                models.Formulario.phone.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Ordenar por fecha descendente y ejecutar la consulta
        citas = query.order_by(models.Formulario.created_at.desc()).all()
        print(f"Número de citas recuperadas: {len(citas)}")  # Debug log
        
        # Obtener estadísticas de servicios
        service_stats_query = (
            db.query(
                models.Formulario.service,
                func.count(models.Formulario.id).label('count')
            )
            .filter(models.Formulario.service.isnot(None))
            .group_by(models.Formulario.service)
        )
        
        service_stats = {}
        for service, count in service_stats_query.all():
            if service:
                service_stats[service] = count
        
        print(f"Estadísticas de servicios: {service_stats}")  # Debug log
        
        # Obtener la fecha actual
        today = datetime.now().date()
        
        return templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "citas": citas,
                "today": today,
                "service_stats": service_stats
            }
        )
        
    except SQLAlchemyError as e:
        print(f"Error de base de datos en admin_panel: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al acceder a la base de datos"
        )
    except Exception as e:
        print(f"Error inesperado en admin_panel: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@app.post("/admin/update-status/{cita_id}")
async def update_status(
    cita_id: int,
    status_update: StatusUpdate,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_admin)
):
    try:
        cita = db.query(models.Formulario).filter(models.Formulario.id == cita_id).first()
        if not cita:
            raise HTTPException(status_code=404, detail="Cita no encontrada")
        
        # Validar el estado
        estados_validos = ["pendiente", "confirmada", "cancelada"]
        if status_update.status not in estados_validos:
            raise HTTPException(
                status_code=400,
                detail="Estado no válido. Los estados permitidos son: pendiente, confirmada, cancelada"
            )
        
        cita.status = status_update.status
        db.commit()
        
        return {"status": "success", "message": "Estado actualizado correctamente"}
    
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        print(f"Error de base de datos en update_status: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al actualizar el estado en la base de datos"
        )
    except Exception as e:
        print(f"Error inesperado en update_status: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@app.get("/admin/delete/{cita_id}")
async def delete_cita(
    cita_id: int,
    request: Request,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_admin)
):
    try:
        # Buscar y eliminar la cita
        cita = db.query(models.Formulario).filter(models.Formulario.id == cita_id).first()
        if cita:
            db.delete(cita)
            db.commit()
        
        return RedirectResponse(url="/admin", status_code=303)
    except Exception as e:
        print(f"Error en delete_cita: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar la cita"
        )

@app.post("/admin/edit-cita/{cita_id}")
async def edit_cita(
    cita_id: int,
    cita_update: CitaUpdate,
    db: Session = Depends(get_db),
    authenticated: bool = Depends(verify_admin)
):
    try:
        cita = db.query(models.Formulario).filter(models.Formulario.id == cita_id).first()
        if not cita:
            raise HTTPException(status_code=404, detail="Cita no encontrada")
        
        # Actualizar los campos
        cita.name = cita_update.name
        try:
            cita.created_at = datetime.strptime(cita_update.created_at, '%Y-%m-%dT%H:%M')
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha inválido")
        
        db.commit()
        return {"status": "success", "message": "Cita actualizada correctamente"}
    
    except HTTPException as he:
        raise he
    except SQLAlchemyError as e:
        print(f"Error de base de datos en edit_cita: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al actualizar la cita en la base de datos"
        )
    except Exception as e:
        print(f"Error inesperado en edit_cita: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 