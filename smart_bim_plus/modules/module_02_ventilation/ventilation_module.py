import os
from typing import Dict, Any
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QComboBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from modules.base_module import BaseModule
from .ventilation_engine import VentilationEngine


class VentilationModule(BaseModule):
    """وحدة التهوية الطبيعية"""
    
    SYSTEM_NUMBER = 2
    SYSTEM_NAME = "Natural Ventilation"
    SYSTEM_NAME_AR = "التهوية الطبيعية"
    ICON_NAME = "air"

    def setup_input_panel(self):
        """إعداد واجهة إدخال البيانات"""
        self.wind_speed_input = QDoubleSpinBox()
        self.wind_speed_input.setRange(0.0, 50.0)
        self.wind_speed_input.setValue(3.5)
        self.wind_speed_input.setSuffix(" m/s")
        
        self.wind_dir_input = QComboBox()
        self.wind_dir_input.addItems(["N", "S", "E", "W", "NE", "NW", "SE", "SW"])
        
        self.temp_input = QDoubleSpinBox()
        self.temp_input.setRange(-20.0, 60.0)
        self.temp_input.setValue(24.0)
        self.temp_input.setSuffix(" °C")
        
        self.input_layout.addWidget(QLabel("سرعة الرياح:"))
        self.input_layout.addWidget(self.wind_speed_input)
        self.input_layout.addWidget(QLabel("اتجاه الرياح:"))
        self.input_layout.addWidget(self.wind_dir_input)
        self.input_layout.addWidget(QLabel("درجة الحرارة:"))
        self.input_layout.addWidget(self.temp_input)

    def setup_canvas(self):
        """إعداد لوحة الرسم الخاصة بالنتائج"""
        self.figure = Figure(facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.canvas_layout.addWidget(self.canvas)

    def generate(self):
        """بدء عملية التوليد والمحاكاة"""
        wind_speed = self.wind_speed_input.value()
        wind_dir = self.wind_dir_input.currentText()
        temp = self.temp_input.value()
        
        engine = VentilationEngine(self.building_data, wind_speed, wind_dir, temp)
        engine.setup_domain()
        engine.run_simulation(steps=200)
        
        self.generated_data = engine.get_results()
        self._update_plot()

    def _update_plot(self):
        """تحديث لوحة الرسم بالنتائج الجديدة"""
        self.figure.clear()
        
        ax1 = self.figure.add_subplot(121, facecolor="#161B22")
        ax2 = self.figure.add_subplot(122, facecolor="#161B22")
        
        u = self.generated_data["u"]
        pressure = self.generated_data["pressure"]
        obstacle = self.generated_data["obstacle"]
        ach_results = self.generated_data["ach"]
        
        nx, ny = pressure.shape
        x = np.arange(nx)
        y = np.arange(ny)
        X, Y = np.meshgrid(x, y, indexing='ij')
        
        speed = np.sqrt(u[0]**2 + u[1]**2)
        speed[obstacle] = np.nan
        
        pc = ax1.pcolormesh(X, Y, speed, cmap='viridis', shading='auto')
        self.figure.colorbar(pc, ax=ax1, label='سرعة الهواء')
        ax1.set_title("حقل السرعة", color="#C9D1D9")
        
        p_plot = pressure.copy()
        p_plot[obstacle] = np.nan
        pc2 = ax2.pcolormesh(X, Y, p_plot, cmap='coolwarm', shading='auto')
        self.figure.colorbar(pc2, ax=ax2, label='الضغط')
        ax2.set_title("توزيع الضغط", color="#C9D1D9")
        
        for name, data in ach_results.items():
            cx, cy = data["center"]
            color = data["color"]
            ach_val = data["ach"]
            ax2.text(cx, cy, f"{name}\nACH: {ach_val:.1f}", color=color, 
                     ha='center', va='center', fontsize=8, fontweight='bold')
                     
        for ax in [ax1, ax2]:
            ax.tick_params(colors="#C9D1D9")
            ax.xaxis.label.set_color("#C9D1D9")
            ax.yaxis.label.set_color("#C9D1D9")
            ax.title.set_color("#C9D1D9")
            for spine in ax.spines.values():
                spine.set_color("#C9D1D9")
                
        self.figure.tight_layout()
        self.canvas.draw()

    def export_dxf(self, filepath: str):
        """تصدير النتائج بصيغة DXF"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("0\nSECTION\n2\nENTITIES\n0\nENDSEC\n0\nEOF\n")

    def export_ifc(self, filepath: str):
        """تصدير النتائج بصيغة IFC"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\nENDSEC;\nEND-ISO-10303-21;\n")
