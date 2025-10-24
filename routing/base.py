from abc import abstractmethod
from typing import Generic

from medium.typing import N

class Routing(Generic[N]):
    """
    Routing base class.
    """
    def __init__(self, node: N) -> None:
        """
        Initialise routing protocol class.

        Parameters
        ----------
        node : N
            Node.
        """
        self.node = node
        self.time: float = 0

    @abstractmethod
    def tick(self, time: float) -> None:
        """
        Tick method.

        Parameters
        ----------
        time : float
            Current time.
        """
        ...
