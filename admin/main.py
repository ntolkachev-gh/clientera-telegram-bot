from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import List, Dict, Any
import secrets

from database.database import get_db
from database.models import Client, Message, OpenAIUsageLog, Appointment, Session as ChatSession
from config import settings

app = FastAPI(title="Clientera Admin", description="Админка для управления клиентами салона красоты")

# Настройка шаблонов
templates = Jinja2Templates(directory="admin/templates")

# Простая HTTP Basic аутентификация
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Проверка аутентификации"""
    correct_username = secrets.compare_digest(credentials.username, settings.admin_username)
    correct_password = secrets.compare_digest(credentials.password, settings.admin_password)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Неверные учетные данные",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db), 
                   current_user: str = Depends(get_current_user)):
    """Главная страница админки"""
    
    # Статистика клиентов
    total_clients = db.query(Client).count()
    active_clients = db.query(Client).filter(
        Client.created_at >= datetime.now() - timedelta(days=30)
    ).count()
    
    # Статистика сообщений
    total_messages = db.query(Message).count()
    messages_today = db.query(Message).filter(
        Message.created_at >= datetime.now().date()
    ).count()
    
    # Статистика OpenAI
    total_cost = db.query(func.sum(OpenAIUsageLog.cost_usd)).scalar() or 0
    cost_today = db.query(func.sum(OpenAIUsageLog.cost_usd)).filter(
        OpenAIUsageLog.created_at >= datetime.now().date()
    ).scalar() or 0
    
    # Активные сессии
    active_sessions = db.query(ChatSession).filter(
        ChatSession.is_active == True
    ).count()
    
    # Записи на сегодня
    appointments_today = db.query(Appointment).filter(
        Appointment.appointment_datetime >= datetime.now().date(),
        Appointment.appointment_datetime < datetime.now().date() + timedelta(days=1)
    ).count()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_clients": total_clients,
        "active_clients": active_clients,
        "total_messages": total_messages,
        "messages_today": messages_today,
        "total_cost": round(total_cost, 2),
        "cost_today": round(cost_today, 2),
        "active_sessions": active_sessions,
        "appointments_today": appointments_today
    })


@app.get("/clients", response_class=HTMLResponse)
async def clients_list(request: Request, db: Session = Depends(get_db),
                      current_user: str = Depends(get_current_user)):
    """Список клиентов"""
    
    clients = db.query(Client).order_by(desc(Client.created_at)).all()
    
    # Добавляем статистику для каждого клиента
    clients_with_stats = []
    for client in clients:
        messages_count = db.query(Message).filter(Message.client_id == client.id).count()
        sessions_count = db.query(ChatSession).filter(ChatSession.client_id == client.id).count()
        
        clients_with_stats.append({
            "client": client,
            "messages_count": messages_count,
            "sessions_count": sessions_count
        })
    
    return templates.TemplateResponse("clients.html", {
        "request": request,
        "clients": clients
    })


@app.get("/clients/{client_id}", response_class=HTMLResponse)
async def client_detail(request: Request, client_id: int, db: Session = Depends(get_db),
                       current_user: str = Depends(get_current_user)):
    """Детальная информация о клиенте"""
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Получаем сессии клиента
    sessions = db.query(ChatSession).filter(
        ChatSession.client_id == client_id
    ).order_by(desc(ChatSession.session_start)).all()
    
    # Получаем записи клиента
    appointments = db.query(Appointment).filter(
        Appointment.client_id == client_id
    ).order_by(desc(Appointment.appointment_datetime)).all()
    
    return templates.TemplateResponse("client_detail.html", {
        "request": request,
        "client": client,
        "sessions": sessions,
        "appointments": appointments
    })


@app.get("/sessions/{session_id}", response_class=HTMLResponse)
async def session_detail(request: Request, session_id: int, db: Session = Depends(get_db),
                        current_user: str = Depends(get_current_user)):
    """Детальная информация о сессии"""
    
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Сессия не найдена")
    
    # Получаем сообщения сессии
    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at).all()
    
    return templates.TemplateResponse("session_detail.html", {
        "request": request,
        "session": session,
        "messages": messages
    })


@app.get("/usage", response_class=HTMLResponse)
async def usage_stats(request: Request, db: Session = Depends(get_db),
                     current_user: str = Depends(get_current_user)):
    """Статистика использования OpenAI"""
    
    # Общая статистика
    total_usage = db.query(OpenAIUsageLog).count()
    total_cost = db.query(func.sum(OpenAIUsageLog.cost_usd)).scalar() or 0
    total_tokens = db.query(func.sum(OpenAIUsageLog.total_tokens)).scalar() or 0
    
    # Статистика по моделям
    model_stats = db.query(
        OpenAIUsageLog.model,
        func.count(OpenAIUsageLog.id).label('count'),
        func.sum(OpenAIUsageLog.cost_usd).label('total_cost'),
        func.sum(OpenAIUsageLog.total_tokens).label('total_tokens')
    ).group_by(OpenAIUsageLog.model).all()
    
    # Статистика по назначению
    purpose_stats = db.query(
        OpenAIUsageLog.purpose,
        func.count(OpenAIUsageLog.id).label('count'),
        func.sum(OpenAIUsageLog.cost_usd).label('total_cost'),
        func.sum(OpenAIUsageLog.total_tokens).label('total_tokens')
    ).group_by(OpenAIUsageLog.purpose).all()
    
    # Последние запросы
    recent_usage = db.query(OpenAIUsageLog).order_by(
        desc(OpenAIUsageLog.created_at)
    ).limit(50).all()
    
    return templates.TemplateResponse("usage.html", {
        "request": request,
        "total_usage": total_usage,
        "total_cost": round(total_cost, 2),
        "total_tokens": total_tokens,
        "model_stats": model_stats,
        "purpose_stats": purpose_stats,
        "recent_usage": recent_usage
    })


@app.get("/appointments", response_class=HTMLResponse)
async def appointments_list(request: Request, db: Session = Depends(get_db),
                           current_user: str = Depends(get_current_user)):
    """Список записей"""
    
    appointments = db.query(Appointment).order_by(
        desc(Appointment.appointment_datetime)
    ).limit(100).all()
    
    return templates.TemplateResponse("appointments.html", {
        "request": request,
        "appointments": appointments
    })


@app.post("/clients/{client_id}/update")
async def update_client(client_id: int, 
                       remind_after_days: int = Form(...),
                       db: Session = Depends(get_db),
                       current_user: str = Depends(get_current_user)):
    """Обновление настроек клиента"""
    
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    client.remind_after_days = remind_after_days
    client.updated_at = datetime.utcnow()
    db.commit()
    
    return RedirectResponse(url=f"/clients/{client_id}", status_code=303)


@app.get("/analytics", response_class=HTMLResponse)
async def analytics(request: Request, db: Session = Depends(get_db),
                   current_user: str = Depends(get_current_user)):
    """Аналитика и графики"""
    
    # Активность по дням (последние 30 дней)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    daily_messages = db.query(
        func.date(Message.created_at).label('date'),
        func.count(Message.id).label('count')
    ).filter(
        Message.created_at >= thirty_days_ago
    ).group_by(func.date(Message.created_at)).all()
    
    # Новые клиенты по дням
    daily_clients = db.query(
        func.date(Client.created_at).label('date'),
        func.count(Client.id).label('count')
    ).filter(
        Client.created_at >= thirty_days_ago
    ).group_by(func.date(Client.created_at)).all()
    
    # Топ активных клиентов
    top_clients = db.query(
        Client,
        func.count(Message.id).label('message_count')
    ).join(Message).group_by(Client.id).order_by(
        desc(func.count(Message.id))
    ).limit(10).all()
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "daily_messages": daily_messages,
        "daily_clients": daily_clients,
        "top_clients": top_clients
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 