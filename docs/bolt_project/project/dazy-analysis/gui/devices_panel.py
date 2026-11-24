"""gui/devices_panel.py — DAZY Device Hub & Multi-Device Privacy Dashboard."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)
from core.devices.device_hub import device_hub
from core.devices.models import DeviceType, TrustLevel
from core.devices.nearby_discovery import nearby_discovery
from core.devices.pairing import pairing_manager
from gui.overlays import _HudOverlay
from gui.style import hud_font, px_font
from gui.theme import C


class DevicesPanel(_HudOverlay):
    """Overlay panel to manage connected devices, nearby discovery, and cross-device privacy."""

    device_selected = pyqtSignal(str)
    _OW = 560

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            DevicesPanel {{
                background: rgba(0, 8, 14, 250);
                border: 1px solid {C.BORDER_B};
                border-radius: 6px;
            }}
        """)
        self.setFixedWidth(self._OW)

        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(20, 16, 20, 16)
        self._lay.setSpacing(10)

        # Header
        title = QLabel("📱  DAZY DEVICE HUB & ECOSYSTEM")
        title.setFont(hud_font(11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.WHITE}; background: transparent;")
        self._lay.addWidget(title)

        sub = QLabel("Multi-Device Monitoring, Secure Pairing & Privacy Controls")
        sub.setFont(px_font(9, QFont.Weight.Normal))
        sub.setStyleSheet(f"color: {C.PRI_DIM}; background: transparent;")
        self._lay.addWidget(sub)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {C.BORDER}; margin: 4px 0;")
        self._lay.addWidget(sep)

        # Local Device Status Row
        local_dev = device_hub.get_local_device()
        batt_str = f"{int(local_dev.battery_level)}%" if local_dev.battery_level is not None else "AC Power"
        if local_dev.is_charging:
            batt_str += " ⚡"

        local_row = QHBoxLayout()
        local_lbl = QLabel(f"THIS DEVICE: {local_dev.friendly_name}  ·  BATTERY: {batt_str}")
        local_lbl.setFont(hud_font(8, QFont.Weight.Bold))
        local_lbl.setStyleSheet(f"color: {C.GREEN}; background: transparent;")
        local_row.addWidget(local_lbl)

        pair_btn = QPushButton("+ PAIR NEW DEVICE")
        pair_btn.setFont(hud_font(8, QFont.Weight.Bold))
        pair_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pair_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PANEL2}; color: {C.ACC2}; border: 1px solid {C.ACC2};
                border-radius: 3px; padding: 4px 8px;
            }}
            QPushButton:hover {{ background: {C.ACC2}; color: #000; }}
        """)
        pair_btn.clicked.connect(self._create_pairing_code)
        local_row.addWidget(pair_btn)
        self._lay.addLayout(local_row)

        # Enrolled Devices List
        enrolled_lbl = QLabel("ENROLLED & TRUSTED DEVICES:")
        enrolled_lbl.setFont(hud_font(8, QFont.Weight.Bold))
        enrolled_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        self._lay.addWidget(enrolled_lbl)

        self._devices_scroll = QScrollArea()
        self._devices_scroll.setWidgetResizable(True)
        self._devices_scroll.setFixedHeight(120)
        self._devices_scroll.setStyleSheet(f"background: {C.PANEL}; border: 1px solid {C.BORDER}; border-radius: 4px;")

        self._devices_container = QWidget()
        self._devices_layout = QVBoxLayout(self._devices_container)
        self._devices_layout.setContentsMargins(10, 8, 10, 8)
        self._devices_layout.setSpacing(6)
        self._devices_scroll.setWidget(self._devices_container)
        self._lay.addWidget(self._devices_scroll)

        # Nearby Discovery Section
        nearby_hdr = QHBoxLayout()
        nearby_lbl = QLabel("📡  DAZY NEARBY DISCOVERY:")
        nearby_lbl.setFont(hud_font(8, QFont.Weight.Bold))
        nearby_lbl.setStyleSheet(f"color: {C.PRI}; background: transparent;")
        nearby_hdr.addWidget(nearby_lbl)

        self._toggle_discovery_btn = QPushButton("NEARBY: ON")
        self._toggle_discovery_btn.setFont(hud_font(7, QFont.Weight.Bold))
        self._toggle_discovery_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_discovery_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PANEL2}; color: {C.GREEN}; border: 1px solid {C.BORDER};
                border-radius: 3px; padding: 2px 6px;
            }}
        """)
        self._toggle_discovery_btn.clicked.connect(self._toggle_nearby)
        nearby_hdr.addWidget(self._toggle_discovery_btn)
        self._lay.addLayout(nearby_hdr)

        self._nearby_info = QLabel("Listening for DAZY mobile companion beacons over LAN / Bluetooth.")
        self._nearby_info.setFont(px_font(9, QFont.Weight.Normal))
        self._nearby_info.setStyleSheet(f"color: {C.TEXT}; background: #00121d; border: 1px solid {C.BORDER}; border-radius: 4px; padding: 8px;")
        self._nearby_info.setWordWrap(True)
        self._lay.addWidget(self._nearby_info)

        # Pairing feedback label
        self._pair_feedback = QLabel("")
        self._pair_feedback.setFont(hud_font(8, QFont.Weight.Bold))
        self._pair_feedback.setStyleSheet(f"color: {C.ACC2}; background: transparent;")
        self._lay.addWidget(self._pair_feedback)

        # Close button
        close_btn = QPushButton("CLOSE")
        close_btn.setFixedHeight(30)
        close_btn.setFont(hud_font(9))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {C.TEXT_MED};
                border: 1px solid {C.BORDER}; border-radius: 3px; }}
            QPushButton:hover {{ color: {C.TEXT}; border-color: {C.BORDER_B}; }}
        """)
        close_btn.clicked.connect(self.hide)
        self._lay.addWidget(close_btn)

        self._render_devices()
        self.adjustSize()

    def _render_devices(self):
        # Clear existing rows
        while self._devices_layout.count():
            item = self._devices_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        devices = device_hub.get_all_devices()
        for d in devices:
            row = QHBoxLayout()
            icon = "💻" if d.device_type == DeviceType.DESKTOP_WINDOWS else "📱"
            lbl = QLabel(f"{icon} {d.friendly_name}  [{d.status.value.upper()}]")
            lbl.setFont(hud_font(8, QFont.Weight.Normal))
            lbl.setStyleSheet(f"color: {C.TEXT};")
            row.addWidget(lbl)

            st_lbl = QLabel(d.trust_level.value.upper())
            st_lbl.setFont(hud_font(8, QFont.Weight.Bold))
            st_color = C.GREEN if d.trust_level == TrustLevel.PAIRED_TRUSTED else C.RED
            st_lbl.setStyleSheet(f"color: {st_color};")
            row.addWidget(st_lbl)

            self._devices_layout.addLayout(row)

    def _create_pairing_code(self):
        session = pairing_manager.create_pairing_request(
            device_id="android_companion_demo",
            device_name="Tarik's Android Phone",
            device_type=DeviceType.MOBILE_ANDROID,
        )
        self._pair_feedback.setText(f"PAIRING CODE: [ {session.one_time_code} ]  (Expires in 5 mins)")

    def _toggle_nearby(self):
        now_enabled = not nearby_discovery.master_enabled
        nearby_discovery.toggle_master_discovery(now_enabled)
        if now_enabled:
            self._toggle_discovery_btn.setText("NEARBY: ON")
            self._toggle_discovery_btn.setStyleSheet(f"background: {C.PANEL2}; color: {C.GREEN}; border: 1px solid {C.BORDER};")
            self._nearby_info.setText("Nearby Discovery active. Detecting nearby DAZY devices.")
        else:
            self._toggle_discovery_btn.setText("NEARBY: OFF")
            self._toggle_discovery_btn.setStyleSheet(f"background: {C.PANEL2}; color: {C.RED}; border: 1px solid {C.BORDER};")
            self._nearby_info.setText("Nearby Discovery disabled. No device beacons will be received or emitted.")
