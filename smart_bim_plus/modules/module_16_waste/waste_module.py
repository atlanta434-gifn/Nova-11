import numpy as np
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, 
                             QComboBox, QGroupBox, QFormLayout)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches

from modules.base_module import BaseModule
from .waste_engine import WasteEngine

class WasteModule(BaseModule):
    """وحدة نظام إدارة النفايات"""

    SYSTEM_NUMBER = 16
    SYSTEM_NAME = "Waste Management"
    SYSTEM_NAME_AR = "نظام إدارة النفايات"
    ICON_NAME = "trash"

    def setup_input_panel(self):
        """إعداد واجهة الإدخال"""
        group = QGroupBox("إعدادات النفايات")
        layout = QFormLayout()

        self.occupants_spin = QSpinBox()
        self.occupants_spin.setRange(1, 10000)
        self.occupants_spin.setValue(100)
        layout.addRow("عدد الشاغلين:", self.occupants_spin)

        self.floors_spin = QSpinBox()
        self.floors_spin.setRange(1, 150)
        self.floors_spin.setValue(10)
        layout.addRow("عدد الطوابق:", self.floors_spin)

        self.building_type_combo = QComboBox()
        self.building_type_combo.addItems(["residential", "commercial"])
        layout.addRow("نوع المبنى:", self.building_type_combo)

        self.recycling_combo = QComboBox()
        self.recycling_combo.addItems(["basic", "advanced"])
        layout.addRow("سياسة إعادة التدوير:", self.recycling_combo)

        group.setLayout(layout)
        self.input_layout.insertWidget(1, group)

        self.results_label = QLabel("النتائج ستظهر هنا")
        self.results_label.setWordWrap(True)
        self.results_label.setStyleSheet("color: #C9D1D9;")
        self.input_layout.insertWidget(2, self.results_label)

    def setup_canvas(self):
        """إعداد لوحة الرسم الخاصة بالنفايات"""
        self.figure = Figure(facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#161B22")
        self.ax.tick_params(colors="#C9D1D9")
        for spine in self.ax.spines.values():
            spine.set_color("#C9D1D9")
        self.canvas_layout.addWidget(self.canvas)

    def generate(self):
        """توليد البيانات والرسم"""
        engine = WasteEngine(
            self.building_data,
            self.occupants_spin.value(),
            self.building_type_combo.currentText(),
            self.recycling_combo.currentText(),
            self.floors_spin.value()
        )
        self.generated_data = engine.calculate()

        self.ax.clear()
        
        rooms = self.building_data.get("rooms", [])
        for room in rooms:
            px = float(room.get("position_x", 0.0))
            py = float(room.get("position_y", 0.0))
            w = float(room.get("width", 0.0))
            l = float(room.get("length", 0.0))
            rect = patches.Rectangle((px, py), w, l, fill=False, edgecolor="#58A6FF", linestyle='--')
            self.ax.add_patch(rect)
            self.ax.text(px + w/2, py + l/2, room.get("name", ""), color="#C9D1D9", ha='center', va='center', fontsize=8)

        chute_pos = self.generated_data["chute_position"]
        self.ax.plot(chute_pos[0], chute_pos[1], 'ro', markersize=15, label='مجرى النفايات')
        
        self.ax.legend(facecolor="#161B22", edgecolor="#C9D1D9", labelcolor="#C9D1D9")
        self.ax.set_title("تصميم نظام النفايات", color="#C9D1D9")
        self.ax.autoscale_view()
        self.canvas.draw()

        res = self.generated_data
        text = (f"النفايات اليومية: {res['daily_total_kg']:.2f} كجم\n"
                f"قطر المجرى: {res['chute_diameter_mm']:.2f} مم\n"
                f"غرفة التجميع: {res['collection_room_area_m2']:.2f} م2\n"
                f"التهوية المطلوبة: {res['ventilation_flow_m3_h']:.2f} م3/س\n"
                f"معدل التدوير: {res['recycling_rate']}%\n"
                f"تكرار التجميع: {res['collection_frequency']}")
        self.results_label.setText(text)

    def export_dxf(self, filepath: str):
        """تصدير DXF"""
        pass

    def export_ifc(self, filepath: str):
        """تصدير IFC"""
        pass
