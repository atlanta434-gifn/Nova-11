from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal


class BaseModule(QWidget):
    """الوحدة الأساسية — كل نظام من أنظمة المبنى يرث من هذا الصنف"""

    generation_started = pyqtSignal()
    generation_finished = pyqtSignal(bool)
    data_generated = pyqtSignal(str, dict)
    progress_updated = pyqtSignal(int)
    log_message = pyqtSignal(str)

    SYSTEM_NUMBER = 0
    SYSTEM_NAME = "Base Module"
    SYSTEM_NAME_AR = "وحدة أساسية"
    ICON_NAME = "module"

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.building_data: Dict[str, Any] = {}
        self.generated_data: Dict[str, Any] = {}
        self.is_generated = False
        self._setup_base_ui()

    def _setup_base_ui(self):
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.input_container = QWidget()
        self.input_layout = QVBoxLayout(self.input_container)
        self.input_layout.setContentsMargins(16, 16, 16, 16)
        self.input_layout.setSpacing(12)

        self.input_scroll_area = __import__('PyQt6.QtWidgets', fromlist=['QScrollArea']).QScrollArea()
        self.input_scroll_area.setWidget(self.input_container)
        self.input_scroll_area.setWidgetResizable(True)
        self.input_scroll_area.setFixedWidth(360)
        self.input_scroll_area.setObjectName("card")
        self.input_scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        header = QLabel(self.SYSTEM_NAME_AR)
        header.setObjectName("titleLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_layout.addWidget(header)

        self.setup_input_panel()

        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("توليد")
        self.generate_btn.setObjectName("primaryButton")
        self.generate_btn.clicked.connect(self._on_generate)
        btn_layout.addWidget(self.generate_btn)
        self.input_layout.addLayout(btn_layout)

        export_layout = QHBoxLayout()
        self.export_dxf_btn = QPushButton("DXF تصدير")
        self.export_dxf_btn.clicked.connect(self._on_export_dxf)
        self.export_dxf_btn.setEnabled(False)
        export_layout.addWidget(self.export_dxf_btn)

        self.export_ifc_btn = QPushButton("IFC تصدير")
        self.export_ifc_btn.clicked.connect(self._on_export_ifc)
        self.export_ifc_btn.setEnabled(False)
        export_layout.addWidget(self.export_ifc_btn)

        self.export_pdf_btn = QPushButton("PDF تصدير")
        self.export_pdf_btn.clicked.connect(self._on_export_pdf)
        self.export_pdf_btn.setEnabled(False)
        export_layout.addWidget(self.export_pdf_btn)

        self.input_layout.addLayout(export_layout)
        self.input_layout.addStretch()

        self.canvas_container = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas_layout.setContentsMargins(8, 8, 8, 8)
        self.setup_canvas()

        self.main_layout.addWidget(self.input_scroll_area)
        self.main_layout.addWidget(self.canvas_container, 1)

    def _on_generate(self):
        self.generation_started.emit()
        self.log_message.emit(f"بدء توليد {self.SYSTEM_NAME_AR}...")
        try:
            self.generate()
            self.is_generated = True
            self.export_dxf_btn.setEnabled(True)
            self.export_ifc_btn.setEnabled(True)
            self.export_pdf_btn.setEnabled(True)
            self.generation_finished.emit(True)
            if self.generated_data:
                self.data_generated.emit(str(self.SYSTEM_NUMBER).zfill(2), self.generated_data)
            self.log_message.emit(f"تم توليد {self.SYSTEM_NAME_AR} بنجاح")
        except Exception as e:
            self.generation_finished.emit(False)
            self.log_message.emit(f"خطأ في توليد {self.SYSTEM_NAME_AR}: {str(e)}")

    def _on_export_dxf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير DXF", f"{self.SYSTEM_NAME}.dxf", "DXF Files (*.dxf)"
        )
        if path:
            try:
                self.export_dxf(path)
                self.log_message.emit(f"تم تصدير DXF: {path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل التصدير: {str(e)}")

    def _on_export_ifc(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير IFC", f"{self.SYSTEM_NAME}.ifc", "IFC Files (*.ifc)"
        )
        if path:
            try:
                self.export_ifc(path)
                self.log_message.emit(f"تم تصدير IFC: {path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل التصدير: {str(e)}")

    def _on_export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير PDF", f"{self.SYSTEM_NAME}.pdf", "PDF Files (*.pdf)"
        )
        if path:
            try:
                self.export_pdf(path)
                self.log_message.emit(f"تم تصدير PDF: {path}")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل التصدير: {str(e)}")

    def set_building_data(self, data: Dict[str, Any]):
        self.building_data = data

    @abstractmethod
    def setup_input_panel(self):
        """إعداد لوحة الإدخال"""
        pass

    @abstractmethod
    def setup_canvas(self):
        """إعداد لوحة الرسم"""
        pass

    @abstractmethod
    def generate(self):
        """توليد بيانات النظام"""
        pass

    @abstractmethod
    def export_dxf(self, filepath: str):
        """تصدير إلى DXF"""
        pass

    @abstractmethod
    def export_ifc(self, filepath: str):
        """تصدير إلى IFC"""
        pass

    def export_pdf(self, filepath: str):
        """تصدير إلى PDF — اختياري"""
        pass
