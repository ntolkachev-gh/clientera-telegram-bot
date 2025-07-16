from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class Client(Base):
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    # Preferences
    favorite_services = Column(JSONB, default=list)
    favorite_masters = Column(JSONB, default=list)
    preferred_time_slots = Column(JSONB, default=list)
    custom_notes = Column(JSONB, default=dict)
    
    # Visit tracking
    last_visit_date = Column(DateTime, nullable=True)
    remind_after_days = Column(Integer, default=21)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="client")
    sessions = relationship("Session", back_populates="client")


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    session_start = Column(DateTime, default=datetime.utcnow)
    session_end = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    client = relationship("Client", back_populates="sessions")
    messages = relationship("Message", back_populates="session")


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    
    # Message content
    message_type = Column(String, nullable=False)  # 'user' or 'bot'
    content = Column(Text, nullable=False)
    telegram_message_id = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    client = relationship("Client", back_populates="messages")
    session = relationship("Session", back_populates="messages")


class OpenAIUsageLog(Base):
    __tablename__ = "openai_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    
    # Usage details
    model = Column(String, nullable=False)
    purpose = Column(String, nullable=False)  # 'chat', 'embedding', 'fact_extraction'
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Cost calculation
    cost_usd = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    client = relationship("Client")


class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # Appointment details
    youclients_id = Column(String, unique=True, nullable=True)
    service_name = Column(String, nullable=False)
    master_name = Column(String, nullable=False)
    appointment_datetime = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    
    # Status
    status = Column(String, default="scheduled")  # scheduled, completed, cancelled
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = relationship("Client") 