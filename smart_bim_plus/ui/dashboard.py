from typing import Optional, Callable
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt


class StatCard(QFrame):
    def __init__(self, title: str, value: str, icon: str = "",
                 color: str = "#58A6FF", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("statsCard")
        self.setFixedSize(220, 120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(title)
        title_label.setObjectName("subtitleLabel")
        title_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName("titleLabel")
        value_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(value_label)


class Dashboard(QWidget):
    """لوحة القيادة الرئيسية"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.new_project_cb: Optional[Callable] = None
        self.open_project_cb: Optional[Callable] = None
        self.drone_connect_cb: Optional[Callable] = None
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)

        header = QLabel("مرحباً بك في NOVA")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #FFFFFF;")
        main_layout.addWidget(header)

        stats_layout = QHBoxLayout()
        self.proj_card = StatCard("المشاريع النشطة", "0", color="#3FB950")
        self.area_card = StatCard("إجمالي المساحات المصممة", "0 م²", color="#58A6FF")
        self.sys_card = StatCard("الأنظمة المولدة", "0", color="#D29922")
        self.drone_card = StatCard("رحلات الدرون", "0", color="#F85149")

        stats_layout.addWidget(self.proj_card)
        stats_layout.addWidget(self.area_card)
        stats_layout.addWidget(self.sys_card)
        stats_layout.addWidget(self.drone_card)
        stats_layout.addStretch()
        main_layout.addLayout(stats_layout)

        actions_group = QFrame()
        actions_group.setObjectName("card")
        actions_layout = QVBoxLayout(actions_group)

        actions_title = QLabel("إجراءات سريعة")
        actions_title.setObjectName("titleLabel")
        actions_layout.addWidget(actions_title)

        btns_layout = QHBoxLayout()
        btns_layout.setSpacing(20)

        new_btn = QPushButton("مشروع جديد")
        new_btn.setObjectName("primaryButton")
        new_btn.setFixedSize(200, 50)
        new_btn.clicked.connect(lambda: self.new_project_cb and self.new_project_cb())

        open_btn = QPushButton("فتح مشروع")
        open_btn.setFixedSize(200, 50)
        open_btn.clicked.connect(lambda: self.open_project_cb and self.open_project_cb())

        drone_btn = QPushButton("اتصال بالدرون")
        drone_btn.setFixedSize(200, 50)
        drone_btn.clicked.connect(lambda: self.drone_connect_cb and self.drone_connect_cb())

        btns_layout.addWidget(new_btn)
        btns_layout.addWidget(open_btn)
        btns_layout.addWidget(drone_btn)
        btns_layout.addStretch()

        actions_layout.addLayout(btns_layout)
        main_layout.addWidget(actions_group)

        recent_group = QFrame()
        recent_group.setObjectName("card")
        recent_layout = QVBoxLayout(recent_group)

        recent_title = QLabel("المشاريع الأخيرة")
        recent_title.setObjectName("titleLabel")
        recent_layout.addWidget(recent_title)

        empty_label = QLabel("لا توجد مشاريع سابقة")
        empty_label.setObjectName("subtitleLabel")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setContentsMargins(0, 40, 0, 40)
        recent_layout.addWidget(empty_label)

        main_layout.addWidget(recent_group)
        main_layout.addStretch()

    def update_stats(self, stats: dict):
        self.proj_card.findChild(QLabel, "titleLabel").setText(str(stats.get("projects", 0)))
        self.area_card.findChild(QLabel, "titleLabel").setText(f"{stats.get('total_area', 0):.0f} م²")
        self.sys_card.findChild(QLabel, "titleLabel").setText(str(stats.get("systems", 0)))
        self.drone_card.findChild(QLabel, "titleLabel").setText(str(stats.get("drone_flights", 0)))
