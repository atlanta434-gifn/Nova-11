import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from sqlalchemy.pool import StaticPool

Base = declarative_base()


class Project(Base):
    """مشروع بناء رئيسي يحتوي على جميع بيانات التصميم"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    location = Column(String(500), default="")
    latitude = Column(Float, default=0.0)
    longitude = Column(Float, default=0.0)
    climate_zone = Column(String(100), default="")
    building_code = Column(String(100), default="IQS")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="draft")
    thumbnail_path = Column(String(500), default="")

    buildings = relationship("Building", back_populates="project", cascade="all, delete-orphan")
    exports = relationship("ExportHistory", back_populates="project", cascade="all, delete-orphan")


class Building(Base):
    """مبنى واحد ضمن المشروع مع أبعاده وخصائصه"""
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), default="Main Building")
    building_type = Column(String(100), nullable=False)
    style = Column(String(100), default="modern")
    total_floors = Column(Integer, default=1)
    basement_floors = Column(Integer, default=0)
    total_area = Column(Float, default=0.0)
    plot_width = Column(Float, default=0.0)
    plot_length = Column(Float, default=0.0)
    floor_height = Column(Float, default=3.0)
    orientation = Column(Float, default=0.0)
    structural_system = Column(String(100), default="concrete_frame")
    geometry_data = Column(JSON, default=dict)

    project = relationship("Project", back_populates="buildings")
    systems = relationship("SystemConfig", back_populates="building", cascade="all, delete-orphan")
    components = relationship("Component", back_populates="building", cascade="all, delete-orphan")
    rooms = relationship("Room", back_populates="building", cascade="all, delete-orphan")


class Room(Base):
    """غرفة واحدة ضمن المبنى"""
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    name = Column(String(255), nullable=False)
    room_type = Column(String(100), nullable=False)
    floor_number = Column(Integer, default=0)
    area = Column(Float, default=0.0)
    width = Column(Float, default=0.0)
    length = Column(Float, default=0.0)
    height = Column(Float, default=3.0)
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    has_window = Column(Boolean, default=True)
    has_balcony = Column(Boolean, default=False)
    window_area = Column(Float, default=0.0)
    properties = Column(JSON, default=dict)

    building = relationship("Building", back_populates="rooms")


class SystemConfig(Base):
    """إعدادات نظام واحد من أنظمة المبنى العشرين"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    system_number = Column(Integer, nullable=False)
    system_name = Column(String(255), nullable=False)
    is_enabled = Column(Boolean, default=True)
    parameters = Column(JSON, default=dict)
    status = Column(String(50), default="pending")
    last_generated = Column(DateTime, nullable=True)
    notes = Column(Text, default="")

    building = relationship("Building", back_populates="systems")


class Component(Base):
    """عنصر إنشائي أو ميكانيكي أو كهربائي"""
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    system_number = Column(Integer, nullable=False)
    component_type = Column(String(100), nullable=False)
    name = Column(String(255), default="")
    position_x = Column(Float, default=0.0)
    position_y = Column(Float, default=0.0)
    position_z = Column(Float, default=0.0)
    width = Column(Float, default=0.0)
    height = Column(Float, default=0.0)
    depth = Column(Float, default=0.0)
    rotation = Column(Float, default=0.0)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    properties = Column(JSON, default=dict)
    ifc_guid = Column(String(36), default="")

    building = relationship("Building", back_populates="components")
    material = relationship("Material")


class Material(Base):
    """مادة بناء مع خصائصها الفيزيائية"""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    name_ar = Column(String(255), default="")
    category = Column(String(100), default="general")
    unit = Column(String(50), default="m³")
    unit_cost = Column(Float, default=0.0)
    density = Column(Float, default=0.0)
    thermal_conductivity = Column(Float, default=0.0)
    specific_heat = Column(Float, default=0.0)
    fire_rating = Column(String(50), default="")
    color_hex = Column(String(7), default="#808080")
    properties = Column(JSON, default=dict)


class ExportHistory(Base):
    """سجل عمليات التصدير"""
    __tablename__ = "export_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    export_format = Column(String(20), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    system_number = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="completed")

    project = relationship("Project", back_populates="exports")


class DesignScore(Base):
    """تقييم التصميم وفق المعايير"""
    __tablename__ = "design_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=False)
    score_type = Column(String(100), nullable=False)
    score_value = Column(Float, default=0.0)
    max_value = Column(Float, default=100.0)
    details = Column(JSON, default=dict)
    evaluated_at = Column(DateTime, default=datetime.utcnow)


class DatabaseManager:
    """مدير قاعدة البيانات — يتولى جميع عمليات CRUD"""

    def __init__(self, db_path: str = "smart_bim.db"):
        if db_path == ":memory:":
            self.engine = create_engine(
                "sqlite:///:memory:",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
            self.engine = create_engine(
                f"sqlite:///{db_path}",
                connect_args={"check_same_thread": False},
            )
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self._seed_materials()

    def _seed_materials(self):
        session = self.SessionLocal()
        try:
            if session.query(Material).count() == 0:
                defaults = [
                    Material(name="Concrete C30", name_ar="خرسانة C30", category="structural",
                             unit="m³", unit_cost=120.0, density=2400.0,
                             thermal_conductivity=1.7, specific_heat=880.0, fire_rating="A1",
                             color_hex="#A0A0A0"),
                    Material(name="Steel Rebar", name_ar="حديد تسليح", category="structural",
                             unit="ton", unit_cost=800.0, density=7850.0,
                             thermal_conductivity=50.0, specific_heat=460.0, fire_rating="A1",
                             color_hex="#4A4A4A"),
                    Material(name="Clay Brick", name_ar="طابوق طيني", category="masonry",
                             unit="m³", unit_cost=45.0, density=1800.0,
                             thermal_conductivity=0.72, specific_heat=840.0, fire_rating="A1",
                             color_hex="#C87533"),
                    Material(name="Gypsum Board", name_ar="جبس بورد", category="finishing",
                             unit="m²", unit_cost=12.0, density=800.0,
                             thermal_conductivity=0.25, specific_heat=1000.0, fire_rating="A2",
                             color_hex="#F5F5DC"),
                    Material(name="Glass 6mm", name_ar="زجاج 6مم", category="glazing",
                             unit="m²", unit_cost=35.0, density=2500.0,
                             thermal_conductivity=1.0, specific_heat=840.0, fire_rating="A1",
                             color_hex="#ADD8E6"),
                    Material(name="Thermal Insulation XPS", name_ar="عزل حراري XPS", category="insulation",
                             unit="m²", unit_cost=18.0, density=35.0,
                             thermal_conductivity=0.034, specific_heat=1500.0, fire_rating="B2",
                             color_hex="#FFB6C1"),
                    Material(name="PVC Pipe", name_ar="أنابيب PVC", category="plumbing",
                             unit="m", unit_cost=8.0, density=1400.0,
                             thermal_conductivity=0.16, specific_heat=900.0, fire_rating="B1",
                             color_hex="#FFFFFF"),
                    Material(name="Copper Wire", name_ar="سلك نحاسي", category="electrical",
                             unit="m", unit_cost=5.0, density=8960.0,
                             thermal_conductivity=385.0, specific_heat=385.0, fire_rating="A1",
                             color_hex="#B87333"),
                    Material(name="Ceramic Tile", name_ar="بلاط سيراميك", category="finishing",
                             unit="m²", unit_cost=25.0, density=2000.0,
                             thermal_conductivity=1.3, specific_heat=800.0, fire_rating="A1",
                             color_hex="#DEB887"),
                    Material(name="Aluminum Frame", name_ar="إطار ألمنيوم", category="glazing",
                             unit="m", unit_cost=40.0, density=2700.0,
                             thermal_conductivity=205.0, specific_heat=900.0, fire_rating="A1",
                             color_hex="#C0C0C0"),
                ]
                session.add_all(defaults)
                session.commit()
        finally:
            session.close()

    def get_session(self) -> Session:
        return self.SessionLocal()

    def create_project(self, name: str, location: str = "",
                       building_code: str = "IQS", **kwargs) -> Project:
        """إنشاء مشروع جديد وإرجاعه"""
        session = self.SessionLocal()
        try:
            project = Project(name=name, location=location,
                              building_code=building_code, **kwargs)
            session.add(project)
            session.commit()
            session.refresh(project)
            return project
        finally:
            session.close()

    def get_project(self, project_id: int) -> Optional[Project]:
        session = self.SessionLocal()
        try:
            return session.query(Project).filter(Project.id == project_id).first()
        finally:
            session.close()

    def get_all_projects(self) -> List[Project]:
        session = self.SessionLocal()
        try:
            return session.query(Project).order_by(Project.updated_at.desc()).all()
        finally:
            session.close()

    def update_project(self, project_id: int, **kwargs) -> Optional[Project]:
        session = self.SessionLocal()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                for key, value in kwargs.items():
                    if hasattr(project, key):
                        setattr(project, key, value)
                project.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(project)
            return project
        finally:
            session.close()

    def delete_project(self, project_id: int) -> bool:
        session = self.SessionLocal()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                session.delete(project)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def add_building(self, project_id: int, building_type: str,
                     name: str = "المبنى الرئيسي", **kwargs) -> Building:
        """إضافة مبنى جديد للمشروع"""
        session = self.SessionLocal()
        try:
            building = Building(
                project_id=project_id,
                building_type=building_type,
                name=name,
                **kwargs
            )
            session.add(building)
            session.commit()
            session.refresh(building)
            return building
        finally:
            session.close()

    def get_building(self, building_id: int) -> Optional[Building]:
        session = self.SessionLocal()
        try:
            return session.query(Building).filter(Building.id == building_id).first()
        finally:
            session.close()

    def get_buildings_for_project(self, project_id: int) -> List[Building]:
        session = self.SessionLocal()
        try:
            return session.query(Building).filter(Building.project_id == project_id).all()
        finally:
            session.close()

    def update_building(self, building_id: int, **kwargs) -> Optional[Building]:
        session = self.SessionLocal()
        try:
            building = session.query(Building).filter(Building.id == building_id).first()
            if building:
                for key, value in kwargs.items():
                    if hasattr(building, key):
                        setattr(building, key, value)
                session.commit()
                session.refresh(building)
            return building
        finally:
            session.close()

    def add_room(self, building_id: int, name: str, room_type: str, **kwargs) -> Room:
        """إضافة غرفة جديدة للمبنى"""
        session = self.SessionLocal()
        try:
            room = Room(building_id=building_id, name=name,
                        room_type=room_type, **kwargs)
            session.add(room)
            session.commit()
            session.refresh(room)
            return room
        finally:
            session.close()

    def get_rooms_for_building(self, building_id: int) -> List[Room]:
        session = self.SessionLocal()
        try:
            return session.query(Room).filter(Room.building_id == building_id).all()
        finally:
            session.close()

    def add_system_config(self, building_id: int, system_number: int,
                          system_name: str, **kwargs) -> SystemConfig:
        """إضافة إعدادات نظام للمبنى"""
        session = self.SessionLocal()
        try:
            config = SystemConfig(
                building_id=building_id,
                system_number=system_number,
                system_name=system_name,
                **kwargs
            )
            session.add(config)
            session.commit()
            session.refresh(config)
            return config
        finally:
            session.close()

    def get_system_configs(self, building_id: int) -> List[SystemConfig]:
        session = self.SessionLocal()
        try:
            return session.query(SystemConfig).filter(
                SystemConfig.building_id == building_id
            ).order_by(SystemConfig.system_number).all()
        finally:
            session.close()

    def add_component(self, building_id: int, system_number: int,
                      component_type: str, **kwargs) -> Component:
        """إضافة عنصر جديد"""
        session = self.SessionLocal()
        try:
            comp = Component(
                building_id=building_id,
                system_number=system_number,
                component_type=component_type,
                **kwargs
            )
            session.add(comp)
            session.commit()
            session.refresh(comp)
            return comp
        finally:
            session.close()

    def get_components(self, building_id: int,
                       system_number: Optional[int] = None) -> List[Component]:
        session = self.SessionLocal()
        try:
            query = session.query(Component).filter(
                Component.building_id == building_id
            )
            if system_number is not None:
                query = query.filter(Component.system_number == system_number)
            return query.all()
        finally:
            session.close()

    def get_all_materials(self) -> List[Material]:
        session = self.SessionLocal()
        try:
            return session.query(Material).order_by(Material.category).all()
        finally:
            session.close()

    def get_materials_by_category(self, category: str) -> List[Material]:
        session = self.SessionLocal()
        try:
            return session.query(Material).filter(
                Material.category == category
            ).all()
        finally:
            session.close()

    def add_material(self, name: str, category: str, **kwargs) -> Material:
        session = self.SessionLocal()
        try:
            mat = Material(name=name, category=category, **kwargs)
            session.add(mat)
            session.commit()
            session.refresh(mat)
            return mat
        finally:
            session.close()

    def log_export(self, project_id: int, export_format: str,
                   file_path: str, **kwargs) -> ExportHistory:
        """تسجيل عملية تصدير"""
        session = self.SessionLocal()
        try:
            file_size = 0
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
            export = ExportHistory(
                project_id=project_id,
                export_format=export_format,
                file_path=file_path,
                file_size=file_size,
                **kwargs
            )
            session.add(export)
            session.commit()
            session.refresh(export)
            return export
        finally:
            session.close()

    def get_export_history(self, project_id: int) -> List[ExportHistory]:
        session = self.SessionLocal()
        try:
            return session.query(ExportHistory).filter(
                ExportHistory.project_id == project_id
            ).order_by(ExportHistory.created_at.desc()).all()
        finally:
            session.close()

    def save_design_score(self, building_id: int, score_type: str,
                          score_value: float, max_value: float = 100.0,
                          details: Optional[Dict] = None) -> DesignScore:
        """حفظ تقييم التصميم"""
        session = self.SessionLocal()
        try:
            score = DesignScore(
                building_id=building_id,
                score_type=score_type,
                score_value=score_value,
                max_value=max_value,
                details=details or {},
            )
            session.add(score)
            session.commit()
            session.refresh(score)
            return score
        finally:
            session.close()

    def get_design_scores(self, building_id: int) -> List[DesignScore]:
        session = self.SessionLocal()
        try:
            return session.query(DesignScore).filter(
                DesignScore.building_id == building_id
            ).order_by(DesignScore.evaluated_at.desc()).all()
        finally:
            session.close()

    def get_project_statistics(self, project_id: int) -> Dict[str, Any]:
        """إحصائيات المشروع الشاملة"""
        session = self.SessionLocal()
        try:
            buildings = session.query(Building).filter(
                Building.project_id == project_id
            ).all()
            total_area = sum(b.total_area for b in buildings)
            total_floors = sum(b.total_floors for b in buildings)
            total_components = session.query(Component).filter(
                Component.building_id.in_([b.id for b in buildings])
            ).count() if buildings else 0
            total_exports = session.query(ExportHistory).filter(
                ExportHistory.project_id == project_id
            ).count()
            return {
                "buildings_count": len(buildings),
                "total_area": total_area,
                "total_floors": total_floors,
                "total_components": total_components,
                "total_exports": total_exports,
            }
        finally:
            session.close()
