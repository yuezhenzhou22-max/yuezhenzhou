from __future__ import annotations

import sys

from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from .flyer import FlightManager
from .manager_window import ReminderManagerWindow
from .scheduler import ReminderScheduler
from .storage import ReminderStore


class TrayApplication(QObject):
    def __init__(self, app: QApplication):
        super().__init__()
        self.app = app
        self.store = ReminderStore()
        self.flight_manager = FlightManager()
        self.scheduler = ReminderScheduler(self.store)
        self.window = ReminderManagerWindow(self.store)
        self.tray = QSystemTrayIcon(_make_tray_icon(), self.app)

        self.open_action = QAction("打开提醒管理", self.tray)
        self.test_action = QAction("测试小飞机", self.tray)
        self.hourly_action = QAction("暂停整点提醒", self.tray)
        self.quit_action = QAction("退出", self.tray)

        self._build_tray_menu()
        self._connect_signals()

    def start(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.warning(
                None,
                "托盘不可用",
                "当前系统托盘不可用，提醒管理窗口会直接打开。",
            )
            self.window.show()
        else:
            self.tray.show()

        self.scheduler.start()

    def _build_tray_menu(self) -> None:
        menu = QMenu()
        menu.addAction(self.open_action)
        menu.addAction(self.test_action)
        menu.addSeparator()
        menu.addAction(self.hourly_action)
        menu.addSeparator()
        menu.addAction(self.quit_action)
        self.tray.setContextMenu(menu)
        self.tray.setToolTip("时间提醒小飞机")

    def _connect_signals(self) -> None:
        self.open_action.triggered.connect(self.show_manager)
        self.test_action.triggered.connect(
            lambda: self.flight_manager.show_message("小飞机试飞成功啦")
        )
        self.hourly_action.triggered.connect(self.toggle_hourly)
        self.quit_action.triggered.connect(self.app.quit)
        self.tray.activated.connect(self._tray_activated)
        self.scheduler.fly_requested.connect(self.flight_manager.show_message)

    def show_manager(self) -> None:
        self.window.refresh_table()
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def toggle_hourly(self) -> None:
        enabled = not self.scheduler.hourly_enabled
        self.scheduler.set_hourly_enabled(enabled)
        self.hourly_action.setText("暂停整点提醒" if enabled else "恢复整点提醒")

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_manager()


def _make_tray_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(QPen(QColor("#6f4b8b"), 3))

    body = QPainterPath()
    body.moveTo(10, 35)
    body.cubicTo(22, 17, 48, 17, 58, 34)
    body.cubicTo(45, 48, 22, 48, 10, 35)
    painter.fillPath(body, QColor("#fff4fa"))
    painter.drawPath(body)

    wing = QPainterPath()
    wing.moveTo(28, 34)
    wing.lineTo(21, 54)
    wing.lineTo(42, 43)
    wing.closeSubpath()
    painter.fillPath(wing, QColor("#9be7ff"))
    painter.drawPath(wing)

    tail = QPainterPath()
    tail.moveTo(12, 34)
    tail.lineTo(2, 24)
    tail.lineTo(21, 30)
    tail.closeSubpath()
    painter.fillPath(tail, QColor("#ffd166"))
    painter.drawPath(tail)

    painter.setBrush(QColor("#ff7aa8"))
    painter.drawEllipse(51, 30, 8, 8)
    painter.end()
    return QIcon(pixmap)


def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("时间提醒小飞机")

    tray_app = TrayApplication(app)
    tray_app.start()
    sys.exit(app.exec())
