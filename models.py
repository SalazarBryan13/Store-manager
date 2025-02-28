from sqlalchemy import Column, Integer, String, DateTime, Text
from database import Base
from datetime import datetime

class Formulario(Base):
    __tablename__ = "formulario"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    service = Column(String(50), nullable=False)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(String(20), default="pendiente", nullable=False)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        if not self.status:
            self.status = "pendiente"
        
        if not self.created_at:
            self.created_at = datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "service": self.service,
            "message": self.message,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "status": self.status
        }

    class Config:
        orm_mode = True 