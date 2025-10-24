from abc import abstractmethod

from medium.interface import RoutingInterface

class Routing():
    """
    Routing base class.
    """
    def __init__(self, interface: RoutingInterface) -> None:
        """
        Initialise routing protocol class.

        Parameters
        ----------
        node : N
            Node.
        """
        self.interface = interface
        self.time: float = 0

    @abstractmethod
    def send(self, address: int, data: bytes) -> None:
        """
        Sends data to an address using the implemented routing protocol.

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
        Receive data from the MAC layer.

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
