"""gui/automation_panel.py — DAZY Automation & Activepieces Management Panel."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)
from gui.overlays import _HudOverlay
from gui.style import hud_font, px_font
from gui.theme import C


class AutomationPanel(_HudOverlay):
    """Drawer/Overlay panel to inspect Activepieces workflows, connections, and DAZY Advisor."""

    workflow_triggered = pyqtSignal(str)
    _OW = 540

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            AutomationPanel {{
                background: rgba(0, 8, 14, 248);
                border: 1px solid {C.BORDER_B};
                border-radius: 6px;
            }}
        """)
        self.setFixedWidth(self._OW)

        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(20, 16, 20, 16)
        self._lay.setSpacing(10)

        # Header
        title = QLabel("⚡  DAZY AUTOMATION & ACTIVEPIECES")
        title.setFont(hud_font(11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C.WHITE}; background: transparent;")
        self._lay.addWidget(title)

        sub = QLabel("24/7 Remote Workflows on VPS & Personal Automation Advisor")
        sub.setFont(px_font(9, QFont.Weight.Normal))
        sub.setStyleSheet(f"color: {C.PRI_DIM}; background: transparent;")
        self._lay.addWidget(sub)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {C.BORDER}; margin: 4px 0;")
        self._lay.addWidget(sep)

        # Status row
        status_row = QHBoxLayout()
        self._status_lbl = QLabel("INSTANCE: ACTIVEPIECES (COOLIFY/VPS)  ·  STATUS: CONNECTED")
        self._status_lbl.setFont(hud_font(8, QFont.Weight.Bold))
        self._status_lbl.setStyleSheet(f"color: {C.GREEN}; background: transparent;")
        status_row.addWidget(self._status_lbl)

        refresh_btn = QPushButton("REFRESH")
        refresh_btn.setFont(hud_font(8, QFont.Weight.Bold))
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C.PANEL2}; color: {C.PRI}; border: 1px solid {C.BORDER};
                border-radius: 3px; padding: 4px 8px;
            }}
            QPushButton:hover {{ border: 1px solid {C.PRI}; color: {C.WHITE}; }}
        """)
        refresh_btn.clicked.connect(self._refresh_state)
        status_row.addWidget(refresh_btn)
        self._lay.addLayout(status_row)

        # Workflows Container
        wf_lbl = QLabel("ACTIVE WORKFLOWS (RUNNING 24/7):")
        wf_lbl.setFont(hud_font(8, QFont.Weight.Bold))
        wf_lbl.setStyleSheet(f"color: {C.TEXT_DIM}; background: transparent;")
        self._lay.addWidget(wf_lbl)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFixedHeight(140)
        self._scroll.setStyleSheet(f"background: {C.PANEL}; border: 1px solid {C.BORDER}; border-radius: 4px;")
        
        self._wf_container = QWidget()
        self._wf_layout = QVBoxLayout(self._wf_container)
        self._wf_layout.setContentsMargins(10, 8, 10, 8)
        self._wf_layout.setSpacing(6)
        self._scroll.setWidget(self._wf_container)
        self._lay.addWidget(self._scroll)

        # Advisor Box
        adv_lbl = QLabel("💡  DAZY AUTOMATION ADVISOR RECOMMENDATION:")
        adv_lbl.setFont(hud_font(8, QFont.Weight.Bold))
        adv_lbl.setStyleSheet(f"color: {C.ACC2}; background: transparent;")
        self._lay.addWidget(adv_lbl)

        self._adv_text = QLabel(
            "Recommendation: Morning Email Radar\n"
            "Checks Gmail at 07:30 AM, summarizes priority senders, and delivers audio briefing."
        )
        self._adv_text.setFont(px_font(9, QFont.Weight.Normal))
        self._adv_text.setStyleSheet(f"color: {C.TEXT}; background: #00121d; border: 1px solid {C.BORDER}; border-radius: 4px; padding: 8px;")
        self._adv_text.setWordWrap(True)
        self._lay.addWidget(self._adv_text)

        self._render_sample_flows()

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

        self.adjustSize()

    def _render_sample_flows(self):
        sample_flows = [
            ("Morning Briefing Flow", "Schedule (07:00 AM)", "ACTIVE"),
            ("Priority Gmail Watcher", "Event: New Email", "ACTIVE"),
            ("WhatsApp Inbound Relay", "Meta Webhook", "ACTIVE"),
            ("System Failure Alert", "DAZY Event", "ACTIVE"),
        ]
        for name, trig, st in sample_flows:
            row = QHBoxLayout()
            lbl = QLabel(f"● {name}  [{trig}]")
            lbl.setFont(hud_font(8, QFont.Weight.Normal))
            lbl.setStyleSheet(f"color: {C.TEXT};")
            row.addWidget(lbl)

            st_lbl = QLabel(st)
            st_lbl.setFont(hud_font(8, QFont.Weight.Bold))
            st_lbl.setStyleSheet(f"color: {C.GREEN};")
            row.addWidget(st_lbl)
            self._wf_layout.addLayout(row)

    def _refresh_state(self):
        self._status_lbl.setText("INSTANCE: ACTIVEPIECES (COOLIFY/VPS)  ·  STATUS: CONNECTED  ✓")
