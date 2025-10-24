from medium.typing import N

from .base import Routing

class RoutingNone(Routing[N]):
    """
    Disabled routing protocol.
    """
    def __init__(self, node: N) -> None:
        """
        Initialise class.

        Parameters
        ----------
        node : N
            Node.
        """
        super().__init__(node)

    def tick(self, time: float) -> None:
        """
        Tick method.

        Parameters
        ----------
        time : float
            Current time.
        """
        self.time = time
