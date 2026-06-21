from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Object(Base):
    __tablename__ = 'objects'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    network = Column(String, nullable=True)
    address = Column(String, nullable=True)
    external_id = Column(String, nullable=True)

class WorkType(Base):
    __tablename__ = 'work_types'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    labor_cost_per_unit = Column(Float, default=0.0)

class Material(Base):
    __tablename__ = 'materials'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    default_price = Column(Float, default=0.0)

class Norm(Base):
    __tablename__ = 'norms'
    id = Column(Integer, primary_key=True)
    work_type_id = Column(Integer, ForeignKey('work_types.id'))
    material_id = Column(Integer, ForeignKey('materials.id'))
    quantity_per_unit = Column(Float, nullable=False)
    work_type = relationship('WorkType', backref='norms')
    material = relationship('Material', backref='norms')

class Task(Base):
# Добавить в класс Task
    profile_step = Column(Float, nullable=True)   # шаг профиля (мм)
    profile_type = Column(String, nullable=True)   # '50', '75', '100'
    has_door = Column(Boolean, default=False)      # наличие дверного проёма
    door_width = Column(Float, nullable=True)      # ширина двери (м)
    door_height = Column(Float, nullable=True)     # высота двери (м)

    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    object_id = Column(Integer, ForeignKey('objects.id'))
    work_type_id = Column(Integer, ForeignKey('work_types.id'))
    volume = Column(Float, nullable=False)
    labor_cost_override = Column(Float, nullable=True)
    all_purchased = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    profile_step = Column(Integer, nullable=True)
    profile_type = Column(String(10), nullable=True)   # 'CD' или 'UW'
    has_door = Column(Boolean, default=False)
    door_width = Column(Float, nullable=True)
    door_height = Column(Float, nullable=True)

class TaskMaterial(Base):
    __tablename__ = 'task_materials'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('tasks.id'))
    material_id = Column(Integer, ForeignKey('materials.id'))
    calculated_qty = Column(Float, nullable=False)
    final_qty = Column(Float, nullable=False)
    is_purchased = Column(Boolean, default=False)
    actual_cost = Column(Float, nullable=True)