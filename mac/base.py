from abc import abstractmethod
from typing import Generic

from medium.typing import N
from routing.typing import TRouting

class MAC(Generic[N, TRouting]):
    """
    MAC base class.
    """
    def __init__(self, node: N, routing: type[TRouting]) -> None:
        """
        Initialise MAC protocol class.

        Parameters
        ----------
        node : N
            Node.
        routing : type[Routing]
            Routing protocol.
        """
        self.node = node
        self.routing = routing(self)
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

    @abstractmethod
    def receive(
        self,
        data: bytes,
        frequency: float,
        rx_power_dbm: float
    ) -> None:
        """
        Process received data.

        Parameters
        ----------
        data : bytes
            Receiving bytes.
        frequency : float
            Frequency received.
        rx_power_dbm : float
            Received power.
        """
        ...

    @abstractmethod
    def transmit(self, data: bytes) -> None:
        """
        Transmit data.

        Parameters
        ----------
        data : bytes
            Bytes to send.
        """
        ...
