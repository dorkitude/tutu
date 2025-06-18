from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from pathlib import Path

Base = declarative_base()

class TutuItem(Base):
    __tablename__ = 'tutu_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='pending')
    context = Column(Text)
    first_progress_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    steps = relationship("TutuItemStep", back_populates="item", cascade="all, delete-orphan")

class TutuItemStep(Base):
    __tablename__ = 'tutu_item_steps'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey('tutu_items.id'), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    item = relationship("TutuItem", back_populates="steps")

def get_db_path():
    db_path = Path.home() / "a" / "base" / "tutu.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)

def get_engine():
    db_path = get_db_path()
    return create_engine(f'sqlite:///{db_path}')

def get_session():
    engine = get_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()