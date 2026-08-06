from PyQt6.QtWidgets import (QVBoxLayout, QFormLayout, QComboBox, 
                               QDoubleSpinBox, QGroupBox, QLabel, QScrollArea, QWidget)
from PyQt6.QtCore import Qt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, Circle, Polygon
from modules.base_module import BaseModule
from .pool_engine import PoolEngine

class PoolModule(BaseModule):
    """وحدة تصميم المسبح الذكي"""

    SYSTEM_NUMBER = 12
    SYSTEM_NAME = "Smart Pool"
    SYSTEM_NAME_AR = "المسبح الذكي"
    ICON_NAME = "pool"

    def __init__(self, parent=None):
        """تهيئة وحدة المسبح الذكي"""
        self.engine = PoolEngine()
        super().__init__(parent)

    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        
        group = QGroupBox("مواصفات المسبح")
        form = QFormLayout()
        
        self.pool_type_combo = QComboBox()
        self.pool_type_combo.addItems(["مستطيل", "حرف L", "كلوي", "انفنيتي"])
        form.addRow("نوع المسبح:", self.pool_type_combo)
        
        self.area_spin = QDoubleSpinBox()
        self.area_spin.setRange(10.0, 500.0)
        self.area_spin.setValue(50.0)
        self.area_spin.setSuffix(" م²")
        form.addRow("المساحة المطلوبة:", self.area_spin)
        
        self.depth_combo = QComboBox()
        self.depth_combo.addItems(["متوسط", "ضحل", "عميق"])
        form.addRow("العمق:", self.depth_combo)
        
        self.heating_combo = QComboBox()
        self.heating_combo.addItems(["بدون تسخين", "سخان كهربائي", "سخان غاز", "طاقة شمسية"])
        form.addRow("نظام التسخين:", self.heating_combo)
        
        self.cover_combo = QComboBox()
        self.cover_combo.addItems(["بدون غطاء", "غطاء حراري", "غطاء آلي"])
        form.addRow("نوع الغطاء:", self.cover_combo)
        
        group.setLayout(form)
        layout.addWidget(group)
        
        self.results_group = QGroupBox("ملخص النتائج")
        self.results_layout = QVBoxLayout()
        self.results_label = QLabel("قم بالتوليد لعرض النتائج")
        self.results_label.setWordWrap(True)
        self.results_layout.addWidget(self.results_label)
        self.results_group.setLayout(self.results_layout)
        layout.addWidget(self.results_group)
        
        layout.addStretch()
        scroll.setWidget(content)
        self.input_layout.insertWidget(1, scroll)

    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure = Figure(figsize=(8, 6), facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.canvas_layout.addWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor("#161B22")
        self.ax.tick_params(colors="#C9D1D9")
        for spine in self.ax.spines.values():
            spine.set_color("#C9D1D9")

    def generate(self):
        """توليد بيانات النظام"""
        area = self.area_spin.value()
        p_type = self.pool_type_combo.currentText()
        d_type = self.depth_combo.currentText()
        h_type = self.heating_combo.currentText()
        c_type = self.cover_combo.currentText()
        
        self.generated_data = self.engine.run_full_analysis(area, p_type, d_type, h_type, c_type)
        self._update_results_ui()
        self._plot_pool()

    def _update_results_ui(self):
        """تحديث واجهة النتائج"""
        d = self.generated_data
        dims = d["dimensions"]
        filt = d["filtration"]
        heat = d["heating"]
        chem = d["chemical"]
        cost = d["costs"]
        
        summary = (
            f"الحجم الكلي: {dims['volume']:.1f} م³\n"
            f"معدل التدفق للمضخة: {filt['flow_rate_gpm']:.1f} GPM\n"
            f"قطر الفلتر المطلوب: {filt['filter_diameter_m']*100:.1f} سم\n"
            f"السخان المطلوب: {heat['required_heater_btu']/1000:.1f} kBTU\n"
            f"الكلور اليومي: {chem['chlorine_daily_grams']:.1f} جرام\n"
            f"التكلفة السنوية التقديرية: {cost['total_annual_cost']:.0f} دولار\n"
        )
        self.results_label.setText(summary)

    def _plot_pool(self):
        """رسم المسبح على اللوحة"""
        self.ax.clear()
        d = self.generated_data
        dims = d["dimensions"]
        p_type = self.pool_type_combo.currentText()
        
        if p_type == "مستطيل":
            w = dims["width"]
            l = dims["length"]
            pool = Rectangle((0, 0), w, l, facecolor="#58A6FF", edgecolor="#C9D1D9", alpha=0.7)
            self.ax.add_patch(pool)
            self.ax.set_xlim(-2, w + 2)
            self.ax.set_ylim(-2, l + 2)
            
            self.ax.plot([-1, -1, w/2], [-1, l/2, l/2], color="#F85149", linestyle="--", label="أنابيب السحب")
            self.ax.plot([w+1, w+1, w/2], [l+1, l/2, l/2], color="#3FB950", linestyle="-.", label="أنابيب الدفع")
            
        elif p_type == "حرف L":
            w = dims["main_width"]
            l = dims["main_length"]
            lw = dims["L_width"]
            poly = Polygon([[0,0], [w+lw,0], [w+lw,lw], [w,lw], [w,l], [0,l]], facecolor="#58A6FF", edgecolor="#C9D1D9", alpha=0.7)
            self.ax.add_patch(poly)
            self.ax.set_xlim(-2, w + lw + 2)
            self.ax.set_ylim(-2, l + 2)
            
        elif p_type in ["كلوي", "انفنيتي"]:
            w = dims["width"]
            l = dims["length"]
            r = dims["radius"]
            c1 = Circle((w/2, r), r, facecolor="#58A6FF", edgecolor="#C9D1D9", alpha=0.7)
            c2 = Circle((w/2, l-r), r, facecolor="#58A6FF", edgecolor="#C9D1D9", alpha=0.7)
            rect = Rectangle((w/2 - r, r), 2*r, l - 2*r, facecolor="#58A6FF", edgecolor="none", alpha=0.7)
            self.ax.add_patch(c1)
            self.ax.add_patch(c2)
            self.ax.add_patch(rect)
            self.ax.set_xlim(-r, w + r)
            self.ax.set_ylim(-r, l + r)
            
        # إضافة منطقة المعدات
        equip_room = Rectangle((-1.5, -1.5), 1, 1, facecolor="#D29922", edgecolor="#C9D1D9")
        self.ax.add_patch(equip_room)
        self.ax.text(-1, -1, "غرفة المعدات", color="#C9D1D9", ha="center", va="center")
            
        self.ax.set_aspect('equal')
        self.ax.set_title("مخطط المسبح الذكي", color="#C9D1D9")
        self.ax.legend(loc="upper right", facecolor="#161B22", edgecolor="#C9D1D9", labelcolor="#C9D1D9")
        self.canvas.draw()

    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        pass

    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        pass
