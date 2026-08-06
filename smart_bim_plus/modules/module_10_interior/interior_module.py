import os
from typing import Dict, Any
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QTableWidget, QTableWidgetItem, QHeaderView)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches

from modules.base_module import BaseModule
from .interior_engine import InteriorEngine

class InteriorModule(BaseModule):
    """وحدة التصميم الداخلي"""

    SYSTEM_NUMBER = 10
    SYSTEM_NAME = "Interior Design"
    SYSTEM_NAME_AR = "التصميم الداخلي"
    ICON_NAME = "palette"

    def __init__(self, parent=None):
        """تهيئة الواجهة"""
        self.engine = InteriorEngine()
        super().__init__(parent)
        self.furniture_layout = {}
        self.syntax_analysis = {}

    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        style_layout = QVBoxLayout()
        style_label = QLabel("نمط التصميم:")
        self.style_combo = QComboBox()
        self.style_combo.addItems(["حديث", "كلاسيكي", "عربي", "مينيمالست"])
        style_layout.addWidget(style_label)
        style_layout.addWidget(self.style_combo)
        self.input_layout.addLayout(style_layout)

        budget_layout = QVBoxLayout()
        budget_label = QLabel("مستوى الميزانية:")
        self.budget_combo = QComboBox()
        self.budget_combo.addItems(["اقتصادي", "قياسي", "فاخر"])
        budget_layout.addWidget(budget_label)
        budget_layout.addWidget(self.budget_combo)
        self.input_layout.addLayout(budget_layout)

        color_layout = QVBoxLayout()
        color_label = QLabel("لوحة الألوان:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(["دافئة", "باردة", "محايدة"])
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_combo)
        self.input_layout.addLayout(color_layout)

    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure = Figure(figsize=(8, 6), facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#161B22")
        self.ax.tick_params(colors="#C9D1D9")
        for spine in self.ax.spines.values():
            spine.set_color("#C9D1D9")
            
        self.canvas_layout.addWidget(self.canvas)

        self.boq_table = QTableWidget()
        self.boq_table.setColumnCount(4)
        self.boq_table.setHorizontalHeaderLabels(["الغرفة", "العنصر", "المواد", "نقاط الحركة"])
        self.boq_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.canvas_layout.addWidget(self.boq_table)

    def generate(self):
        """توليد التصميم الداخلي"""
        rooms = self.building_data.get("rooms", [])
        style = self.style_combo.currentText()
        budget = self.budget_combo.currentText()
        
        self.syntax_analysis = self.engine.analyze_space_syntax(rooms)
        self.furniture_layout = self.engine.place_furniture(rooms)
        
        self._update_plot(rooms)
        self._update_table(rooms, style, budget)
        
        self.generated_data = {
            "syntax": self.syntax_analysis,
            "furniture": self.furniture_layout
        }

    def _update_plot(self, rooms):
        """تحديث الرسم البياني"""
        self.ax.clear()
        self.ax.set_facecolor("#161B22")
        
        for room in rooms:
            rx = room.get("position_x", 0.0)
            ry = room.get("position_y", 0.0)
            rw = room.get("width", 3.0)
            rl = room.get("length", 3.0)
            
            room_rect = patches.Rectangle((rx, ry), rw, rl, fill=False, edgecolor="#C9D1D9", linewidth=2)
            self.ax.add_patch(room_rect)
            self.ax.text(rx + rw/2, ry + rl/2, room["name"], color="#C9D1D9", ha="center", va="center", alpha=0.5)
            
            furnitures = self.furniture_layout.get(room["name"], [])
            for f in furnitures:
                f_rect = patches.Rectangle((f["x"], f["y"]), f["w"], f["l"], facecolor=f["color"], edgecolor="white", alpha=0.8)
                self.ax.add_patch(f_rect)
                
                clear_rect = patches.Rectangle((f["x"] - 0.3, f["y"] - 0.3), f["w"] + 0.6, f["l"] + 0.6, 
                                               fill=False, edgecolor="#D29922", linestyle=":", alpha=0.5)
                self.ax.add_patch(clear_rect)
                
            if len(furnitures) > 0:
                cx = rx + rw/2
                cy = ry + rl/2
                self.ax.plot([rx+0.5, cx], [ry+0.5, cy], color="#3FB950", linestyle="--", alpha=0.6)
                
        self.ax.autoscale()
        self.canvas.draw()

    def _update_table(self, rooms, style, budget):
        """تحديث جدول الكميات"""
        self.boq_table.setRowCount(0)
        row = 0
        for room in rooms:
            rname = room["name"]
            furnitures = self.furniture_layout.get(rname, [])
            materials = self.engine.recommend_materials(room.get("room_type", ""), style, budget)
            mat_str = f"أرضية: {materials['floor']}"
            score = self.engine.calculate_circulation_score(
                room.get("position_x", 0.0), room.get("position_y", 0.0),
                room.get("width", 3.0), room.get("length", 3.0), furnitures
            )
            
            for f in furnitures:
                self.boq_table.insertRow(row)
                self.boq_table.setItem(row, 0, QTableWidgetItem(rname))
                self.boq_table.setItem(row, 1, QTableWidgetItem(f["name"]))
                self.boq_table.setItem(row, 2, QTableWidgetItem(mat_str))
                self.boq_table.setItem(row, 3, QTableWidgetItem(f"{score:.1f}%"))
                row += 1

    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        pass

    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        pass
