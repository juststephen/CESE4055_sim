from typing import Any
import numpy as np
from PySide6.QtWidgets import QApplication
import sys
import argparse

from medium import Medium, Node2D
from ui import MainWindow

from configs import EXPERIMENTS

np.random.seed(0)

if __name__ == '__main__':
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Ad Hoc Network Simulator")
    parser.add_argument(
        '--experiment', 
        type=str, 
        default='csma_flooding_ui_show',  # <-- Set your default experiment here
        choices=EXPERIMENTS.keys(),
        help='The experiment configuration to run.'
    )
    args = parser.parse_args()

    # Get the chosen configuration
    config = EXPERIMENTS[args.experiment]
    print(f"Running experiment: {args.experiment}")
    

    m = Medium[Node2D]()
    nodes = []
    for _ in range(config.get("NODE_COUNT", 50)):
        x, y = np.random.uniform(-config["COORD_MAX"], config["COORD_MAX"], size=2)
        n = Node2D(
            x, y,
            config["MAC_TYPE"],
            config["ROUTING_TYPE"],
            mac_param=config["MAC_PARAM"],
            routing_param=config["ROUTING_PARAM"]
        )
        m.add_node(n)
        

    # --- Launch the GUI ---
    app = QApplication(sys.argv)
    window = MainWindow(m, thread_param=config["THREAD_PARAM"])
    window.show()
    window.activateWindow()
    window.raise_()
    sys.exit(app.exec())