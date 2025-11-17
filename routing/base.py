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
        interface: RoutingInterface
            Accessible for the routing layer.
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
    def receive(self, data: bytes, sender_id: int) -> None:
        """
        Receive data from the MAC layer.

        Parameters
        ----------
        data: bytes
            The recieved data.
        sender_id: int
            The ID of the node that sent the packet (the 1-hop neighbor).
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
