import numpy as np
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, 
    QComboBox, QSpinBox, QSlider, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from modules.base_module import BaseModule
from .lighting_engine import LightingEngine

class LightingModule(BaseModule):
    """وحدة الإضاءة الطبيعية والصناعية"""
    
    SYSTEM_NUMBER = 3
    SYSTEM_NAME = "Lighting System"
    SYSTEM_NAME_AR = "الإضاءة الطبيعية والصناعية"
    ICON_NAME = "sun"
    
    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        group_box = QGroupBox("إعدادات الموقع والوقت")
        layout = QFormLayout()
        
        self.lat_input = QDoubleSpinBox()
        self.lat_input.setRange(-90.0, 90.0)
        self.lat_input.setValue(24.7136)
        layout.addRow("خط العرض:", self.lat_input)
        
        self.lon_input = QDoubleSpinBox()
        self.lon_input.setRange(-180.0, 180.0)
        self.lon_input.setValue(46.6753)
        layout.addRow("خط الطول:", self.lon_input)
        
        self.month_input = QSpinBox()
        self.month_input.setRange(1, 12)
        self.month_input.setValue(6)
        layout.addRow("الشهر:", self.month_input)
        
        self.day_input = QSpinBox()
        self.day_input.setRange(1, 31)
        self.day_input.setValue(21)
        layout.addRow("اليوم:", self.day_input)
        
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setRange(6, 18)
        self.time_slider.setValue(12)
        self.time_label = QLabel("12:00")
        self.time_slider.valueChanged.connect(lambda v: self.time_label.setText(f"{v}:00"))
        
        time_layout = QHBoxLayout()
        time_layout.addWidget(self.time_slider)
        time_layout.addWidget(self.time_label)
        layout.addRow("الوقت:", time_layout)
        
        self.sky_combo = QComboBox()
        self.sky_combo.addItems(["clear", "partly cloudy", "overcast"])
        self.sky_combo.setItemText(0, "صافي")
        self.sky_combo.setItemText(1, "غائم جزئياً")
        self.sky_combo.setItemText(2, "غائم")
        layout.addRow("حالة السماء:", self.sky_combo)
        
        group_box.setLayout(layout)
        self.input_layout.insertWidget(1, group_box)
        
    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure = Figure(facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.canvas_layout.addWidget(self.canvas)
        
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#161B22")
        self.ax.tick_params(colors="#C9D1D9")
        for spine in self.ax.spines.values():
            spine.set_color("#C9D1D9")
            
    def generate(self):
        """توليد بيانات النظام"""
        lat = self.lat_input.value()
        lon = self.lon_input.value()
        month = self.month_input.value()
        day = self.day_input.value()
        hour = float(self.time_slider.value())
        sky_cond = ["clear", "partly cloudy", "overcast"][self.sky_combo.currentIndex()]
        
        engine = LightingEngine(lat, lon)
        self.generated_data = engine.run_analysis(self.building_data, month, day, hour, sky_cond)
        
        self._update_plot()
        
    def _update_plot(self):
        """تحديث الرسم البياني"""
        self.ax.clear()
        
        if not self.generated_data:
            self.canvas.draw()
            return
            
        sun_pos = self.generated_data.get("sun_position", {})
        az = sun_pos.get("azimuth", 0)
        alt = sun_pos.get("altitude", 0)
        
        self.ax.set_title(f"تحليل الإضاءة - السمت: {az:.1f}° | الارتفاع: {alt:.1f}°", color="#C9D1D9")
        
        rooms = self.generated_data.get("rooms", [])
        for room_data in rooms:
            room = room_data["room_data"]
            x = room.get("position_x", 0)
            y = room.get("position_y", 0)
            w = room.get("width", 5)
            h = room.get("length", 5)
            
            grid = room_data.get("illuminance_grid", np.array([]))
            avg_lux = 0
            if grid.size > 0:
                avg_lux = np.mean(grid)
                
            if avg_lux > 500:
                color = "#58A6FF"
            elif avg_lux >= 300:
                color = "#3FB950"
            else:
                color = "#F85149"
                
            rect = Rectangle((x, y), w, h, facecolor=color, alpha=0.5, edgecolor="#C9D1D9")
            self.ax.add_patch(rect)
            
            self.ax.text(x + w/2, y + h/2, f"{room.get('name', 'Room')}\n{avg_lux:.0f} lx", 
                         color="#C9D1D9", ha="center", va="center")
            
        self.ax.autoscale()
        self.ax.set_aspect('equal')
        self.canvas.draw()
        
    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        pass
        
    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        pass
