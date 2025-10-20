import numpy as np
from PySide6.QtWidgets import QApplication
import sys

from medium import Medium, Node2D
from ui import MainWindow

m = Medium[Node2D]()
nodes = [Node2D(*np.random.uniform(-1e4, 1e4, size=2)) for _ in range(1048)]
for n in nodes:
    m.add_node(n)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(m)
    window.show()
    window.activateWindow()
    window.raise_()
    sys.exit(app.exec())
