import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QSpinBox, QDoubleSpinBox, QDateEdit, QFormLayout, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, QDate

from modules.base_module import BaseModule
from .project_engine import ProjectEngine

class ProjectManagementModule(BaseModule):
    """وحدة إدارة المشاريع والمسار الحرج"""

    SYSTEM_NUMBER = 19
    SYSTEM_NAME = "Project Management"
    SYSTEM_NAME_AR = "إدارة المشاريع"
    ICON_NAME = "project"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = None
        self.canvas = None
        self.figure = None
        self.axes = None

    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        group_box = QGroupBox("إعدادات المشروع")
        layout = QFormLayout(group_box)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        layout.addRow(QLabel("تاريخ البدء:"), self.start_date_edit)

        self.b_type_combo = QComboBox()
        self.b_type_combo.addItems(["سكني", "تجاري", "صناعي", "مختلط"])
        layout.addRow(QLabel("نوع المبنى:"), self.b_type_combo)

        self.complexity_combo = QComboBox()
        self.complexity_combo.addItems(["بسيط", "متوسط", "معقد"])
        layout.addRow(QLabel("تعقيد المشروع:"), self.complexity_combo)

        self.workers_spin = QSpinBox()
        self.workers_spin.setRange(5, 500)
        self.workers_spin.setValue(20)
        layout.addRow(QLabel("عدد العمال:"), self.workers_spin)

        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(4, 24)
        self.hours_spin.setValue(8)
        layout.addRow(QLabel("ساعات العمل/اليوم:"), self.hours_spin)

        self.input_layout.addWidget(group_box)

        self.summary_box = QGroupBox("ملخص المشروع")
        self.summary_layout = QVBoxLayout(self.summary_box)
        
        self.duration_label = QLabel("المدة الكلية: -")
        self.cost_label = QLabel("التكلفة التقديرية: -")
        self.p50_label = QLabel("احتمالية 50%: -")
        self.p90_label = QLabel("احتمالية 90%: -")
        
        self.summary_layout.addWidget(self.duration_label)
        self.summary_layout.addWidget(self.cost_label)
        self.summary_layout.addWidget(self.p50_label)
        self.summary_layout.addWidget(self.p90_label)
        
        self.input_layout.addWidget(self.summary_box)

    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        self.figure = Figure(figsize=(10, 8), facecolor="#0D1117")
        self.canvas = FigureCanvas(self.figure)
        self.canvas_layout.addWidget(self.canvas)
        
        self.axes = self.figure.add_subplot(111)
        self.axes.set_facecolor("#161B22")
        self.axes.tick_params(colors="#C9D1D9")
        for spine in self.axes.spines.values():
            spine.set_color("#C9D1D9")

    def generate(self):
        """توليد بيانات النظام"""
        self.engine = ProjectEngine(self.building_data)
        
        complexity = self.complexity_combo.currentText()
        comp_factor = 1.0
        if complexity == "بسيط":
            comp_factor = 0.8
        elif complexity == "معقد":
            comp_factor = 1.3
            
        for act in self.engine.activities.values():
            act.likely_dur *= comp_factor
            act.min_dur *= comp_factor
            act.max_dur *= comp_factor
            
        self.engine.calculate_cpm()
        self.engine.run_monte_carlo(1000)
        
        self.duration_label.setText(f"المدة الكلية: {self.engine.project_duration:.1f} يوم")
        self.cost_label.setText(f"التكلفة التقديرية: {self.engine.total_cost:,.2f}")
        self.p50_label.setText(f"احتمالية 50%: {self.engine.p50:.1f} يوم")
        self.p90_label.setText(f"احتمالية 90%: {self.engine.p90:.1f} يوم")
        
        self._plot_gantt()

    def _plot_gantt(self):
        """رسم مخطط جانت"""
        self.axes.clear()
        self.axes.set_facecolor("#161B22")
        
        acts = list(self.engine.activities.values())
        acts.sort(key=lambda x: x.es)
        
        y_ticks = []
        y_labels = []
        
        for i, act in enumerate(acts):
            y_pos = len(acts) - i
            y_ticks.append(y_pos)
            y_labels.append(f"{act.id}: {act.name}")
            
            color = "#F85149" if act.is_critical else "#58A6FF"
            
            self.axes.barh(y_pos, act.duration, left=act.es, height=0.4, color=color, alpha=0.8)
            
            if act.tf > 0:
                self.axes.barh(y_pos, act.tf, left=act.ef, height=0.2, color="#3FB950", alpha=0.5)
                
            for succ_id in act.successors:
                succ = self.engine.activities[succ_id]
                succ_idx = acts.index(succ)
                succ_y_pos = len(acts) - succ_idx
                
                self.axes.annotate(
                    "",
                    xy=(succ.es, succ_y_pos + 0.2),
                    xytext=(act.ef, y_pos - 0.2),
                    arrowprops=dict(arrowstyle="->", color="#C9D1D9", lw=1, alpha=0.5)
                )
                
        self.axes.set_yticks(y_ticks)
        self.axes.set_yticklabels(y_labels, color="#C9D1D9", fontsize=8)
        self.axes.set_xlabel("الأيام", color="#C9D1D9")
        self.axes.set_title("مخطط جانت - المسار الحرج", color="#C9D1D9")
        
        self.figure.tight_layout()
        self.canvas.draw()

    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        pass

    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        pass
