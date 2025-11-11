from typing import Any
import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel
)
import pyqtgraph as pg

from medium import NodeStatus, Medium, Node2D, Messages

from .input import NumericInputWidget
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

        # Path loss exponent option
        self.option_pathloss = NumericInputWidget(
            'Path loss exponent',
            medium.path_loss_exp,
            float,
            2,
            8,
            0.1
        )
        self.option_pathloss.value_updated.connect(
            lambda value: setattr(medium, 'path_loss_exp', value) # type: ignore
        )

        # Overview label
        self.overview_label = QLabel()

        # Layout for the graph and overview
        graph_layout = QVBoxLayout()
        graph_layout.addWidget(self.graph_medium)
        graph_layout.addWidget(self.overview_label)

        # Options layout
        options_layout = QVBoxLayout()
        options_layout.addWidget(
            self.options_label,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        options_layout.addWidget(
            self.option_pathloss,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        options_layout.addStretch()

        # Layout for the entire graph layout and the options menu
        layout = QHBoxLayout()
        layout.addLayout(graph_layout)
        layout.addLayout(options_layout)

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
            f'Success rate: {Messages.get_success_rate():.1f}% (end to end)\n'
            f'Average delay: {Messages.get_avg_delay():.2e}s (end to end)\n'
            f'Average speed: {Messages.get_avg_speed():.2e}m/s (end to end)\n'
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
