from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QSpinBox, QDoubleSpinBox, QFormLayout, 
    QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from modules.base_module import BaseModule
from .structural_engine import StructuralEngine

class StructuralModule(BaseModule):
    """وحدة التحليل الإنشائي - واجهة المستخدم"""
    
    SYSTEM_NUMBER = 13
    SYSTEM_NAME = "Structural Analysis"
    SYSTEM_NAME_AR = "التحليل الإنشائي"
    ICON_NAME = "structure"

    def setup_input_panel(self):
        """إعداد لوحة الإدخال للمعاملات الإنشائية"""
        group_box = QGroupBox("محددات التصميم")
        form_layout = QFormLayout(group_box)
        
        self.soil_capacity_spin = QDoubleSpinBox()
        self.soil_capacity_spin.setRange(50.0, 500.0)
        self.soil_capacity_spin.setValue(150.0)
        self.soil_capacity_spin.setSuffix(" kN/m²")
        form_layout.addRow("جهد التربة:", self.soil_capacity_spin)
        
        self.concrete_combo = QComboBox()
        self.concrete_combo.addItems(["C20", "C25", "C30", "C35", "C40"])
        self.concrete_combo.setCurrentText("C25")
        form_layout.addRow("رتبة الخرسانة:", self.concrete_combo)
        
        self.steel_combo = QComboBox()
        self.steel_combo.addItems(["400", "420", "500"])
        self.steel_combo.setCurrentText("420")
        form_layout.addRow("رتبة الحديد:", self.steel_combo)
        
        self.seismic_spin = QSpinBox()
        self.seismic_spin.setRange(1, 4)
        self.seismic_spin.setValue(2)
        form_layout.addRow("المنطقة الزلزالية:", self.seismic_spin)
        
        self.floors_spin = QSpinBox()
        self.floors_spin.setRange(1, 100)
        self.floors_spin.setValue(1)
        form_layout.addRow("عدد الأدوار:", self.floors_spin)
        
        self.input_layout.insertWidget(1, group_box)

        self.summary_group = QGroupBox("ملخص التصميم")
        self.summary_layout = QVBoxLayout(self.summary_group)
        self.summary_label = QLabel("لم يتم التوليد بعد")
        self.summary_label.setWordWrap(True)
        self.summary_layout.addWidget(self.summary_label)
        self.input_layout.insertWidget(2, self.summary_group)

    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure, self.ax = plt.subplots(figsize=(8, 6))
        self.figure.patch.set_facecolor("#0D1117")
        self.ax.set_facecolor("#161B22")
        self.ax.tick_params(colors="#C9D1D9")
        for spine in self.ax.spines.values():
            spine.set_color("#C9D1D9")
            
        self.canvas = FigureCanvas(self.figure)
        self.canvas_layout.addWidget(self.canvas)

    def generate(self):
        """بدء عملية التحليل ورسم النتائج"""
        engine = StructuralEngine(
            building_data=self.building_data,
            soil_capacity=self.soil_capacity_spin.value(),
            concrete_grade=self.concrete_combo.currentText(),
            steel_grade=self.steel_combo.currentText(),
            seismic_zone=self.seismic_spin.value()
        )
        
        engine.floors = self.floors_spin.value()
        self.generated_data = engine.analyze()
        self._update_summary()
        self._draw_results()
        
    def _update_summary(self):
        """تحديث نصوص الملخص بعد التحليل"""
        res = self.generated_data
        concrete = res.get("total_concrete", 0)
        steel = res.get("total_steel", 0)
        shear = res.get("base_shear", 0)
        
        text = f"إجمالي الخرسانة: {concrete:.2f} m³\n"
        text += f"إجمالي الحديد: {steel:.2f} kg\n"
        text += f"قوى القص القاعدية: {shear:.2f} kN\n"
        text += f"عدد الأعمدة: {len(res.get('columns', []))}\n"
        text += f"عدد الجيزان: {len(res.get('beams', []))}\n"
        
        self.summary_label.setText(text)
        
    def _draw_results(self):
        """رسم المخطط الإنشائي"""
        self.ax.clear()
        
        columns = self.generated_data.get("columns", [])
        beams = self.generated_data.get("beams", [])
        
        for b in beams:
            n1 = b["n1"]
            n2 = b["n2"]
            sr = b.get("stress_ratio", 0)
            if sr < 0.5:
                c = "#3FB950" 
            elif sr < 0.8:
                c = "#D29922" 
            else:
                c = "#F85149"
            
            self.ax.plot([n1["x"], n2["x"]], [n1["y"], n2["y"]], color=c, linewidth=4, alpha=0.8)
            
        for c_data in columns:
            x = c_data["x"]
            y = c_data["y"]
            sr = c_data.get("stress_ratio", 0)
            if sr < 0.5:
                c = "#3FB950" 
            elif sr < 0.8:
                c = "#D29922" 
            else:
                c = "#F85149"
            self.ax.plot(x, y, marker='s', color=c, markersize=10)
            
        self.ax.set_title("المخطط الإنشائي (أعمدة وجيزان)", color="#C9D1D9")
        self.ax.set_aspect('equal')
        self.figure.tight_layout()
        self.canvas.draw()
        
    def export_dxf(self, filepath: str):
        """تصدير إلى ملف DXF"""
        pass
        
    def export_ifc(self, filepath: str):
        """تصدير إلى ملف IFC"""
        pass
