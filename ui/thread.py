import numpy as np
from PySide6.QtCore import QThread
import time

from medium import Medium, Node2D

MSG: str = "Sender:{send}, Code:{code}, Dist:{dist:.2e}"
AVG_MSG_LEN: float = 33
SIMULATION_FPS: int = 100

class SimulationThread(QThread):
    """
    A thread for the simulation.
    """
    def __init__(
        self,
        medium: Medium[Node2D],
        *,
        step_size: float = 1e-7,
        data_rate: float = 1e6,
        simulation_time_limit: float = 30,
        fps_limit: bool = False
    ):
        """
        Initialise simulation thread.
        
        Parameters
        ----------
        medium : Medium[Node2D]
            2D simulation medium.
        step_size: float, default: 1e-7
            The duration of one simulation step in seconds.
        data_rate: float, default: 1e6
            The average traffic that is put in the network in bytes per second.
        simulation_time_limit, default: 30
            The maximum simulated time after which the simulation stops.
        fps_limit, default: False
            Whether to limit the simulation FPS for viewing purposes.
        """
        super().__init__()
        self.medium = medium
        self._step_size = step_size
        self._data_rate = data_rate
        self._running: bool = True
        self._simulation_time_limit = simulation_time_limit
        self._fps_limit = fps_limit

    def run(self) -> None:
        """
        Run the simulation at roughly 30 steps a second.
        """

        start_time: float = time.time()
        step: float = 1.0 / SIMULATION_FPS
        
        while self._running:
            self.medium.step(self._step_size)
            
            if self._simulation_time_limit is not None and self.medium.time >= self._simulation_time_limit:
                print(f"Simulation time limit of {self._simulation_time_limit}s reached.")
                self._running = False
                break

            # Occasionally generate traffic
            if np.random.rand() < self._step_size * self._data_rate / AVG_MSG_LEN:
                i = np.random.randint(0, len(self.medium.nodes))
                node = self.medium.nodes[i]
                address: int = i
                while address == i:
                    address = np.random.randint(0, len(self.medium.nodes))

                other = self.medium.nodes[address]
                dist: float = pow(pow(other.x - node.x, 2) + pow(other.y - node.y, 2), .5)
                node.send(address, MSG.format(send=i, code=int(10 * np.random.rand()), dist=dist).encode())

            if self._fps_limit:
                # Sleep to get SIMULATION_FPS steps per second
                time.sleep(max(step - (time.time() - start_time), 0))
                start_time += step

    def stop(self) -> None:
        """
        Stop the simulation.
        """
        self._running = False
        self.wait()
