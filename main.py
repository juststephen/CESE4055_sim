import numpy as np
from PySide6.QtWidgets import QApplication
import sys

from mac import MACAloha
from medium import Medium, Node2D
from ui import MainWindow
from routing import RoutingNone

from mac import MACCsmaCaRtsCts

np.random.seed(0)

n_rts_cts_nodes: int = 300 # number of Nodes with RTS/CTS protocol

m = Medium[Node2D]()
nodes = []
for _ in range(1048 - n_rts_cts_nodes):
    x, y = np.random.uniform(-1e4, 1e4, size=2)
    n = Node2D(x, y, MACAloha, RoutingNone)
    m.add_node(n)

# Adding the RTS/CTS nodes
for _ in range(n_rts_cts_nodes):  
    x, y = np.random.uniform(-1e4, 1e4, size=2)
    n = Node2D(x, y, MACCsmaCaRtsCts, RoutingNone)
    m.add_node(n)
# • #

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow(m)
    window.show()
    window.activateWindow()
    window.raise_()
    sys.exit(app.exec())
