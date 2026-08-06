from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QDoubleSpinBox
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Rectangle
from typing import Dict, Any

from modules.base_module import BaseModule
from .gas_engine import GasEngine


class GasModule(BaseModule):
    """واجهة مستخدم نظام الغاز"""

    SYSTEM_NUMBER = 7
    SYSTEM_NAME = "Gas System"
    SYSTEM_NAME_AR = "نظام الغاز"
    ICON_NAME = "gas"

    def setup_input_panel(self):
        """إعداد لوحة الإدخال للنظام"""
        self.gas_type_label = QLabel("نوع الغاز:")
        self.gas_type_combo = QComboBox()
        self.gas_type_combo.addItems(["غاز طبيعي (Natural)", "غاز مسال (LPG)"])
        self.input_layout.addWidget(self.gas_type_label)
        self.input_layout.addWidget(self.gas_type_combo)

        self.meter_x_label = QLabel("موقع العداد (X):")
        self.meter_x_spin = QDoubleSpinBox()
        self.meter_x_spin.setRange(0, 100)
        self.meter_x_spin.setValue(0)
        self.input_layout.addWidget(self.meter_x_label)
        self.input_layout.addWidget(self.meter_x_spin)

        self.meter_y_label = QLabel("موقع العداد (Y):")
        self.meter_y_spin = QDoubleSpinBox()
        self.meter_y_spin.setRange(0, 100)
        self.meter_y_spin.setValue(0)
        self.input_layout.addWidget(self.meter_y_label)
        self.input_layout.addWidget(self.meter_y_spin)

        self.burners_label = QLabel("عدد الشعلات:")
        self.burners_spin = QSpinBox()
        self.burners_spin.setRange(1, 10)
        self.burners_spin.setValue(4)
        self.input_layout.addWidget(self.burners_label)
        self.input_layout.addWidget(self.burners_spin)

        self.heater_label = QLabel("نوع سخان المياه:")
        self.heater_combo = QComboBox()
        self.heater_combo.addItems(["غاز (Gas)", "كهرباء (Electric)"])
        self.input_layout.addWidget(self.heater_label)
        self.input_layout.addWidget(self.heater_combo)

        self.analysis_table = QTableWidget()
        self.analysis_table.setColumnCount(2)
        self.analysis_table.setHorizontalHeaderLabels(["الخاصية", "القيمة"])
        self.analysis_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.analysis_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.input_layout.addWidget(self.analysis_table)

    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure, self.ax = plt.subplots()
        self.figure.patch.set_facecolor("#0D1117")
        self.ax.set_facecolor("#161B22")
        self.ax.tick_params(colors="#C9D1D9")
        for spine in self.ax.spines.values():
            spine.set_color("#C9D1D9")
        self.canvas = FigureCanvas(self.figure)
        self.canvas_layout.addWidget(self.canvas)

    def generate(self):
        """توليد ورسم شبكة الغاز"""
        gas_type = "Natural" if self.gas_type_combo.currentIndex() == 0 else "LPG"
        meter_pos = (self.meter_x_spin.value(), self.meter_y_spin.value())
        burners = self.burners_spin.value()
        heater_type = "Gas" if self.heater_combo.currentIndex() == 0 else "Electric"

        engine = GasEngine(self.building_data, gas_type, meter_pos, burners, heater_type)
        self.generated_data = engine.run()

        self._update_table(self.generated_data.get("analysis", {}))
        self._draw_system()

    def _update_table(self, analysis_results: Dict[str, str]):
        """تحديث جدول نتائج التحليل"""
        self.analysis_table.setRowCount(len(analysis_results))
        for row, (key, value) in enumerate(analysis_results.items()):
            self.analysis_table.setItem(row, 0, QTableWidgetItem(key))
            self.analysis_table.setItem(row, 1, QTableWidgetItem(value))

    def _draw_system(self):
        """رسم المخطط مع شبكة الغاز"""
        self.ax.clear()
        
        for room in self.building_data.get("rooms", []):
            rx = room.get("position_x", 0)
            ry = room.get("position_y", 0)
            rw = room.get("width", 0)
            rl = room.get("length", 0)
            
            rect = Rectangle((rx, ry), rw, rl, fill=False, edgecolor="#C9D1D9", linestyle="--")
            self.ax.add_patch(rect)
            self.ax.text(rx + rw/2, ry + rl/2, room.get("name", ""), color="#C9D1D9", ha="center", va="center", fontsize=8)

        pipes = self.generated_data.get("pipes", [])
        for pipe in pipes:
            path = pipe["path"]
            if path:
                xs, ys = zip(*path)
                self.ax.plot(xs, ys, color="#D29922", linewidth=2, label="أنبوب غاز" if pipes.index(pipe) == 0 else "")

        detectors = self.generated_data.get("detectors", [])
        if detectors:
            dxs, dys = zip(*detectors)
            self.ax.scatter(dxs, dys, color="#D29922", marker="o", s=50, label="كاشف تسرب")

        valves = self.generated_data.get("valves", [])
        if valves:
            vxs, vys = zip(*valves)
            self.ax.scatter(vxs, vys, color="#F85149", marker="s", s=50, label="صمام غلق")

        ventilations = self.generated_data.get("ventilations", [])
        if ventilations:
            vtxs = [v["x"] for v in ventilations]
            vtys = [v["y"] for v in ventilations]
            self.ax.scatter(vtxs, vtys, color="#3FB950", marker="^", s=50, label="فتحة تهوية")

        meter_x = self.meter_x_spin.value()
        meter_y = self.meter_y_spin.value()
        self.ax.scatter([meter_x], [meter_y], color="#58A6FF", marker="D", s=70, label="العداد الرئيسي")

        self.ax.set_title("مخطط نظام الغاز", color="#C9D1D9")
        self.ax.set_aspect("equal")
        self.ax.legend(loc="upper right", facecolor="#161B22", edgecolor="#C9D1D9", labelcolor="#C9D1D9", fontsize=8)
        self.canvas.draw()

    def export_dxf(self, filepath: str):
        """تصدير إلى صيغة DXF"""
        pass

    def export_ifc(self, filepath: str):
        """تصدير إلى صيغة IFC"""
        pass
