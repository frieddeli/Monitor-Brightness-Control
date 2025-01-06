from monitorcontrol import get_monitors
from PyQt5 import QtWidgets, QtCore, QtGui
import math

def create_sun_pixmap(width: int, height: int) -> QtGui.QPixmap:
    """Creates a sun-shaped QPixmap by drawing with QPainter."""
    pixmap = QtGui.QPixmap(width, height)
    pixmap.fill(QtCore.Qt.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)

    # Draw the sun's core
    core_color = QtGui.QColor('yellow')
    painter.setBrush(core_color)
    painter.setPen(QtGui.QPen(core_color))
    center = QtCore.QPoint(width // 2, height // 2)
    radius = min(width, height) // 4
    painter.drawEllipse(center, radius, radius)

    # Draw sun rays
    ray_color = QtGui.QColor('orange')
    painter.setBrush(QtCore.Qt.NoBrush)
    painter.setPen(QtGui.QPen(ray_color, 2))
    num_rays = 8
    ray_length = min(width, height) // 2
    for i in range(num_rays):
        angle = (360 / num_rays) * i
        radians = math.radians(angle)
        start_point = QtCore.QPointF(
            center.x() + radius * math.cos(radians),
            center.y() + radius * math.sin(radians)
        )
        end_point = QtCore.QPointF(
            center.x() + ray_length * math.cos(radians),
            center.y() + ray_length * math.sin(radians)
        )
        painter.drawLine(start_point, end_point)

    painter.end()
    return pixmap