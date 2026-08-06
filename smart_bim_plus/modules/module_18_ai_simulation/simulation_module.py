from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QSpinBox, QDoubleSpinBox, QTabWidget,
    QLabel, QPushButton, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import matplotlib.pyplot as plt

from modules.base_module import BaseModule
from modules.module_18_ai_simulation.thermal_sim import ThermalSimulator
from modules.module_18_ai_simulation.airflow_sim import AirflowSimulator
from modules.module_18_ai_simulation.cost_engine import CostEngine


class SimulationModule(BaseModule):
    """وحدة المحاكاة والذكاء الاصطناعي — النظام 18"""

    SYSTEM_NUMBER = 18
    SYSTEM_NAME = "AI Simulation"
    SYSTEM_NAME_AR = "المحاكاة والذكاء الاصطناعي"
    ICON_NAME = "simulation"

    def __init__(self, parent: Optional[QWidget] = None):
        self.thermal_sim = ThermalSimulator()
        self.airflow_sim = AirflowSimulator()
        self.cost_engine = CostEngine()
        self.figure = None
        self.canvas = None
        self.sim_data = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_progress)
        self.progress_val = 0
        super().__init__(parent)

    def setup_input_panel(self):
        """إعداد لوحة إدخال متغيرات المحاكاة"""
        env_group = QGroupBox("البيئة والمناخ")
        env_layout = QFormLayout(env_group)

        self.out_temp_spin = QDoubleSpinBox()
        self.out_temp_spin.setRange(-20, 60)
        self.out_temp_spin.setValue(45.0)
        self.out_temp_spin.setSuffix(" °C")
        env_layout.addRow("الحرارة الخارجية:", self.out_temp_spin)

        self.in_temp_spin = QDoubleSpinBox()
        self.in_temp_spin.setRange(16, 30)
        self.in_temp_spin.setValue(24.0)
        self.in_temp_spin.setSuffix(" °C")
        env_layout.addRow("الحرارة المستهدفة:", self.in_temp_spin)

        self.wind_speed_spin = QDoubleSpinBox()
        self.wind_speed_spin.setRange(0, 50)
        self.wind_speed_spin.setValue(5.0)
        self.wind_speed_spin.setSuffix(" m/s")
        env_layout.addRow("سرعة الرياح:", self.wind_speed_spin)

        self.wind_angle_spin = QDoubleSpinBox()
        self.wind_angle_spin.setRange(0, 360)
        self.wind_angle_spin.setValue(45.0)
        self.wind_angle_spin.setSuffix(" °")
        env_layout.addRow("اتجاه الرياح:", self.wind_angle_spin)

        self.input_layout.addWidget(env_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.input_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("جاهز لبدء المحاكاة")
        self.status_label.setObjectName("subtitleLabel")
        self.input_layout.addWidget(self.status_label)

    def setup_canvas(self):
        """إعداد لوحة رسم نتائج المحاكاة"""
        self.tabs = QTabWidget()
        self.canvas_layout.addWidget(self.tabs)

        self.thermal_tab = QWidget()
        self.thermal_layout = QVBoxLayout(self.thermal_tab)
        self.thermal_fig = Figure(figsize=(8, 6), facecolor="#0D1117")
        self.thermal_canvas = FigureCanvasQTAgg(self.thermal_fig)
        self.thermal_layout.addWidget(self.thermal_canvas)
        self.tabs.addTab(self.thermal_tab, "المحاكاة الحرارية")

        self.airflow_tab = QWidget()
        self.airflow_layout = QVBoxLayout(self.airflow_tab)
        self.airflow_fig = Figure(figsize=(8, 6), facecolor="#0D1117")
        self.airflow_canvas = FigureCanvasQTAgg(self.airflow_fig)
        self.airflow_layout.addWidget(self.airflow_canvas)
        self.tabs.addTab(self.airflow_tab, "تدفق الهواء")

        self.cost_tab = QWidget()
        self.cost_layout = QVBoxLayout(self.cost_tab)
        self.cost_fig = Figure(figsize=(8, 6), facecolor="#0D1117")
        self.cost_canvas = FigureCanvasQTAgg(self.cost_fig)
        self.cost_layout.addWidget(self.cost_canvas)
        self.tabs.addTab(self.cost_tab, "التكلفة والكميات")

    def generate(self):
        """بدء عملية المحاكاة"""
        rooms = self.building_data.get("rooms", [])
        if not rooms:
            rooms = [
                {"name": "غرفة", "position_x": 5, "position_y": 5, "width": 10, "length": 15}
            ]
            self.building_data["rooms"] = rooms
            self.building_data["plot_width"] = 20
            self.building_data["plot_length"] = 25

        self.thermal_sim.outdoor_temp = self.out_temp_spin.value()
        self.thermal_sim.indoor_target = self.in_temp_spin.value()
        self.airflow_sim.wind_speed = self.wind_speed_spin.value()
        self.airflow_sim.wind_angle = self.wind_angle_spin.value()

        self.generate_btn.setEnabled(False)
        self.progress_val = 0
        self.progress_bar.setValue(0)
        self.status_label.setText("جاري تشغيل محاكاة الطاقة والتكلفة...")
        self.timer.start(50)

    def _update_progress(self):
        self.progress_val += 5
        self.progress_bar.setValue(self.progress_val)
        
        if self.progress_val == 30:
            self.sim_data["thermal"] = self.thermal_sim.simulate(self.building_data)
            self._draw_thermal()
        elif self.progress_val == 60:
            self.sim_data["airflow"] = self.airflow_sim.simulate(self.building_data)
            self._draw_airflow()
        elif self.progress_val == 90:
            self.sim_data["cost"] = self.cost_engine.calculate_cost(self.building_data)
            self._draw_cost()
        elif self.progress_val >= 100:
            self.timer.stop()
            self.generate_btn.setEnabled(True)
            self.status_label.setText("اكتملت المحاكاة بنجاح")
            self.is_generated = True
            self.export_pdf_btn.setEnabled(True)
            self.generation_finished.emit(True)

    def _draw_thermal(self):
        self.thermal_fig.clear()
        ax = self.thermal_fig.add_subplot(111)
        ax.set_facecolor("#161B22")
        
        data = self.sim_data["thermal"]
        grid = data["temp_grid"]
        ext = data["grid_extent"]
        
        im = ax.imshow(grid, extent=ext, origin="lower", cmap="coolwarm", alpha=0.8)
        self.thermal_fig.colorbar(im, ax=ax, label="Temperature (°C)")
        
        for room in self.building_data.get("rooms", []):
            px, py = room.get("position_x", 0), room.get("position_y", 0)
            rw, rl = room.get("width", 4), room.get("length", 4)
            from matplotlib.patches import Rectangle
            ax.add_patch(Rectangle((px, py), rw, rl, fill=False, edgecolor="white", lw=1.5))
            
        ax.set_title(f"Thermal Map (Load: {data['total_cooling_load_ton']:.1f} Tons)", color="white")
        ax.tick_params(colors="white")
        self.thermal_fig.tight_layout()
        self.thermal_canvas.draw()

    def _draw_airflow(self):
        self.airflow_fig.clear()
        ax = self.airflow_fig.add_subplot(111)
        ax.set_facecolor("#161B22")
        
        data = self.sim_data["airflow"]
        X, Y, U, V, Speed = data["X"], data["Y"], data["U"], data["V"], data["Speed"]
        
        strm = ax.streamplot(X, Y, U, V, color=Speed, cmap="YlGnBu", linewidth=1.5, density=1.5)
        self.airflow_fig.colorbar(strm.lines, ax=ax, label="Wind Speed (m/s)")
        
        for room in self.building_data.get("rooms", []):
            px, py = room.get("position_x", 0), room.get("position_y", 0)
            rw, rl = room.get("width", 4), room.get("length", 4)
            from matplotlib.patches import Rectangle
            ax.add_patch(Rectangle((px, py), rw, rl, facecolor="#161B22", edgecolor="white", lw=1))
            
        ax.set_title(f"Airflow Simulation ({data['wind_speed']}m/s at {data['wind_angle']}°)", color="white")
        ax.tick_params(colors="white")
        self.airflow_fig.tight_layout()
        self.airflow_canvas.draw()

    def _draw_cost(self):
        self.cost_fig.clear()
        ax = self.cost_fig.add_subplot(111)
        ax.set_facecolor("#161B22")
        
        data = self.sim_data["cost"]
        breakdown = data["breakdown"]
        
        labels = list(breakdown.keys())
        values = list(breakdown.values())
        
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct='%1.1f%%',
            startangle=90, textprops=dict(color="white"),
            colors=plt.cm.Set3.colors
        )
        
        ax.set_title(f"Cost Breakdown (Total: ${data['total']:,.0f})", color="white")
        self.cost_fig.tight_layout()
        self.cost_canvas.draw()

    def export_dxf(self, filepath: str):
        pass

    def export_ifc(self, filepath: str):
        pass
