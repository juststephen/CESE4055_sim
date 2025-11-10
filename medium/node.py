from abc import abstractmethod
from typing import Any, Generic, TYPE_CHECKING

from medium.interface import MACInterface, NodeStatus, RoutingInterface
from medium.messages import MessageNode, Messages

if TYPE_CHECKING:
    from .medium import Medium

from .typing import M
from mac.typing import TMAC
from routing.typing import TRouting

class Node(Generic[M, TMAC, TRouting], MACInterface, RoutingInterface):
    """
    Node base class.
    """
    _next_id: int = 0

    def __init__(
        self,
        mac: type[TMAC],
        routing: type[TRouting],
        *,
        mac_param: dict[str, Any] = {},
        routing_param: dict[str, Any] = {}
    ) -> None:
        """
        Initialise node object.

        Parameters
        ----------
        mac : type[TMAC]
            MAC protocol.
        routing : type[TRouting]
            Routing protocol.
        mac_param: dict[str, Any], default: {}
            Parameters to modify MAC protocol
        routing_param: dict[str, Any], default: {}
            Parameters to modify routing protocol
        """
        self._id: int = Node._next_id
        Node._next_id += 1

        self.medium: M | None = None
        self.time: float = 0

        self.mac = mac(self, **mac_param)
        self.routing = routing(self, **routing_param)

        self._status: NodeStatus = NodeStatus.IDLE
    
    @property
    def id(self) -> int:
        return self._id

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
        return self._status

    @status.setter
    def status(self, status: NodeStatus) -> None:
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
        self.routing.tick(time)
        
    def send(
        self,
        address: int,
        data: bytes
    ) -> None:
        """
        Sends data to an address.

        Parameters
        ----------
        address: int
            Address of the target node. Negative values for broadcast.
        data: bytes
            The data to send.
        """
        print(f'Sending message to node {address}: {data}')
        self.routing.send(address, data)

        # Sender is only allowed if it is a MessageNode
        sender: MessageNode | None = None
        if isinstance(self, MessageNode):
            sender = self

        # Register the sent message
        Messages.register_message(sender, address, data, self.time)
    
    def MAC_send(self, address: int, data: bytes) -> None:
        self.mac.send(address, data)
    
    def routing_receive(self, data: bytes) -> None:
        self.routing.receive(data)
        
    def receive(
        self,
        data: bytes
    ) -> None:
        # Receiver is only allowed if it is a MessageNode
        receiver: MessageNode | None = None
        if isinstance(self, MessageNode):
            receiver = self

        # Register received message
        (delay, dist) = Messages.verify_message(receiver, data, self.time)

        # Only print if valid delay and distance
        if delay > 0 and dist > 0:
            print(f'Delay: {delay:.2e}s, distance: {dist:.2e}s - Node {self.id} received message: {data}')

    def antenna_receive(
        self,
        data: bytes,
        frequency: float,
        rx_power_dbm: float
    ) -> None:
        """
        Handle data received by the antenna.

        Parameters
        ----------
        data : bytes
            Receiving bytes.
        frequency : float
            Frequency received.
        rx_power_dbm : float
            Received power.
        """
        # print(
        #     f'Node {self.id} received {data} at '
        #     f'{rx_power_dbm:.2f} [dBm] at {frequency:.3e} [Hz]'
        # )
        self.status = NodeStatus.IDLE
        self.mac.receive(data)

    def antenna_transmit(
        self,
        data: bytes,
        *,
        bitrate: float = 1e6,
        frequency: float = 2.4e9,
        tx_power_dbm: float = 20.0
    ) -> None:
        if not self.medium:
            raise RuntimeError('Node is not part of a medium.')
        self.status = NodeStatus.TRANSMITTING
        self.medium.propagate(self, data, bitrate, frequency, tx_power_dbm)

class Node2D(Node['Medium[Node2D]', Any, Any], MessageNode):
    """
    Two dimensional node class.
    """
    def __init__(
        self,
        x: float,
        y: float,
        mac: type[TMAC],
        routing: type[TRouting],
        *,
        mac_param: dict[str, Any] = {},
        routing_param: dict[str, Any] = {}
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
        mac_param: dict[str, Any], default: {}
            Parameters to modify MAC protocol
        routing_param: dict[str, Any], default: {}
            Parameters to modify routing protocol
        """
        super().__init__(mac, routing, mac_param=mac_param, routing_param=routing_param)
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
