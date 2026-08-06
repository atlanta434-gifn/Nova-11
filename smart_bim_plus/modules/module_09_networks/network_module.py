import numpy as np
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QDoubleSpinBox, QFormLayout, QGroupBox, QSpinBox)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from modules.base_module import BaseModule
from .network_engine import NetworkEngine

class NetworkModule(BaseModule):
    """وحدة تصميم شبكات الاتصالات والإنترنت"""

    SYSTEM_NUMBER = 9
    SYSTEM_NAME = "Networks & Telecom"
    SYSTEM_NAME_AR = "شبكات الاتصالات والإنترنت"
    ICON_NAME = "wifi"

    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        settings_group = QGroupBox("إعدادات الشبكة")
        form_layout = QFormLayout()

        self.standard_combo = QComboBox()
        self.standard_combo.addItems(["WiFi 6", "WiFi 5", "WiFi 6E"])
        form_layout.addRow("معيار الشبكة:", self.standard_combo)

        self.material_combo = QComboBox()
        self.material_combo.addItems(["طابوق", "خرسانة", "جدران جافة", "زجاج"])
        form_layout.addRow("مادة الجدران:", self.material_combo)

        self.coverage_spin = QDoubleSpinBox()
        self.coverage_spin.setRange(-90.0, -40.0)
        self.coverage_spin.setValue(-70.0)
        self.coverage_spin.setSuffix(" dBm")
        form_layout.addRow("التغطية المطلوبة:", self.coverage_spin)

        self.power_spin = QDoubleSpinBox()
        self.power_spin.setRange(10.0, 30.0)
        self.power_spin.setValue(20.0)
        self.power_spin.setSuffix(" dBm")
        form_layout.addRow("طاقة المرسل:", self.power_spin)

        settings_group.setLayout(form_layout)
        self.input_layout.addWidget(settings_group)

        summary_group = QGroupBox("ملخص النتائج")
        sum_layout = QVBoxLayout()
        self.ap_count_lbl = QLabel("عدد نقاط الوصول: -")
        self.cable_len_lbl = QLabel("طول الكابلات: - م")
        self.cost_lbl = QLabel("التكلفة التقديرية: - $")
        
        sum_layout.addWidget(self.ap_count_lbl)
        sum_layout.addWidget(self.cable_len_lbl)
        sum_layout.addWidget(self.cost_lbl)
        summary_group.setLayout(sum_layout)
        
        self.input_layout.addWidget(summary_group)

    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure = Figure(facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#161B22")
        self.ax.tick_params(colors="#C9D1D9")
        for spine in self.ax.spines.values():
            spine.set_color("#30363D")
        self.canvas_layout.addWidget(self.canvas)

    def generate(self):
        """توليد بيانات النظام"""
        engine = NetworkEngine(self.building_data)
        
        standard = self.standard_combo.currentText()
        material = self.material_combo.currentText()
        coverage = self.coverage_spin.value()
        power = self.power_spin.value()

        self.generated_data = engine.generate_network(standard, material, coverage, power)
        
        aps = self.generated_data["access_points"]
        cable_len = self.generated_data["total_cable_length"]
        cost = self.generated_data["cost"]

        self.ap_count_lbl.setText(f"عدد نقاط الوصول: {len(aps)}")
        self.cable_len_lbl.setText(f"طول الكابلات: {cable_len:.1f} م")
        self.cost_lbl.setText(f"التكلفة التقديرية: {cost:.0f} $")

        self._draw_results()

    def _draw_results(self):
        """رسم النتائج على اللوحة"""
        self.ax.clear()
        
        heatmap_data = self.generated_data["heatmap"]
        res = self.generated_data["grid_res"]
        extent = [0, heatmap_data.shape[1] * res, 0, heatmap_data.shape[0] * res]
        
        colors = ["#F85149", "#D29922", "#3FB950"]
        cmap = LinearSegmentedColormap.from_list("wifi_cmap", colors)
        
        img = self.ax.imshow(heatmap_data, extent=extent, origin='lower', 
                             cmap=cmap, alpha=0.6, vmin=-90, vmax=-40)
        
        rooms = self.building_data.get("rooms", [])
        for room in rooms:
            px = float(room.get("position_x", 0.0))
            py = float(room.get("position_y", 0.0))
            w = float(room.get("width", 5.0))
            l = float(room.get("length", 5.0))
            rect = patches.Rectangle((px, py), w, l, fill=False, edgecolor="#C9D1D9", linewidth=1.5)
            self.ax.add_patch(rect)

        cables = self.generated_data.get("cables", [])
        for p1, p2 in cables:
            self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="#58A6FF", linewidth=2.0, linestyle="--")

        aps = self.generated_data.get("access_points", [])
        for ax_x, ax_y in aps:
            self.ax.plot(ax_x, ax_y, marker='o', color="#3FB950", markersize=8)
            
        server = self.generated_data.get("server_room")
        if server:
            self.ax.plot(server[0], server[1], marker='s', color="#D29922", markersize=10)

        self.ax.set_title(self.SYSTEM_NAME_AR, color="#C9D1D9")
        self.ax.set_aspect('equal')
        self.canvas.draw()

    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        pass

    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        pass
