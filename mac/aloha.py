from medium.typing import N
from routing.typing import TRouting

from .base import MAC

class MACAloha(MAC[N, TRouting]):
    """
    ALOHA MAC protocol class.
    """
    def __init__(self, node: N, routing: type[TRouting]) -> None:
        """
        Initialise class.

        Parameters
        ----------
        node : N
            Node.
        routing : type[Routing]
            Routing protocol.
        """
        super().__init__(node, routing)

    def tick(self, time: float) -> None:
        """
        Tick method.

        Parameters
        ----------
        time : float
            Current time.
        """
        self.time = time
        self.routing.tick(time)
