from abc import abstractmethod
from typing import Generic

from medium.typing import N

class MAC(Generic[N]):
    """
    MAC base class.
    """
    def __init__(self, node: N) -> None:
        """
        Initialise MAC protocol class.

        Parameters
        ----------
        node : N
            Node.
        """
        self.node = node
        self.time: float = 0

    @abstractmethod
    def send(self, address: int, data: bytes) -> None:
        """
        Sends data to an address using the implemented MAC protocol.

        Parameters
        ----------
        address: int
            Address of the target node. Negative values for broadcast.
        data: bytes
            The data to send.
        """
        ...

    @abstractmethod
    def receive(self, data: bytes) -> None:
        """
        Receive data from the PHY layer.

        Parameters
        ----------
        data: bytes
            The recieved data.
        """
        ...

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
