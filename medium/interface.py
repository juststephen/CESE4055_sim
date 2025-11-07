from abc import abstractmethod
from enum import Enum

class NodeStatus(Enum):
    IDLE = 0
    RECEIVING = 1
    TRANSMITTING = 2
    COLLIDING = 3

class MACInterface():
    """
    Expose methods accessible for the MAC layer
    """
    @property
    @abstractmethod
    def id(self) -> int:
        """
        Node id.
        """
        ...
    
    @property
    @abstractmethod
    def status(self) -> NodeStatus:
        """
        Node status.

        Returns
        -------
        status : NodeStatus
            Current status.
        """
        ...

    @abstractmethod
    def antenna_transmit(
        self,
        data: bytes,
        *,
        bitrate: float = 1e6,
        frequency: float = 2.4e9,
        tx_power_dbm: float = 20.0
    ) -> None:
        """
        Transmit data.

        Parameters
        ----------
        data : bytes
            Bytes to send.
        bitrate : float, default: 1e6
            The bitrate for the data transmission, by default 1 [Mb/s].
        frequency : float, default: 2.4e9
            Transmission frequency.
        tx_power_dbm : float, default: 20.0
            Transmission power.
        """
        ...
    
    @abstractmethod
    def routing_receive(self, data: bytes) -> None:
        """
        Invoke the routing layer to process received data.

        Parameters
        ----------
        data : bytes
            Receiving bytes.
        """
        ...

class RoutingInterface():
    """
    Expose methods accessible for the routing layer
    """
    @property
    @abstractmethod
    def id(self) -> int:
        """
        The node id.
        """
        ...

    @abstractmethod
    def MAC_send(self, address: int, data: bytes) -> None:
        """
        Send to the MAC layer.

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
        Process received data.

        Parameters
        ----------
        data : bytes
            Receiving bytes.
        """
        ...
