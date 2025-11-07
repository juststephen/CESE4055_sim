from typing import Any
import numpy as np
from PySide6.QtCore import QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel
)
import pyqtgraph as pg

from medium import NodeStatus, Medium, Node2D

from .thread import SimulationThread

class MainWindow(QMainWindow):
    """
    Main window class for the UI.
    """
    def __init__(self, medium: Medium[Node2D], *, thread_param: dict[str, Any] = {}):
        """
        Initialise main window.

        Parameters
        ----------
        medium : Medium[Node2D]
            2D simulation medium.
        thread_param: dict[str, Any], default: {}
            Parameters to modify the simulation thread
        """
        super().__init__()
        self.medium = medium

        self.setWindowTitle('Simulation')
        # self.resize(500, 300)

        # Main graph
        self.graph_medium = pg.PlotWidget()
        self.graph_medium.showGrid(x=True, y=True)
        # Scatter: white node markers with a black border of size 10
        self.node_markers = pg.ScatterPlotItem(
            size=10, brush=pg.mkBrush('w'), pen=pg.mkPen('k')
        )
        self.graph_medium.addItem(self.node_markers)

        # Options menu
        self.options_label = QLabel('Options')

        # Overview label
        self.overview_label = QLabel()

        # Layout for the graph and overview
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.graph_medium)
        graph_layout.addWidget(self.overview_label)

        # Layout for the entire graph layout and the options menu
        layout = QHBoxLayout()
        layout.addLayout(graph_layout)
        layout.addWidget(self.options_label)

        # Main widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Seperate thread for the simulation
        self.sim_thread = SimulationThread(self.medium, **thread_param)
        self.sim_thread.start()

        # Timer for simulation and UI updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_ui)
        self.timer.start(30)

    def refresh_ui(self):
        """
        Reresh the UI.
        """
        # Update node positions and colors
        pos = np.array([node.pos for node in self.medium.nodes])
        status_colors = {
            NodeStatus.TRANSMITTING: 'b',
            NodeStatus.RECEIVING: 'g',
            NodeStatus.COLLIDING: 'r',
        }
        colors = [status_colors.get(node.status, 'w') for node in self.medium.nodes]
        self.node_markers.setData(pos=pos, brush=colors)

        # Update overview
        self.overview_label.setText(
            f'Time: {self.medium.time:.3e}\n'
            f'Total Nodes: {len(self.medium.nodes)}\n'
        )


    def closeEvent(self, event: QCloseEvent):
        """
        Ensure the simulation thread stops on close.

        Parameters
        ----------
        event : QCloseEvent
        """
        self.sim_thread.stop()
        super().closeEvent(event)
