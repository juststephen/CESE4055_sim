from abc import abstractmethod
from enum import Enum
from typing import Any, Generic, TYPE_CHECKING

if TYPE_CHECKING:
    from .medium import Medium

from .typing import M
from mac.typing import TMAC
from routing.typing import TRouting

class NodeStatus(Enum):
    IDLE = 0
    RECEIVING = 1
    TRANSMITTING = 2
    COLLIDING = 3

class Node(Generic[M, TMAC, TRouting]):
    """
    Node base class.
    """
    _next_id: int = 0

    def __init__(self, mac: type[TMAC], routing: type[TRouting]) -> None:
        """
        Initialise node object.

        Parameters
        ----------
        mac : type[TMAC]
            MAC protocol.
        routing : type[TRouting]
            Routing protocol.
        """
        self.id: int = Node._next_id
        Node._next_id += 1

        self.medium: M | None = None
        self.time: float = 0

        self.mac = mac(self, routing)

        self._status: NodeStatus = NodeStatus.IDLE

    @property
    @abstractmethod
    def pos(self) -> tuple[float, ...]:
        """
        Get the position of the node.

        Returns
        -------
        tuple[float, ...]
            Coordinates.
        """
        ...

    @property
    def status(self) -> NodeStatus:
        """
        Node status getter.

        Returns
        -------
        status : NodeStatus
            Current status.
        """
        return self._status

    @status.setter
    def status(self, status: NodeStatus) -> None:
        """
        Node status setter.

        Parameters
        ----------
        status : NodeStatus
            Status to set.
        """
        match self._status:
            case NodeStatus.IDLE:
                self._status = status

            case NodeStatus.RECEIVING if status == NodeStatus.RECEIVING:
                self._status = NodeStatus.COLLIDING

            case NodeStatus.RECEIVING:
                    self._status = status

            case NodeStatus.TRANSMITTING | NodeStatus.COLLIDING:
                if status == NodeStatus.IDLE:
                    self._status = NodeStatus.IDLE

    def tick(self, time: float) -> None:
        """
        Tick method.

        Parameters
        ----------
        time : float
            Current time.
        """
        self.time = time
        self.mac.tick(time)

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
        self.status = NodeStatus.IDLE
        self.mac.receive(data, frequency, rx_power_dbm)
        print(
            f'Node {self.id} received {data} at '
            f'{rx_power_dbm:.2f} [dBm] at {frequency:.3e} [Hz]'
        )

    def transmit(
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
        tx_power_dbm : float
            Transmission power.
        """
        if not self.medium:
            raise RuntimeError('Node is not part of a medium.')
        self.status = NodeStatus.TRANSMITTING
        self.medium.propagate(self, data, bitrate, frequency, tx_power_dbm)

class Node2D(Node['Medium[Node2D]', Any, Any]):
    """
    Two dimensional node class.
    """
    def __init__(
        self,
        x: float,
        y: float,
        mac: type[TMAC],
        routing: type[TRouting]
    ) -> None:
        """
        Initialise node object.

        Parameters
        ----------
        x : float
            X coordinate.
        y : float
            Y coordinate.
        mac : type[TMAC]
            MAC protocol.
        routing : type[Routing]
            Routing protocol.
        """
        super().__init__(mac, routing)
        self.x = x
        self.y = y

    @property
    def pos(self) -> tuple[float, float]:
        """
        Get the position of the node.

        Returns
        -------
        tuple[float, float]
            X and Y coordinate.
        """
        return (self.x, self.y)
