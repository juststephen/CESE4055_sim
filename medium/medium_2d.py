import numpy as np
from scipy.spatial import KDTree
from typing import Optional

from .medium import Node, Medium

class Node2D(Node):
    """
    Two dimensional node class.
    """
    def __init__(self, x: float, y: float) -> None:
        """
        Initialise node object.

        Parameters
        ----------
        x : float
            X coordinate.
        y : float
            Y coordinate.
        """
        super().__init__()
        self.x = x
        self.y = y

    @property
    def pos(self) -> tuple[float, float]:
        """
        Get the position of the node.

        Returns
        -------
        tuple[float, float]
            X and Y coordinate.
        """
        return (self.x, self.y)

class Medium2D(Medium[Node2D]):
    """
    Simulation medium for two dimensions.
    """
    def __init__(self) -> None:
        """
        Initialise two dimensional medium object.
        """
        super().__init__()
        self.nodes: list[Node2D] = []
        self._tree: Optional[KDTree] = None

    def add_node(self, node: Node2D) -> None:
        """
        Add a node to the medium.

        Parameters
        ----------
        node : Node2D
            Node to add.
        """
        node.medium = self
        self.nodes.append(node)
        # Invalidate tree
        self._tree = None

    def _ensure_tree(self):
        """
        Ensure a tree exists, otherwise generate it.
        """
        if self._tree is None and self.nodes:
            self._tree = KDTree([n.pos for n in self.nodes])

    def propagate(
        self,
        sender: Node2D,
        data: bytes,
        tx_power_dbm: float
    ) -> None:
        """
        Propagate a node's transmitted radio signal.

        Parameters
        ----------
        sender : Node
            Sending node.
        data : bytes
            Sent bytes.
        tx_power_dbm : float
            Transmission power.
        """
        self._ensure_tree()
        if not self._tree:
            return

        # Query potential receivers near the sender
        indices: list[int] = self._tree.query_ball_point(sender.pos, self.search_radius)
        # Select receivers, excluding the sender
        receivers = [self.nodes[i] for i in indices if self.nodes[i] is not sender]
        if not receivers:
            return

        # Get positions of receivers
        rx_positions = np.array([rx.pos for rx in receivers])

        # Compute distances
        diffs = rx_positions - np.array(sender.pos)
        distances = np.linalg.norm(diffs, axis=1)

        # Prevent extremely short distances by clipping them to a minimum
        np.clip(distances, 1e-6, None, distances)

        # Path loss and fading
        path_loss = 10 * self.path_loss_exp * np.log10(distances)
        fading = np.random.normal(0, self.fading_std, size=distances.shape)

        # Multipath factor (Rayleigh fading)
        multipath_factor = 20 * np.log10(np.random.rayleigh(1.0, size=distances.shape))

        # Compute final power at receivers
        rx_power = tx_power_dbm - path_loss + fading + multipath_factor * 0.1

        # Compute propagation delays
        delays = distances / self.light_speed

        # Deliver data to receivers above sensitivity threshold
        for rx, power, delay in zip(receivers, rx_power, delays):
            if power >= self.sensitivity_dbm:
                self.schedule(delay, rx.receive, data, power)
