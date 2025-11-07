from abc import abstractmethod

from medium.node import MACInterface

class MAC():
    """
    MAC base class.
    """
    def __init__(self, interface: MACInterface) -> None:
        """
        Initialise MAC protocol class.

        Parameters
        ----------
        interface: MACInterface
            Accessible for the MAC layer.
        """
        self.interface = interface
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
