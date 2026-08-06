import sys
import numpy as np
from typing import Dict, Any
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, 
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from modules.base_module import BaseModule
from .plumbing_engine import PlumbingEngine

class PlumbingModule(BaseModule):
    """وحدة التمديدات الصحية والمياه"""

    SYSTEM_NUMBER = 5
    SYSTEM_NAME = "Plumbing Module"
    SYSTEM_NAME_AR = "وحدة التمديدات الصحية"
    ICON_NAME = "plumbing"

    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        group_box = QGroupBox("إعدادات التصميم")
        form_layout = QFormLayout(group_box)
        
        self.occupants_spin = QSpinBox()
        self.occupants_spin.setRange(1, 1000)
        self.occupants_spin.setValue(4)
        
        self.material_combo = QComboBox()
        self.material_combo.addItems(["PVC", "Copper", "PEX"])
        
        self.heater_loc_combo = QComboBox()
        self.heater_loc_combo.addItems(["Main", "Bathroom", "Kitchen"])
        
        form_layout.addRow("عدد الشاغلين:", self.occupants_spin)
        form_layout.addRow("مادة الأنابيب:", self.material_combo)
        form_layout.addRow("موقع السخان:", self.heater_loc_combo)
        
        self.input_layout.insertWidget(1, group_box)

        self.table = QTableWidget(5, 2)
        self.table.setHorizontalHeaderLabels(["الخاصية", "القيمة"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.input_layout.insertWidget(2, self.table)

    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure = Figure(facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#161B22")
        self.canvas_layout.addWidget(self.canvas)

    def generate(self):
        """توليد بيانات النظام"""
        params = {
            "occupants": self.occupants_spin.value(),
            "material": self.material_combo.currentText(),
            "heater_location": self.heater_loc_combo.currentText()
        }
        
        engine = PlumbingEngine(self.building_data, params)
        self.generated_data = engine.generate_networks()
        
        self._update_ui_results()
        self._plot_networks()

    def _update_ui_results(self):
        """تحديث جدول النتائج"""
        data = [
            ("طول شبكة المياه الباردة", f"{self.generated_data.get('total_cold_length', 0):.2f} م"),
            ("طول شبكة المياه الساخنة", f"{self.generated_data.get('total_hot_length', 0):.2f} م"),
            ("طول شبكة الصرف", f"{self.generated_data.get('total_drain_length', 0):.2f} م"),
            ("الاستهلاك اليومي", f"{self.generated_data.get('estimated_consumption', 0):.0f} لتر"),
            ("حجم خزان الحصاد", f"{self.generated_data.get('tank_size', 0):.1f} م٣")
        ]
        
        for i, (key, val) in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(key))
            self.table.setItem(i, 1, QTableWidgetItem(val))

    def _plot_networks(self):
        """رسم الشبكات"""
        self.ax.clear()
        
        nodes = self.generated_data.get("nodes", [])
        cold = self.generated_data.get("cold_network", [])
        hot = self.generated_data.get("hot_network", [])
        drain = self.generated_data.get("drain_network", [])
        
        pos_dict = {n["id"]: n["pos"] for n in nodes}
        
        for e in drain:
            if e["u"] in pos_dict and e["v"] in pos_dict:
                x = [pos_dict[e["u"]][0], pos_dict[e["v"]][0]]
                y = [pos_dict[e["u"]][1], pos_dict[e["v"]][1]]
                self.ax.plot(x, y, color="#8B4513", linewidth=3, linestyle="--", alpha=0.7, label="صرف صحي")
                
        for e in cold:
            if e["u"] in pos_dict and e["v"] in pos_dict:
                x = [pos_dict[e["u"]][0], pos_dict[e["v"]][0]]
                y = [pos_dict[e["u"]][1], pos_dict[e["v"]][1]]
                self.ax.plot(x, y, color="#58A6FF", linewidth=2, label="مياه باردة")
                
        for e in hot:
            if e["u"] in pos_dict and e["v"] in pos_dict:
                x = [pos_dict[e["u"]][0], pos_dict[e["v"]][0]]
                y = [pos_dict[e["u"]][1], pos_dict[e["v"]][1]]
                self.ax.plot(x, y, color="#F85149", linewidth=2, label="مياه ساخنة")
                
        for n in nodes:
            color = "#C9D1D9"
            if n["type"] == "wet":
                color = "#3FB950"
            elif n["type"] == "heater":
                color = "#D29922"
            elif n["type"] == "entry":
                color = "#ffffff"
            self.ax.scatter(n["pos"][0], n["pos"][1], color=color, s=100, zorder=5)
            self.ax.text(n["pos"][0], n["pos"][1]+0.5, n["id"], color="#C9D1D9", fontsize=8, ha="center")

        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        if by_label:
            self.ax.legend(by_label.values(), by_label.keys(), loc="upper right")

        self.ax.set_title("شبكات التمديدات الصحية", color="#C9D1D9")
        self.ax.tick_params(colors="#C9D1D9")
        self.ax.set_aspect('equal')
        self.figure.tight_layout()
        self.canvas.draw()

    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        pass

    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        pass
