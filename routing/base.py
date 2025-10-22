from abc import abstractmethod
from typing import Generic

from mac.typing import TMAC

class Routing(Generic[TMAC]):
    """
    Routing base class.
    """
    def __init__(self, mac: TMAC) -> None:
        """
        Initialise routing protocol class.

        Parameters
        ----------
        mac : TMAC
            MAC protocol.
        """
        self.mac = mac
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
    def receive(self, data: bytes) -> None:
        """
        Process received data.

        Parameters
        ----------
        data : bytes
            Receiving bytes.
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
