import os
import json
import numpy as np
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QDoubleSpinBox, 
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches

from modules.base_module import BaseModule
from .hvac_engine import HVACEngine

class HVACModule(BaseModule):
    """وحدة تصميم و حسابات التكييف والتهوية"""

    SYSTEM_NUMBER = 6
    SYSTEM_NAME = "HVAC"
    SYSTEM_NAME_AR = "التكييف والتهوية"
    ICON_NAME = "hvac"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = None

    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        settings_group = QGroupBox("إعدادات التصميم")
        settings_layout = QVBoxLayout()

        outdoor_layout = QHBoxLayout()
        outdoor_layout.addWidget(QLabel("الحرارة الخارجية (°C):"))
        self.outdoor_temp_spin = QDoubleSpinBox()
        self.outdoor_temp_spin.setRange(20, 55)
        self.outdoor_temp_spin.setValue(45)
        outdoor_layout.addWidget(self.outdoor_temp_spin)
        settings_layout.addLayout(outdoor_layout)

        indoor_layout = QHBoxLayout()
        indoor_layout.addWidget(QLabel("الحرارة الداخلية (°C):"))
        self.indoor_temp_spin = QDoubleSpinBox()
        self.indoor_temp_spin.setRange(16, 30)
        self.indoor_temp_spin.setValue(22)
        indoor_layout.addWidget(self.indoor_temp_spin)
        settings_layout.addLayout(indoor_layout)

        orient_layout = QHBoxLayout()
        orient_layout.addWidget(QLabel("توجيه المبنى (درجة):"))
        self.orient_spin = QDoubleSpinBox()
        self.orient_spin.setRange(0, 360)
        self.orient_spin.setValue(0)
        orient_layout.addWidget(self.orient_spin)
        settings_layout.addLayout(orient_layout)

        wall_layout = QHBoxLayout()
        wall_layout.addWidget(QLabel("عزل الجدران:"))
        self.wall_combo = QComboBox()
        self.wall_combo.addItems(["ضعيف", "متوسط", "جيد", "ممتاز"])
        self.wall_combo.setCurrentText("متوسط")
        wall_layout.addWidget(self.wall_combo)
        settings_layout.addLayout(wall_layout)

        glass_layout = QHBoxLayout()
        glass_layout.addWidget(QLabel("نوع الزجاج:"))
        self.glass_combo = QComboBox()
        self.glass_combo.addItems(["عادي", "مزدوج", "عاكس"])
        self.glass_combo.setCurrentText("مزدوج")
        glass_layout.addWidget(self.glass_combo)
        settings_layout.addLayout(glass_layout)

        settings_group.setLayout(settings_layout)
        self.input_layout.insertWidget(1, settings_group)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["الخاصية", "القيمة"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("background-color: #161B22; color: #C9D1D9;")
        self.input_layout.insertWidget(2, self.table)

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
        if not self.building_data:
            raise ValueError("لا توجد بيانات للمبنى")

        outdoor = self.outdoor_temp_spin.value()
        indoor = self.indoor_temp_spin.value()
        orientation = self.orient_spin.value()
        wall_ins = self.wall_combo.currentText()
        glass = self.glass_combo.currentText()

        self.engine = HVACEngine(self.building_data, outdoor, indoor, orientation, wall_ins, glass)
        self.engine.calculate_loads()
        self.engine.route_ducts()
        self.engine.calculate_duct_sizes()
        self.engine.calculate_efficiency()

        self.generated_data = self.engine.results

        self._update_table()
        self._draw_plan()

    def _update_table(self):
        """تحديث جدول النتائج"""
        self.table.setRowCount(0)
        data = [
            ("الحمل الكلي (BTU)", f"{self.generated_data.get('total_load_btu', 0):.2f}"),
            ("عدد وحدات التكييف", str(len(self.generated_data.get('ac_units', [])))),
            ("كفاءة الطاقة (SEER)", f"{self.generated_data.get('seer', 0):.1f}"),
            ("تكلفة الطاقة المتوقعة/ساعة", f"${self.generated_data.get('energy_cost_per_hour', 0):.2f}")
        ]
        
        for row, (key, val) in enumerate(data):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(key))
            self.table.setItem(row, 1, QTableWidgetItem(val))

    def _draw_plan(self):
        """رسم المخطط وتوزيعات التكييف"""
        self.ax.clear()
        
        plot_w = self.building_data.get("plot_width", 20.0)
        plot_l = self.building_data.get("plot_length", 20.0)
        self.ax.set_xlim(-1, plot_w + 1)
        self.ax.set_ylim(-1, plot_l + 1)
        self.ax.set_aspect('equal')
        
        max_load = max([r["load_btu"] for r in self.generated_data.get("room_loads", [])] + [1])
        
        for room in self.generated_data.get("room_loads", []):
            intensity = min(1.0, room["load_btu"] / max_load)
            color = (intensity, 0.2, 1 - intensity, 0.3)
            
            rect = patches.Rectangle(
                (room["x"], room["y"]), room["w"], room["l"],
                linewidth=1, edgecolor="#58A6FF", facecolor=color
            )
            self.ax.add_patch(rect)
            self.ax.text(
                room["x"] + room["w"]/2, room["y"] + room["l"]/2,
                f"{room['load_ton']:.1f} TR",
                color="#C9D1D9", ha="center", va="center"
            )

        for ac in self.generated_data.get("ac_units", []):
            self.ax.plot(ac["x"], ac["y"], 's', color="#F85149", markersize=10)
            
        for duct in self.generated_data.get("ducts", []):
            path = duct["path"]
            if len(path) > 1:
                xs = [p[0] for p in path]
                ys = [p[1] for p in path]
                self.ax.plot(xs, ys, '-', color="#3FB950", linewidth=max(2, duct.get("width_in", 10)/5))

        self.ax.set_title("مخطط التكييف ومسارات الهواء", color="#C9D1D9")
        self.canvas.draw()

    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("0\nSECTION\n2\nENTITIES\n")
            for ac in self.generated_data.get("ac_units", []):
                f.write("0\nCIRCLE\n8\nHVAC\n")
                f.write(f"10\n{ac['x']}\n20\n{ac['y']}\n40\n0.5\n")
            for duct in self.generated_data.get("ducts", []):
                path = duct["path"]
                for i in range(len(path)-1):
                    f.write("0\nLINE\n8\nDUCTS\n")
                    f.write(f"10\n{path[i][0]}\n20\n{path[i][1]}\n")
                    f.write(f"11\n{path[i+1][0]}\n21\n{path[i+1][1]}\n")
            f.write("0\nENDSEC\n0\nEOF\n")

    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\n")
            f.write("/* بيانات مجاري الهواء والوحدات هنا */\n")
            f.write("ENDSEC;\nEND-ISO-10303-21;\n")
