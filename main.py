import numpy as np
from PySide6.QtWidgets import QApplication
import sys

from mac import MACAloha, MAC_CSMA_CA
from medium import Medium, Node2D
from ui import MainWindow
from routing import RoutingNone, RoutingFlooding

np.random.seed(0)

m = Medium[Node2D]()
nodes = []
for _ in range(1048):
    x, y = np.random.uniform(-1e4, 1e4, size=2)
    n = Node2D(x, y, MAC_CSMA_CA, RoutingFlooding)
    m.add_node(n)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(m)
    window.show()
    window.activateWindow()
    window.raise_()
    sys.exit(app.exec())
