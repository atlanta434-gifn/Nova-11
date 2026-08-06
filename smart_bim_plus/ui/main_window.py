import os
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QDockWidget, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QFrame, QSplitter, QTabWidget,
    QTextEdit, QProgressBar, QMessageBox, QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from core.database import DatabaseManager
from core.ai_engine import AIEngine
from core.drone_handler import DroneHandler, DroneStatus

from ui.dashboard import Dashboard
from modules.module_01_plans.plans_module import PlansModule
from modules.module_02_ventilation.ventilation_module import VentilationModule
from modules.module_03_lighting.lighting_module import LightingModule
from modules.module_04_electricity.electricity_module import ElectricityModule
from modules.module_05_plumbing.plumbing_module import PlumbingModule
from modules.module_06_hvac.hvac_module import HVACModule
from modules.module_07_gas.gas_module import GasModule
from modules.module_08_fire.fire_module import FireSafetyModule
from modules.module_09_networks.network_module import NetworkModule
from modules.module_10_interior.interior_module import InteriorModule
from modules.module_11_garden.garden_module import GardenModule
from modules.module_12_pool.pool_module import PoolModule
from modules.module_13_structural.structural_module import StructuralModule
from modules.module_14_security.security_module import SecurityModule
from modules.module_15_energy.energy_module import EnergyModule
from modules.module_16_waste.waste_module import WasteModule
from modules.module_17_acoustics.acoustics_module import AcousticsModule
from modules.module_18_ai_simulation.simulation_module import SimulationModule
from modules.module_19_project_mgmt.project_module import ProjectManagementModule
from modules.module_20_gis.gis_module import GISModule


class SmartBIMMainWindow(QMainWindow):
    """النافذة الرئيسية لتطبيق NOVA"""

    MODULES_INFO = [
        ("01", "المخططات المعمارية", PlansModule),
        ("02", "التهوية الطبيعية", VentilationModule),
        ("03", "الإضاءة الطبيعية", LightingModule),
        ("04", "الكهرباء والطاقة", ElectricityModule),
        ("05", "السباكة والمياه", PlumbingModule),
        ("06", "التكييف والتدفئة (HVAC)", HVACModule),
        ("07", "الغاز", GasModule),
        ("08", "الحريق والسلامة", FireSafetyModule),
        ("09", "الشبكات والاتصالات", NetworkModule),
        ("10", "التصميم الداخلي", InteriorModule),
        ("11", "الحديقة الذكية", GardenModule),
        ("12", "المسبح الذكي", PoolModule),
        ("13", "التحليل الإنشائي", StructuralModule),
        ("14", "نظام الأمان", SecurityModule),
        ("15", "إدارة الطاقة", EnergyModule),
        ("16", "إدارة النفايات", WasteModule),
        ("17", "الصوتيات والترفيه", AcousticsModule),
        ("18", "المحاكاة والذكاء الاصطناعي", SimulationModule),
        ("19", "إدارة المشاريع", ProjectManagementModule),
        ("20", "الخرائط الجغرافية", GISModule),
    ]

    def __init__(self, db_manager: DatabaseManager, ai_engine: AIEngine,
                 drone_handler: DroneHandler):
        super().__init__()
        self.db = db_manager
        self.ai = ai_engine
        self.drone = drone_handler
        self.current_project = None
        self.modules = {}

        self.setWindowTitle("NOVA — DSBA System")
        self.setMinimumSize(1280, 800)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._setup_ui()
        self._setup_connections()

        self.ai_status_indicator.setStyleSheet("background-color: #3FB950;" if self.ai.is_onnx_available else "background-color: #D29922;")

    def _setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self._setup_top_bar()

        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.content_splitter, 1)

        self._setup_sidebar()

        self.stack = QStackedWidget()
        self.content_splitter.addWidget(self.stack)

        self.dashboard = Dashboard()
        self.dashboard.new_project_cb = self._on_new_project
        self.dashboard.drone_connect_cb = self._on_drone_connect
        self.stack.addWidget(self.dashboard)

        self._init_modules()

        self.content_splitter.setSizes([250, 1030])

        self._setup_bottom_panel()

    def _setup_top_bar(self):
        self.top_bar = QFrame()
        self.top_bar.setObjectName("topBar")
        self.top_bar.setFixedHeight(60)
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)

        self.project_label = QLabel("لم يتم تحديد مشروع")
        self.project_label.setObjectName("titleLabel")
        top_layout.addWidget(self.project_label)

        top_layout.addStretch()

        ai_layout = QHBoxLayout()
        self.ai_status_indicator = QFrame()
        self.ai_status_indicator.setObjectName("statusIndicator")
        ai_layout.addWidget(self.ai_status_indicator)
        ai_label = QLabel("AI Engine")
        ai_label.setObjectName("subtitleLabel")
        ai_layout.addWidget(ai_label)
        top_layout.addLayout(ai_layout)

        top_layout.addSpacing(20)

        drone_layout = QHBoxLayout()
        self.drone_status_indicator = QFrame()
        self.drone_status_indicator.setObjectName("statusOffline")
        drone_layout.addWidget(self.drone_status_indicator)
        drone_label = QLabel("Drone Status")
        drone_label.setObjectName("subtitleLabel")
        drone_layout.addWidget(drone_label)
        top_layout.addLayout(drone_layout)

        self.main_layout.addWidget(self.top_bar)

    def _setup_sidebar(self):
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("sidebarFrame")
        self.sidebar_widget.setMinimumWidth(250)
        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
        self.sidebar_layout.setContentsMargins(10, 20, 10, 20)
        self.sidebar_layout.setSpacing(5)

        dash_btn = QPushButton("لوحة القيادة")
        dash_btn.setObjectName("sidebarButton")
        dash_btn.setCheckable(True)
        dash_btn.setChecked(True)
        dash_btn.clicked.connect(lambda: self._switch_module("dashboard", dash_btn))
        self.sidebar_layout.addWidget(dash_btn)
        self.nav_buttons = [dash_btn]

        line = QFrame()
        line.setObjectName("separator")
        self.sidebar_layout.addWidget(line)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(2)

        for num, name, mod_class in self.MODULES_INFO:
            btn = QPushButton(f"{num} - {name}")
            btn.setObjectName("sidebarButton")
            btn.setCheckable(True)
            if mod_class is None:
                btn.setEnabled(False)
                btn.setText(btn.text() + " (قريباً)")
            else:
                btn.clicked.connect(lambda checked, n=num, b=btn: self._switch_module(n, b))
            
            scroll_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        self.sidebar_layout.addWidget(scroll)

        self.content_splitter.addWidget(self.sidebar_widget)

    def _init_modules(self):
        for num, name, mod_class in self.MODULES_INFO:
            if mod_class:
                mod = mod_class()
                mod.log_message.connect(self.log_msg)
                mod.data_generated.connect(self._on_module_data_generated)
                self.modules[num] = mod
                self.stack.addWidget(mod)

    def _on_module_data_generated(self, module_id: str, data: dict):
        self.log_msg(f"تم استلام بيانات جديدة من القسم {module_id}، جاري تعميمها...")
        for num, mod in self.modules.items():
            if num != module_id:
                mod.set_building_data(data)

    def _setup_bottom_panel(self):
        self.bottom_panel = QDockWidget("السجلات والعمليات", self)
        self.bottom_panel.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea)
        self.bottom_panel.setFixedHeight(200)

        panel_widget = QWidget()
        panel_layout = QVBoxLayout(panel_widget)
        panel_layout.setContentsMargins(0, 0, 0, 0)

        self.bottom_tabs = QTabWidget()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.bottom_tabs.addTab(self.log_text, "السجلات (Logs)")

        self.progress_tab = QWidget()
        prog_layout = QVBoxLayout(self.progress_tab)
        self.global_progress = QProgressBar()
        prog_layout.addWidget(self.global_progress)
        prog_layout.addStretch()
        self.bottom_tabs.addTab(self.progress_tab, "العمليات")

        panel_layout.addWidget(self.bottom_tabs)
        self.bottom_panel.setWidget(panel_widget)
        
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.bottom_panel)

    def _setup_connections(self):
        self.drone.on_status_change(self._on_drone_status_change)
        self.drone.on_frame(self._on_drone_frame)

    def _switch_module(self, module_id: str, active_btn: QPushButton):
        for btn in self.nav_buttons:
            if btn != active_btn:
                btn.setChecked(False)
        active_btn.setChecked(True)

        if module_id == "dashboard":
            self.stack.setCurrentWidget(self.dashboard)
        elif module_id in self.modules:
            mod = self.modules[module_id]
            if self.current_project:
                bldg = self.db.get_buildings_for_project(self.current_project.id)
                if bldg:
                    rooms = self.db.get_rooms_for_building(bldg[0].id)
                    rooms_data = []
                    for r in rooms:
                        rooms_data.append({
                            "name": r.name,
                            "room_type": r.room_type,
                            "area": r.area,
                            "width": r.width,
                            "length": r.length,
                            "position_x": r.position_x,
                            "position_y": r.position_y,
                            "has_window": r.has_window
                        })
                    mod.set_building_data({
                        "project_id": self.current_project.id,
                        "building_id": bldg[0].id,
                        "plot_width": bldg[0].plot_width,
                        "plot_length": bldg[0].plot_length,
                        "total_floors": bldg[0].total_floors,
                        "building_type": bldg[0].building_type,
                        "rooms": rooms_data
                    })
            self.stack.setCurrentWidget(mod)

    def _on_new_project(self):
        try:
            proj = self.db.create_project("مشروع جديد " + str(len(self.db.get_all_projects()) + 1))
            self.db.add_building(proj.id, "residential", plot_width=20.0, plot_length=25.0)
            self.current_project = proj
            self.project_label.setText(f"المشروع الحالي: {proj.name}")
            self.log_msg(f"تم إنشاء مشروع جديد: {proj.name}")
            
            for btn in self.nav_buttons:
                if btn.text().startswith("01"):
                    btn.click()
                    break
        except Exception as e:
            self.log_msg(f"خطأ في إنشاء المشروع: {e}")

    def _on_drone_connect(self):
        if self.drone.status == DroneStatus.DISCONNECTED:
            self.drone.connect()
        else:
            self.drone.disconnect()

    def _on_drone_status_change(self, status: DroneStatus):
        colors = {
            DroneStatus.DISCONNECTED: "statusOffline",
            DroneStatus.CONNECTING: "statusProcessing",
            DroneStatus.CONNECTED: "statusOnline",
            DroneStatus.ERROR: "statusOffline"
        }
        self.drone_status_indicator.setObjectName(colors.get(status, "statusOffline"))
        self.drone_status_indicator.style().unpolish(self.drone_status_indicator)
        self.drone_status_indicator.style().polish(self.drone_status_indicator)
        self.log_msg(f"Drone status changed to: {status.value}")

    def _on_drone_frame(self, frame):
        pass

    def log_msg(self, message: str):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
