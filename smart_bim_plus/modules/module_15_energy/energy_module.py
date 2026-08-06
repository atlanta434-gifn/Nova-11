import sys
import numpy as np
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, 
    QComboBox, QCheckBox, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from modules.base_module import BaseModule
from .energy_engine import EnergyEngine

class EnergyModule(BaseModule):
    """وحدة إدارة الطاقة للمبنى"""
    
    SYSTEM_NUMBER = 15
    SYSTEM_NAME = "Energy Management"
    SYSTEM_NAME_AR = "إدارة الطاقة"
    ICON_NAME = "energy"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = None
        
    def setup_input_panel(self):
        """إعداد واجهة الإدخال"""
        group = QGroupBox("إعدادات الطاقة")
        layout = QGridLayout(group)
        
        layout.addWidget(QLabel("التعرفة ($/kWh):"), 0, 0)
        self.tariff_input = QDoubleSpinBox()
        self.tariff_input.setRange(0.01, 2.0)
        self.tariff_input.setValue(0.15)
        self.tariff_input.setSingleStep(0.01)
        layout.addWidget(self.tariff_input, 0, 1)
        
        layout.addWidget(QLabel("قدرة اللوح الشمسي:"), 1, 0)
        self.panel_combo = QComboBox()
        self.panel_combo.addItems(["300W", "400W", "500W"])
        layout.addWidget(self.panel_combo, 1, 1)
        
        self.battery_check = QCheckBox("نظام بطاريات (Off-Grid / Hybrid)")
        layout.addWidget(self.battery_check, 2, 0, 1, 2)
        
        layout.addWidget(QLabel("نمط الاستخدام:"), 3, 0)
        self.pattern_combo = QComboBox()
        self.pattern_combo.addItems(["سكني", "تجاري"])
        layout.addWidget(self.pattern_combo, 3, 1)
        
        self.input_layout.addWidget(group)
        
        self.summary_group = QGroupBox("ملخص النتائج")
        self.summary_layout = QVBoxLayout(self.summary_group)
        
        self.lbl_consumption = QLabel("الاستهلاك الكلي: -")
        self.lbl_solar = QLabel("الإنتاج الشمسي: -")
        self.lbl_net_cost = QLabel("التكلفة الصافية: -")
        self.lbl_payback = QLabel("فترة الاسترداد: -")
        self.lbl_rating = QLabel("تصنيف الطاقة: -")
        
        self.summary_layout.addWidget(self.lbl_consumption)
        self.summary_layout.addWidget(self.lbl_solar)
        self.summary_layout.addWidget(self.lbl_net_cost)
        self.summary_layout.addWidget(self.lbl_payback)
        self.summary_layout.addWidget(self.lbl_rating)
        
        self.input_layout.addWidget(self.summary_group)
        
    def setup_canvas(self):
        """إعداد لوحات الرسم باستخدام Matplotlib"""
        self.figure = Figure(figsize=(10, 8), facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.canvas_layout.addWidget(self.canvas)
        
        self.ax_profile = self.figure.add_subplot(211)
        self.ax_balance = self.figure.add_subplot(223)
        self.ax_flow = self.figure.add_subplot(224)
        
        self.figure.tight_layout(pad=3.0)
        
    def _apply_dark_theme(self, ax):
        """تطبيق السمة الداكنة على المحاور"""
        ax.set_facecolor("#161B22")
        ax.tick_params(colors="#C9D1D9")
        for spine in ax.spines.values():
            spine.set_color("#30363D")
        ax.xaxis.label.set_color("#C9D1D9")
        ax.yaxis.label.set_color("#C9D1D9")
        ax.title.set_color("#C9D1D9")
        
    def generate(self):
        """توليد البيانات وحساب التحسين ورسم المخططات"""
        self.engine = EnergyEngine(self.building_data)
        
        tariff = self.tariff_input.value()
        panel_wattage = float(self.panel_combo.currentText().replace("W", ""))
        has_battery = self.battery_check.isChecked()
        pattern = self.pattern_combo.currentText()
        
        critical, shiftable, categories = self.engine.calculate_base_loads(pattern)
        
        hours = np.arange(24)
        solar_prod = self.engine.calculate_solar_production(panel_wattage, hours)
        
        opt_shiftable, net_grid, cost_wo_solar, cost_w_solar = self.engine.optimize_load_scheduling(
            critical, shiftable, solar_prod, tariff, has_battery
        )
        
        total_daily_cons = np.sum(critical + opt_shiftable)
        total_daily_solar = np.sum(solar_prod)
        monthly_cons = total_daily_cons * 30
        monthly_solar = total_daily_solar * 30
        monthly_savings = (cost_wo_solar - cost_w_solar) * 30
        
        epi, rating = self.engine.calculate_metrics(total_daily_cons * 365)
        payback = self.engine.calculate_roi(monthly_savings, panel_wattage, has_battery)
        
        self.lbl_consumption.setText(f"الاستهلاك الكلي: {monthly_cons:.2f} kWh/month")
        self.lbl_solar.setText(f"الإنتاج الشمسي: {monthly_solar:.2f} kWh/month")
        self.lbl_net_cost.setText(f"التكلفة الصافية: ${cost_w_solar*30:.2f} / month")
        self.lbl_payback.setText(f"فترة الاسترداد: {payback:.1f} سنة")
        self.lbl_rating.setText(f"تصنيف الطاقة: {rating}")
        
        self.ax_profile.clear()
        self.ax_balance.clear()
        self.ax_flow.clear()
        
        self._apply_dark_theme(self.ax_profile)
        self._apply_dark_theme(self.ax_balance)
        self._apply_dark_theme(self.ax_flow)
        
        # 1. 24-hour profile
        self.ax_profile.bar(hours, critical, label="أساسي", color="#F85149", alpha=0.7)
        self.ax_profile.bar(hours, opt_shiftable, bottom=critical, label="مجدول", color="#D29922", alpha=0.7)
        self.ax_profile.plot(hours, solar_prod, label="إنتاج شمسي", color="#3FB950", linewidth=2)
        self.ax_profile.set_title("المنحنى اليومي للأحمال والإنتاج")
        self.ax_profile.set_xlabel("الساعة")
        self.ax_profile.set_ylabel("الطاقة (kW)")
        self.ax_profile.legend(facecolor="#0D1117", edgecolor="#30363D", labelcolor="#C9D1D9")
        
        # 2. Monthly Balance
        months = np.arange(1, 13)
        monthly_solar_var = monthly_solar * (1 + 0.2 * np.sin(np.pi * (months - 4) / 6))
        self.ax_balance.bar(months - 0.2, [monthly_cons]*12, width=0.4, label="استهلاك", color="#58A6FF")
        self.ax_balance.bar(months + 0.2, monthly_solar_var, width=0.4, label="إنتاج", color="#3FB950")
        self.ax_balance.set_title("توازن الطاقة الشهري")
        self.ax_balance.set_xlabel("الشهر")
        self.ax_balance.set_ylabel("الطاقة (kWh)")
        
        # 3. Categories Pie Chart
        cats = ["تكييف", "إضاءة", "أجهزة", "تسخين", "طبخ"]
        vals = list(categories.values())
        colors = ["#58A6FF", "#3FB950", "#D29922", "#F85149", "#A371F7"]
        wedges, texts, autotexts = self.ax_flow.pie(
            vals, labels=cats, colors=colors, autopct='%1.1f%%', 
            textprops=dict(color="#C9D1D9")
        )
        self.ax_flow.set_title("توزيع استهلاك الطاقة")
        
        self.figure.canvas.draw()
        
    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        pass
        
    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        pass
