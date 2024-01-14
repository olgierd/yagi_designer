#!/usr/bin/env python3

import sys
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt, QTimer


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.label = QtWidgets.QLabel()
    
        self.canvas = QtGui.QPixmap(1000, 1000)
        self.label.setPixmap(self.canvas)
        self.setCentralWidget(self.label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.draw_antenna)
        self.timer.start(200)

    def nec_to_lines(self, nec_path):
        with open(nec_path, 'r') as f:
            nec_file = f.read()

        wires = [[float(x) for x in w.split()[3:9]] for w in nec_file.splitlines() if w.startswith("GW")]
        return wires
    

    def draw_antenna(self):

        wires = self.nec_to_lines('/tmp/yagidesign.nec')
        if not wires:
            return

        canvas = QtGui.QPixmap(900, 900)
        canvas.fill(Qt.gray)

        painter = QtGui.QPainter(canvas)
        pen = QtGui.QPen()
        pen.setWidth(4)
        pen.setColor(QtGui.QColor('black'))
        painter.setPen(pen)

        # scale to fit
        xmin, xmax = min([min(w[0], w[3]) for w in wires]), max([max(w[0], w[3]) for w in wires])
        ymin, ymax = min([min(w[1], w[4]) for w in wires]), max([max(w[1], w[4]) for w in wires])

        dx, dy = xmax-xmin, ymax-ymin
        centx, centy = (xmin+xmax)/2, (ymin+ymax)/2
        scale = max(dx, dy)

        for w in wires:
            x1, y1, x2, y2 = [(w[0]-centx)/scale, (w[1]-centy)/scale, (w[3]-centx)/scale, (w[4]-centy)/scale]
            x1 = int(x1*800)+500
            y1 = int(y1*800)+500
            x2 = int(x2*800)+500
            y2 = int(y2*800)+500

            painter.drawLine(QtCore.QPoint(x1, y1), QtCore.QPoint(x2, y2))

        painter.end()
        self.label.setPixmap(canvas)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()

app.exec_()