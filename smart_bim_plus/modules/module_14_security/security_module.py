"""وحدة واجهة المستخدم لنظام الأمان والمراقبة"""
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Wedge, Rectangle, Circle
from PyQt6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QSpinBox, QDoubleSpinBox, QGroupBox)
from PyQt6.QtCore import Qt

from modules.base_module import BaseModule
from modules.module_14_security.security_engine import SecurityEngine

class SecurityModule(BaseModule):
    """واجهة المستخدم الخاصة بتوزيع كاميرات المراقبة وأنظمة الأمان"""

    SYSTEM_NUMBER = 14
    SYSTEM_NAME = "SecuritySystem"
    SYSTEM_NAME_AR = "نظام الأمان والمراقبة"
    ICON_NAME = "shield"

    def __init__(self, parent=None):
        """تهيئة الوحدة وتحديد الواجهة"""
        super().__init__(parent)
        self.engine = None

    def setup_input_panel(self):
        """إعداد لوحة الإدخال والتحكم"""
        self.settings_group = QGroupBox("إعدادات الأمان")
        layout = QVBoxLayout()

        cam_layout = QHBoxLayout()
        cam_label = QLabel("نوع الكاميرا:")
        self.cam_type = QComboBox()
        self.cam_type.addItems(["dome", "bullet", "ptz"])
        cam_layout.addWidget(cam_label)
        cam_layout.addWidget(self.cam_type)
        layout.addLayout(cam_layout)

        cov_layout = QHBoxLayout()
        cov_label = QLabel("التغطية المطلوبة (%):")
        self.coverage_target = QSpinBox()
        self.coverage_target.setRange(50, 100)
        self.coverage_target.setValue(95)
        cov_layout.addWidget(cov_label)
        cov_layout.addWidget(self.coverage_target)
        layout.addLayout(cov_layout)

        sens_layout = QHBoxLayout()
        sens_label = QLabel("حساسية الحركة:")
        self.sensitivity = QDoubleSpinBox()
        self.sensitivity.setRange(0.1, 1.0)
        self.sensitivity.setValue(0.8)
        self.sensitivity.setSingleStep(0.1)
        sens_layout.addWidget(sens_label)
        sens_layout.addWidget(self.sensitivity)
        layout.addLayout(sens_layout)

        alarm_layout = QHBoxLayout()
        alarm_label = QLabel("نوع الإنذار:")
        self.alarm_type = QComboBox()
        self.alarm_type.addItems(["صوتي", "صامت", "مزدوج"])
        alarm_layout.addWidget(alarm_label)
        alarm_layout.addWidget(self.alarm_type)
        layout.addLayout(alarm_layout)

        self.settings_group.setLayout(layout)
        self.input_layout.insertWidget(1, self.settings_group)

        self.summary_group = QGroupBox("ملخص النظام")
        sum_layout = QVBoxLayout()
        self.summary_label = QLabel("بانتظار التوليد...")
        self.summary_label.setWordWrap(True)
        sum_layout.addWidget(self.summary_label)
        self.summary_group.setLayout(sum_layout)
        self.input_layout.insertWidget(2, self.summary_group)

    def setup_canvas(self):
        """إعداد لوحة الرسم الخاصة بالنتيجة النهائية"""
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.figure.patch.set_facecolor('#0D1117')
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#161B22')
        self.ax.tick_params(colors='#C9D1D9')
        for spine in self.ax.spines.values():
            spine.set_color('#C9D1D9')
        
        self.canvas_layout.addWidget(self.canvas)

    def generate(self):
        """تشغيل خوارزمية الأمان وعرض النتائج"""
        if not self.building_data:
            raise ValueError("بيانات المبنى غير متوفرة")

        self.engine = SecurityEngine(self.building_data)
        
        target_cov = self.coverage_target.value()
        cam = self.cam_type.currentText()
        sens = self.sensitivity.value()

        self.engine.optimize_camera_placement(target_cov, cam)
        self.engine.place_sensors(sens)
        total_cable = self.engine.route_cables()
        zones = self.engine.assess_security_zones()

        self.generated_data = {
            'cameras': self.engine.cameras,
            'sensors': self.engine.sensors,
            'cables': self.engine.cables,
            'cable_length': total_cable,
            'zones': zones
        }

        self._update_plot()
        self._update_summary(total_cable)

    def _update_plot(self):
        """تحديث لوحة الرسم بعد التوليد"""
        self.ax.clear()
        
        # رسم الغرف
        for room in self.building_data.get('rooms', []):
            rx = room.get('position_x', 0)
            ry = room.get('position_y', 0)
            rw = room.get('width', 0)
            rl = room.get('length', 0)
            rect = Rectangle((rx, ry), rw, rl, fill=False, edgecolor='#58A6FF', linewidth=2)
            self.ax.add_patch(rect)
            self.ax.text(rx + rw/2, ry + rl/2, room.get('name', ''), color='#C9D1D9',
                         ha='center', va='center', fontsize=8)

        # رسم التغطية (heatmap)
        if hasattr(self.engine, 'coverage_grid') and hasattr(self.engine, 'grid_size'):
            gs = self.engine.grid_size
            for i in range(self.engine.width):
                for j in range(self.engine.length):
                    if self.engine.coverage_grid[i, j] == 1:
                        self.ax.add_patch(Rectangle((i*gs, j*gs), gs, gs, color='#3FB950', alpha=0.3))

        # رسم الكاميرات ومجال الرؤية
        for cam in self.generated_data.get('cameras', []):
            cx, cy = cam['x'], cam['y']
            fov = cam['fov']
            angle = cam['angle']
            r = cam['radius']
            
            self.ax.plot(cx, cy, 'o', color='#F85149', markersize=6)
            if fov == 360:
                circ = Circle((cx, cy), r, color='#F85149', alpha=0.2)
                self.ax.add_patch(circ)
            else:
                w = Wedge((cx, cy), r, angle, angle + fov, color='#F85149', alpha=0.2)
                self.ax.add_patch(w)

        # رسم المستشعرات
        for sensor in self.generated_data.get('sensors', []):
            sx, sy = sensor['x'], sensor['y']
            color = '#D29922' if sensor['type'] == 'motion' else '#58A6FF'
            self.ax.plot(sx, sy, 's', color=color, markersize=5)

        # رسم مسارات الكابلات
        for cable in self.generated_data.get('cables', []):
            xs = [p[0] for p in cable]
            ys = [p[1] for p in cable]
            self.ax.plot(xs, ys, '--', color='#C9D1D9', linewidth=1, alpha=0.5)

        self.ax.set_aspect('equal')
        self.ax.set_title("مخطط نظام الأمان والمراقبة", color='#C9D1D9')
        self.canvas.draw()

    def _update_summary(self, cable_length: float):
        """تحديث نص الملخص"""
        cams_count = len(self.generated_data.get('cameras', []))
        sensors_count = len(self.generated_data.get('sensors', []))
        
        summary = (
            f"عدد الكاميرات: {cams_count}\n"
            f"عدد المستشعرات: {sensors_count}\n"
            f"إجمالي طول الكابلات: {cable_length:.2f} متر\n"
            f"التكلفة التقديرية: ${(cams_count * 150) + (sensors_count * 50) + (cable_length * 2):.2f}"
        )
        self.summary_label.setText(summary)

    def export_dxf(self, filepath: str):
        """تصدير المخطط إلى ملف DXF"""
        pass

    def export_ifc(self, filepath: str):
        """تصدير المخطط إلى ملف IFC"""
        pass
