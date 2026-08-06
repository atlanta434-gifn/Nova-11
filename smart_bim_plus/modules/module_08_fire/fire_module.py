import os
import numpy as np
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                            QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches

from modules.base_module import BaseModule
from .fire_engine import FireSafetyEngine

class FireSafetyModule(BaseModule):
    """وحدة الإطفاء والسلامة"""
    
    SYSTEM_NUMBER = 8
    SYSTEM_NAME = "Fire and Safety"
    SYSTEM_NAME_AR = "الإطفاء والسلامة"
    ICON_NAME = "fire"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        self.hazard_combo = QComboBox()
        self.hazard_combo.addItems(["light", "ordinary", "extra"])
        self.input_layout.addWidget(QLabel("تصنيف الخطورة:"))
        self.input_layout.addWidget(self.hazard_combo)
        
        self.occupancy_combo = QComboBox()
        self.occupancy_combo.addItems(["سكن", "تجاري", "مكاتب", "صناعي"])
        self.input_layout.addWidget(QLabel("نوع الإشغال:"))
        self.input_layout.addWidget(self.occupancy_combo)
        
        self.occupants_spin = QSpinBox()
        self.occupants_spin.setRange(1, 1000)
        self.occupants_spin.setValue(10)
        self.input_layout.addWidget(QLabel("عدد الأشخاص للغرفة:"))
        self.input_layout.addWidget(self.occupants_spin)
        
        self.exits_spin = QSpinBox()
        self.exits_spin.setRange(1, 10)
        self.exits_spin.setValue(2)
        self.input_layout.addWidget(QLabel("عدد مخارج الطوارئ:"))
        self.input_layout.addWidget(self.exits_spin)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(2)
        self.results_table.setHorizontalHeaderLabels(["الغرفة", "وقت الإخلاء (ثانية)"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.input_layout.addWidget(QLabel("تحليل الإخلاء:"))
        self.input_layout.addWidget(self.results_table)
        
    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure = Figure(facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#161B22")
        self.ax.tick_params(colors="#C9D1D9")
        for spine in self.ax.spines.values():
            spine.set_color("#C9D1D9")
        self.canvas_layout.addWidget(self.canvas)
        
    def generate(self):
        """توليد بيانات النظام"""
        hazard_class = self.hazard_combo.currentText()
        occupants = self.occupants_spin.value()
        exits = self.exits_spin.value()
        
        engine = FireSafetyEngine(self.building_data, hazard_class, occupants, exits)
        self.generated_data = engine.generate_system()
        self._update_ui()
        self._plot_results()
        
    def _update_ui(self):
        """تحديث واجهة المستخدم"""
        times = self.generated_data.get("times", {})
        self.results_table.setRowCount(len(times))
        for i, (room, t) in enumerate(times.items()):
            self.results_table.setItem(i, 0, QTableWidgetItem(room))
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{t:.1f}"))
            
    def _plot_results(self):
        """رسم النتائج على المخطط"""
        self.ax.clear()
        
        rooms = self.building_data.get("rooms", [])
        for room in rooms:
            px, py = room.get("position_x", 0), room.get("position_y", 0)
            w, l = room.get("width", 5), room.get("length", 5)
            rect = patches.Rectangle((px, py), w, l, fill=False, edgecolor="#C9D1D9", linewidth=2)
            self.ax.add_patch(rect)
            
        for ex, ey in self.generated_data.get("exits", []):
            self.ax.plot(ex, ey, marker='s', color="#3FB950", markersize=12, label="مخرج طوارئ")
            
        for sx, sy in self.generated_data.get("sprinklers", []):
            self.ax.plot(sx, sy, marker='o', color="#58A6FF", markersize=6, alpha=0.7)
            
        for ex, ey in self.generated_data.get("extinguishers", []):
            self.ax.plot(ex, ey, marker='^', color="#F85149", markersize=8)
            
        for dx, dy in self.generated_data.get("detectors", []):
            self.ax.plot(dx, dy, marker='.', color="#D29922", markersize=10)
            
        for route in self.generated_data.get("routes", {}).values():
            if len(route) >= 2:
                xs, ys = zip(*route)
                self.ax.plot(xs, ys, color="#3FB950", linestyle='--', linewidth=2, alpha=0.8)
                self.ax.arrow(xs[0], ys[0], xs[-1]-xs[0], ys[-1]-ys[0], 
                             head_width=0.5, head_length=0.5, fc="#3FB950", ec="#3FB950", 
                             length_includes_head=True, alpha=0.5)
                
        self.ax.set_aspect('equal')
        self.ax.set_title("مخطط الإطفاء والسلامة (Fire & Safety)", color="#C9D1D9")
        self.figure.tight_layout()
        self.canvas.draw()
        
    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        pass
        
    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        pass
