import numpy as np
from PySide6.QtCore import QThread
import time

from medium import Medium, Node2D

AVG_DATA_RATE: float = 1e4
AVG_MSG_LEN: float = 22

class SimulationThread(QThread):
    """
    A thread for the simulation.
    """
    def __init__(
        self,
        medium: Medium[Node2D],
        step_size: float = 5e-7
    ):
        """
        Initialise simulation thread.
        """
        super().__init__()
        self.medium = medium
        self.step_size = step_size
        self._running: bool = True

    def run(self) -> None:
        """
        Run the simulation at roughly 30 steps a second.
        """
        while self._running:
            start_time = time.time()

            self.medium.step(self.step_size)

            # Occasionally generate traffic
            if np.random.rand() < self.step_size * AVG_DATA_RATE / AVG_MSG_LEN:
                i = np.random.randint(0, len(self.medium.nodes))
                node = self.medium.nodes[i]
                address: int = i
                # if self.medium._tree:
                #     # Try to target local nodes, useful for testing MAC without routing
                #     indices: list[int] = self.medium._tree.query_ball_point(node.pos, 2e3)
                #     if len(indices) > 1:
                #         while address == i:
                #             j = np.random.randint(0, len(indices))
                #             address = indices[j]
                while address == i:
                    address = np.random.randint(0, len(self.medium.nodes))
                node.send(address, f'Sender: {i}, Code: {int(1000 * np.random.rand())}'.encode())

            # Sleep to get 100 steps per second
            time.sleep(max(0.01 - (time.time() - start_time), 0))

    def stop(self) -> None:
        """
        Stop the simulation.
        """
        self._running = False
        self.wait()
