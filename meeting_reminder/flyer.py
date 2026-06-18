from __future__ import annotations

import math
from collections import deque

from PySide6.QtCore import (
    QEasingCurve,
    QPointF,
    Property,
    QRectF,
    QPropertyAnimation,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QWidget


class AirplaneOverlay(QWidget):
    finished = Signal()

    def __init__(self, message: str, duration_ms: int = 14400):
        super().__init__()
        self.message = message
        self._progress = 0.0
        self._duration_ms = duration_ms
        self._animation: QPropertyAnimation | None = None

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowStaysOnTopHint
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

    @Property(float)
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, value: float) -> None:
        self._progress = value
        self.update()

    def start(self) -> None:
        self.show()
        self.raise_()
        self._animation = QPropertyAnimation(self, b"progress", self)
        self._animation.setDuration(self._duration_ms)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.setEasingCurve(QEasingCurve.InOutSine)
        self._animation.finished.connect(self._finish)
        self._animation.start()

    def _finish(self) -> None:
        self.hide()
        self.finished.emit()
        self.deleteLater()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        font = QFont("Microsoft YaHei UI", 20)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        metrics = painter.fontMetrics()

        max_banner_width = max(420, int(self.width() * 0.58))
        banner_width = min(
            max(metrics.horizontalAdvance(self.message) + 120, 430),
            max_banner_width,
        )
        group_width = banner_width + 180
        group_height = 168
        x = -group_width - 60 + (self.width() + group_width + 120) * self._progress
        bob = math.sin(self._progress * math.pi * 6) * 14
        y = self.height() * 0.48 - group_height / 2 + bob

        painter.translate(x, y)
        self._draw_banner(painter, banner_width, group_height)
        self._draw_plane(painter, banner_width + 38, 28)

    def _draw_banner(self, painter: QPainter, width: int, height: int) -> None:
        shadow = QPainterPath()
        shadow.addRoundedRect(QRectF(8, 50, width, 78), 22, 22)
        painter.fillPath(shadow, QColor(46, 41, 78, 44))

        rope_pen = QPen(QColor("#875f9a"), 4)
        rope_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(rope_pen)
        painter.drawLine(QPointF(width - 4, 86), QPointF(width + 54, 82))

        banner = QPainterPath()
        banner.moveTo(20, 44)
        banner.cubicTo(width * 0.25, 30, width * 0.45, 56, width - 28, 42)
        banner.quadTo(width + 8, 84, width - 18, 126)
        banner.cubicTo(width * 0.70, 138, width * 0.34, 115, 18, 130)
        banner.quadTo(-8, 86, 20, 44)

        painter.fillPath(banner, QBrush(QColor("#fff7c8")))
        outline = QPen(QColor("#6f4b8b"), 3)
        outline.setCapStyle(Qt.RoundCap)
        outline.setJoinStyle(Qt.RoundJoin)
        painter.setPen(outline)
        painter.drawPath(banner)

        colors = [
            "#ff7aa8",
            "#69d2e7",
            "#f9d423",
            "#8bd17c",
            "#b388ff",
            "#ff9f68",
        ]
        flag_top = 120
        flag_width = 30
        for index, left in enumerate(range(34, max(35, width - 40), flag_width + 8)):
            path = QPainterPath()
            path.moveTo(left, flag_top)
            path.lineTo(left + flag_width, flag_top + 2)
            path.lineTo(left + flag_width / 2, flag_top + 28 + (index % 2) * 5)
            path.closeSubpath()
            painter.fillPath(path, QColor(colors[index % len(colors)]))
            painter.setPen(QPen(QColor("#6f4b8b"), 1.5))
            painter.drawPath(path)

        painter.setPen(QColor("#3f3555"))
        font = QFont("Microsoft YaHei UI", 20)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        text_rect = QRectF(34, 55, width - 66, 58)
        elided = painter.fontMetrics().elidedText(
            self.message, Qt.ElideRight, int(text_rect.width())
        )
        painter.drawText(text_rect, Qt.AlignCenter, elided)

        sparkle_pen = QPen(QColor("#ff7aa8"), 3)
        sparkle_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(sparkle_pen)
        painter.drawLine(QPointF(26, 34), QPointF(34, 22))
        painter.drawLine(QPointF(39, 35), QPointF(51, 28))
        painter.drawLine(QPointF(width - 34, 34), QPointF(width - 24, 22))

    def _draw_plane(self, painter: QPainter, x: float, y: float) -> None:
        painter.save()
        painter.translate(x, y)
        painter.rotate(math.sin(self._progress * math.pi * 4) * 5)

        body = QPainterPath()
        body.moveTo(14, 62)
        body.cubicTo(45, 24, 110, 24, 142, 58)
        body.cubicTo(116, 89, 48, 91, 14, 62)
        painter.fillPath(body, QColor("#fff4fa"))
        painter.setPen(QPen(QColor("#7a4a8d"), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(body)

        wing = QPainterPath()
        wing.moveTo(62, 60)
        wing.cubicTo(52, 84, 44, 110, 78, 108)
        wing.cubicTo(96, 94, 101, 76, 92, 61)
        painter.fillPath(wing, QColor("#9be7ff"))
        painter.drawPath(wing)

        top_wing = QPainterPath()
        top_wing.moveTo(70, 52)
        top_wing.cubicTo(72, 22, 92, 12, 112, 31)
        top_wing.cubicTo(106, 44, 94, 53, 70, 52)
        painter.fillPath(top_wing, QColor("#ffd1dc"))
        painter.drawPath(top_wing)

        tail = QPainterPath()
        tail.moveTo(18, 59)
        tail.lineTo(-10, 33)
        tail.quadTo(20, 28, 36, 50)
        tail.closeSubpath()
        painter.fillPath(tail, QColor("#ffd166"))
        painter.drawPath(tail)

        painter.setBrush(QColor("#6ed6c8"))
        painter.setPen(QPen(QColor("#7a4a8d"), 2))
        painter.drawEllipse(QRectF(92, 46, 18, 18))
        painter.drawEllipse(QRectF(116, 50, 12, 12))

        painter.setBrush(QColor("#ff8fb3"))
        painter.drawEllipse(QRectF(135, 52, 16, 16))

        painter.save()
        painter.translate(151, 60)
        painter.rotate(self._progress * 1440)
        painter.setPen(QPen(QColor("#7a4a8d"), 2))
        painter.setBrush(QColor(255, 255, 255, 190))
        painter.drawEllipse(QRectF(-4, -24, 8, 48))
        painter.drawEllipse(QRectF(-24, -4, 48, 8))
        painter.restore()

        trail_pen = QPen(QColor("#9bdcff"), 3)
        trail_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(trail_pen)
        painter.drawLine(QPointF(-26, 52), QPointF(-54, 43))
        painter.drawLine(QPointF(-24, 68), QPointF(-60, 78))

        painter.restore()


class FlightManager:
    def __init__(self):
        self._queue: deque[str] = deque()
        self._active: AirplaneOverlay | None = None

    def show_message(self, message: str) -> None:
        self._queue.append(message)
        if self._active is None:
            self._start_next()

    def _start_next(self) -> None:
        if not self._queue:
            self._active = None
            return

        self._active = AirplaneOverlay(self._queue.popleft())
        self._active.finished.connect(self._handle_finished)
        self._active.start()

    def _handle_finished(self) -> None:
        self._active = None
        self._start_next()
