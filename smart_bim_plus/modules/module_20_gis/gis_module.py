import os
from typing import Dict, Any
import numpy as np
from PyQt6.QtWidgets import (
    QVBoxLayout, QFormLayout, QDoubleSpinBox, QComboBox, 
    QLabel, QGroupBox, QSpinBox, QHBoxLayout
)
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from modules.base_module import BaseModule
from .gis_engine import GISEngine


class GISModule(BaseModule):
    """وحدة الخرائط الجغرافية والمسح"""
    
    SYSTEM_NUMBER = 20
    SYSTEM_NAME = "Geographic Maps"
    SYSTEM_NAME_AR = "الخرائط الجغرافية والمسح"
    ICON_NAME = "map"

    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        group_box = QGroupBox("محددات الموقع الجغرافي")
        form_layout = QFormLayout(group_box)
        
        self.grade_input = QDoubleSpinBox()
        self.grade_input.setRange(50.0, 500.0)
        self.grade_input.setValue(100.0)
        self.grade_input.setSuffix(" م")
        form_layout.addRow("منسوب التسوية:", self.grade_input)
        
        self.soil_type_input = QComboBox()
        self.soil_type_input.addItems(["رملي", "طيني", "صخري", "غريني"])
        form_layout.addRow("نوع التربة:", self.soil_type_input)

        self.groundwater_input = QDoubleSpinBox()
        self.groundwater_input.setRange(0.0, 100.0)
        self.groundwater_input.setValue(2.5)
        self.groundwater_input.setSuffix(" م")
        form_layout.addRow("عمق المياه الجوفية:", self.groundwater_input)

        self.seismic_zone_input = QSpinBox()
        self.seismic_zone_input.setRange(1, 5)
        self.seismic_zone_input.setValue(2)
        form_layout.addRow("المنطقة الزلزالية:", self.seismic_zone_input)

        self.input_layout.insertWidget(1, group_box)

        results_group = QGroupBox("نتائج التحليل")
        results_layout = QFormLayout(results_group)
        
        self.lbl_cut = QLabel("0.0 م³")
        self.lbl_fill = QLabel("0.0 م³")
        self.lbl_net = QLabel("0.0 م³")
        
        results_layout.addRow("حجم الحفر:", self.lbl_cut)
        results_layout.addRow("حجم الردم:", self.lbl_fill)
        results_layout.addRow("الصافي:", self.lbl_net)
        
        self.input_layout.insertWidget(2, results_group)

    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure = Figure(facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.canvas_layout.addWidget(self.canvas)

        self.ax_surface = self.figure.add_subplot(121, projection='3d')
        self.ax_surface.set_facecolor("#161B22")
        
        self.ax_contour = self.figure.add_subplot(122)
        self.ax_contour.set_facecolor("#161B22")
        
        self.figure.tight_layout()

    def generate(self):
        """توليد التحليل الجغرافي"""
        width = float(self.building_data.get("plot_width", 50.0))
        length = float(self.building_data.get("plot_length", 50.0))
        
        engine = GISEngine(width, length, resolution=1.0)
        engine.generate_synthetic_terrain(base_elevation=100.0, variance=2.5)
        
        grade = self.grade_input.value()
        cut_fill = engine.calculate_cut_fill(grade)
        
        self.lbl_cut.setText(f"{cut_fill['cut_volume']:.2f} م³")
        self.lbl_fill.setText(f"{cut_fill['fill_volume']:.2f} م³")
        self.lbl_net.setText(f"{cut_fill['net']:.2f} م³")
        
        self.lbl_cut.setStyleSheet("color: #F85149;")
        self.lbl_fill.setStyleSheet("color: #58A6FF;")
        net_color = "#3FB950" if abs(cut_fill['net']) < 10 else "#D29922"
        self.lbl_net.setStyleSheet(f"color: {net_color};")
        
        slope_data = engine.analyze_slope()
        drainage_data = engine.analyze_drainage()
        
        self.ax_surface.clear()
        self.ax_contour.clear()
        
        self.ax_surface.set_facecolor("#161B22")
        self.ax_surface.xaxis.set_pane_color((0.086, 0.106, 0.133, 1.0))
        self.ax_surface.yaxis.set_pane_color((0.086, 0.106, 0.133, 1.0))
        self.ax_surface.zaxis.set_pane_color((0.086, 0.106, 0.133, 1.0))
        
        self.ax_surface.plot_surface(
            engine.X, engine.Y, engine.elevation,
            cmap='terrain', edgecolor='none', alpha=0.8
        )
        self.ax_surface.plot_surface(
            engine.X, engine.Y, np.full_like(engine.elevation, grade),
            color="#58A6FF", alpha=0.3
        )
        
        self.ax_surface.set_title("النموذج ثلاثي الأبعاد", color="#C9D1D9")
        self.ax_surface.tick_params(colors="#C9D1D9")
        
        self.ax_contour.set_facecolor("#161B22")
        self.ax_contour.contourf(
            engine.X, engine.Y, engine.elevation,
            levels=20, cmap='terrain', alpha=0.8
        )
        self.ax_contour.contour(
            engine.X, engine.Y, engine.elevation,
            levels=20, colors='black', linewidths=0.5
        )
        
        step = max(1, int(min(engine.nx, engine.ny) / 15))
        self.ax_contour.quiver(
            engine.X[::step, ::step], engine.Y[::step, ::step],
            drainage_data['u'][::step, ::step], drainage_data['v'][::step, ::step],
            color="#58A6FF", alpha=0.6, scale=20
        )
        
        rooms = self.building_data.get("rooms", [])
        for room in rooms:
            rx = float(room.get("position_x", 0))
            ry = float(room.get("position_y", 0))
            rw = float(room.get("width", 0))
            rl = float(room.get("length", 0))
            rect = plt.Rectangle((rx, ry), rw, rl, fill=False, edgecolor="#F85149", linewidth=2)
            self.ax_contour.add_patch(rect)
            
        self.ax_contour.set_title("الخريطة الكنتورية ومسارات التصريف", color="#C9D1D9")
        self.ax_contour.tick_params(colors="#C9D1D9")
        self.ax_contour.set_aspect('equal')
        
        self.canvas.draw()
        
        self.generated_data = {
            'cut_volume': cut_fill['cut_volume'],
            'fill_volume': cut_fill['fill_volume'],
            'net_volume': cut_fill['net'],
            'slope_stats': slope_data['stats'],
            'optimal_grade': engine.get_optimal_grade()
        }

    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("0\nSECTION\n2\nENTITIES\n0\nENDSEC\n0\nEOF\n")

    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n")
