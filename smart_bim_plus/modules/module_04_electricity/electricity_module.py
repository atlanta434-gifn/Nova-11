import os
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QSpinBox,
    QDoubleSpinBox, QLabel, QPushButton, QMessageBox, QFileDialog, QComboBox
)
from PyQt6.QtCore import Qt

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

from modules.base_module import BaseModule
from modules.module_04_electricity.load_calculator import LoadCalculator
from modules.module_04_electricity.circuit_router import CircuitRouter
from modules.module_04_electricity.diagram_generator import DiagramGenerator


class ElectricityModule(BaseModule):
    """وحدة الأنظمة الكهربائية والطاقة — النظام الرابع
    حساب الأحمال، توجيه الدوائر، الألواح الشمسية، ورسم المخطط الخطي"""

    SYSTEM_NUMBER = 4
    SYSTEM_NAME = "Electricity & Energy"
    SYSTEM_NAME_AR = "الكهرباء والطاقة"
    ICON_NAME = "electricity"

    def __init__(self, parent: Optional[QWidget] = None):
        self.calculator = LoadCalculator()
        self.router = CircuitRouter()
        self.diagrammer = DiagramGenerator()
        self.figure = None
        self.canvas = None
        self.electrical_data = {}
        super().__init__(parent)

    def setup_input_panel(self):
        """إعداد لوحة إدخال أحمال الكهرباء والطاقة"""
        load_group = QGroupBox("إعدادات الأحمال والطاقة")
        load_layout = QFormLayout(load_group)

        self.solar_percent_spin = QSpinBox()
        self.solar_percent_spin.setRange(0, 100)
        self.solar_percent_spin.setValue(20)
        self.solar_percent_spin.setSuffix("%")
        load_layout.addRow("نسبة الطاقة الشمسية:", self.solar_percent_spin)

        self.voltage_combo = QComboBox()
        self.voltage_combo.addItems(["230V / 400V (3-Phase)", "110V / 220V (Split-Phase)"])
        load_layout.addRow("نظام الجهد:", self.voltage_combo)

        self.input_layout.addWidget(load_group)

        self.summary_table = QTableWidget(0, 2)
        self.summary_table.setHorizontalHeaderLabels(["الخاصية", "القيمة"])
        self.summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.summary_table.setFixedHeight(250)
        self.input_layout.addWidget(self.summary_table)

    def setup_canvas(self):
        """إعداد لوحة رسم المخطط الخطي الفردي (SLD)"""
        self.figure = Figure(figsize=(10, 8), facecolor="#0D1117")
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas_layout.addWidget(self.canvas)
        self._draw_empty_canvas()

    def _draw_empty_canvas(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#161B22")
        ax.axis("off")
        ax.text(0.5, 0.5, "المخطط الخطي الفردي للكهرباء (SLD)",
                ha="center", va="center", fontsize=14,
                color="#8B949E", fontfamily="sans-serif",
                transform=ax.transAxes)
        self.canvas.draw()

    def generate(self):
        """توليد الأحمال والدوائر والمخطط"""
        rooms = self.building_data.get("rooms", [])
        if not rooms:
            rooms = [
                {"name": "غرفة معيشة", "room_type": "living_room", "area": 25.0},
                {"name": "مطبخ", "room_type": "kitchen", "area": 16.0},
                {"name": "غرفة نوم 1", "room_type": "master_bedroom", "area": 20.0},
                {"name": "حمام", "room_type": "bathroom", "area": 6.0},
            ]
            self.log_message.emit("لا توجد بيانات غرف من الوحدة السابقة، استخدام غرف افتراضية")

        solar_pct = self.solar_percent_spin.value()
        self.electrical_data = self.calculator.calculate_building_load(rooms, solar_pct)
        
        circuits_data = self.router.route_circuits(
            self.electrical_data["room_loads"], panel_position=(0, 0)
        )
        self.electrical_data["circuits_data"] = circuits_data

        self._update_summary_table()
        self.diagrammer.generate(self.electrical_data, self.figure)
        self.canvas.draw()
        self.progress_updated.emit(100)

    def _update_summary_table(self):
        self.summary_table.setRowCount(0)
        data = [
            ("الحمل الكلي (Watt)", f"{self.electrical_data.get('total_installed_watt', 0):.0f}"),
            ("حمل التصميم (Watt)", f"{self.electrical_data.get('design_watt', 0):.0f}"),
            ("التيار الكلي (Amp)", f"{self.electrical_data.get('design_current', 0):.1f}"),
            ("القاطع الرئيسي (Amp)", f"{self.electrical_data.get('main_breaker_amp', 0)}"),
            ("عدد الدوائر الفرعية", f"{self.electrical_data.get('circuits_data', {}).get('total_circuits', 0)}"),
            ("الألواح الشمسية المقترحة", f"{self.electrical_data.get('solar_panels_count', 0)}"),
            ("قدرة الطاقة الشمسية (W)", f"{self.electrical_data.get('solar_capacity_watt', 0):.0f}"),
            ("نوع الطور (Phase)", self.electrical_data.get('phase_type', '')),
        ]
        
        for row, (key, val) in enumerate(data):
            self.summary_table.insertRow(row)
            self.summary_table.setItem(row, 0, QTableWidgetItem(key))
            self.summary_table.setItem(row, 1, QTableWidgetItem(val))

    def export_pdf(self, filepath: str):
        """تصدير جدول الأحمال والمخطط إلى PDF باستخدام ReportLab و Matplotlib"""
        if not self.electrical_data:
            raise ValueError("لا توجد بيانات لتصديرها")
            
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import tempfile

            doc = SimpleDocTemplate(filepath, pagesize=A4)
            elements = []
            
            # Since standard fonts might not support Arabic without complex setup,
            # we'll use a basic approach that works for English/numbers fallback
            # In a real app, you would load an Arabic TTF font here
            styles = getSampleStyleSheet()
            title_style = styles['Heading1']
            title_style.alignment = 1  # Center
            
            elements.append(Paragraph("NOVA Electrical Load Schedule", title_style))
            elements.append(Spacer(1, 20))
            
            # Summary Table
            summary_data = [["Property", "Value"]]
            summary_data.append(["Total Installed Load (W)", f"{self.electrical_data.get('total_installed_watt', 0):.0f}"])
            summary_data.append(["Design Load (W)", f"{self.electrical_data.get('design_watt', 0):.0f}"])
            summary_data.append(["Main Breaker (A)", f"{self.electrical_data.get('main_breaker_amp', 0)}"])
            summary_data.append(["Solar Capacity (W)", f"{self.electrical_data.get('solar_capacity_watt', 0):.0f}"])
            
            t_summary = Table(summary_data, colWidths=[200, 200])
            t_summary.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F6FEB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#161B22')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#C9D1D9')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#30363D'))
            ]))
            elements.append(t_summary)
            elements.append(Spacer(1, 30))
            
            # Circuits Table
            elements.append(Paragraph("Circuit Details", styles['Heading2']))
            elements.append(Spacer(1, 10))
            
            circuits_data = [["Circuit ID", "Type", "Load (W)", "Wire (mm2)", "Breaker (A)"]]
            for c in self.electrical_data.get("circuits_data", {}).get("circuits", []):
                circuits_data.append([
                    str(c.get("id")),
                    c.get("type", ""),
                    f"{c.get('load_w', 0):.0f}",
                    str(c.get("wire_mm2", "")),
                    str(c.get("breaker", ""))
                ])
                
            t_circuits = Table(circuits_data, colWidths=[60, 100, 80, 80, 80])
            t_circuits.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F6FEB')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#161B22')),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#C9D1D9')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#30363D'))
            ]))
            elements.append(t_circuits)
            elements.append(Spacer(1, 30))
            
            # Plot
            temp_img = tempfile.mktemp(suffix='.png')
            self.figure.savefig(temp_img, format='png', dpi=150, facecolor='#0D1117', edgecolor='none')
            elements.append(Image(temp_img, width=400, height=300))
            
            doc.build(elements)
            
            try:
                os.remove(temp_img)
            except:
                pass
                
        except ImportError:
            raise Exception("ReportLab is not installed or failed to import")

    def export_dxf(self, filepath: str):
        raise NotImplementedError("تصدير DXF للكهرباء غير مدعوم في هذه النسخة")

    def export_ifc(self, filepath: str):
        raise NotImplementedError("تصدير IFC للكهرباء غير مدعوم في هذه النسخة")
