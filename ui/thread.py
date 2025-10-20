import numpy as np
from PySide6.QtCore import QThread
import time

from medium import Medium, Node2D

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
            if not self.medium.has_events_queued:
                i = np.random.randint(0, len(self.medium.nodes))
                self.medium.nodes[i].transmit(f'test {i}'.encode(), bitrate=4e6)
            if np.random.rand() < 1e-3:
                i = np.random.randint(0, len(self.medium.nodes))
                self.medium.nodes[i].transmit(f'rand {i}'.encode(), bitrate=8e6)

            # Sleep to get 30 steps per second
            time.sleep(max(0.033 - (time.time() - start_time), 0))

    def stop(self) -> None:
        """
        Stop the simulation.
        """
        self._running = False
        self.wait()
