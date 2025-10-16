from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import heapq
from typing import Any, Callable, Generic, Optional, TypeVar

N = TypeVar('N', bound="Node")

@dataclass(order=True)
class Event:
    """
    Event data class.
    """
    time: float
    priority: int
    action: Callable[..., Any] = field(compare=False)
    args: tuple[Any, ...] = field(
        compare=False,
        default_factory=tuple[Any, ...]
    )
    kwargs: dict[str, Any] = field(
        compare=False,
        default_factory=dict[str, Any]
    )

class Node(ABC):
    """
    Node base class.
    """
    _next_id: int = 0

    @abstractmethod
    def __init__(self) -> None:
        """
        Initialise node object.
        """
        self.id = Node._next_id
        Node._next_id += 1

        self.medium: Optional[Medium[N]] = None

    def receive(self, data: bytes, rx_power_dbm: float):
        """
        Process received data.

        Parameters
        ----------
        data : bytes
            Receiving bytes.
        rx_power_dbm : float
            Received power.
        """
        print(f'Node {self.id} received {data} at {rx_power_dbm:.2f} [dBm]')

    def transmit(
        self,
        data: bytes,
        *,
        tx_power_dbm: float = 20.0
    ) -> None:
        """
        Transmit data.

        Parameters
        ----------
        data : bytes
            Bytes to send.
        tx_power_dbm : float
            Transmission power.
        """
        if not self.medium:
            raise RuntimeError('Node is not part of a medium.')
        self.medium.propagate(self, data, tx_power_dbm)

class Medium(ABC, Generic[N]):
    """
    Simulation medium base class.
    """
    _next_priority: int = 0

    def __init__(self) -> None:
        """
        Initialise medium object.
        """
        # Time and events
        self.time: float = 0.0
        self._events: list[Event] = []

        # Propogation parameters
        self.path_loss_exp: float = 2
        self.fading_std: float = 4
        self.sensitivity_dbm: float = -90
        self.search_radius: float = 50 # [m]
        self.light_speed: float = 299792458 # [m/s]

    @abstractmethod
    def propagate(
        self,
        sender: N,
        data: bytes,
        tx_power_dbm: float
    ) -> None:
        """
        Propagate a node's transmitted radio signal.

        Parameters
        ----------
        sender : N
            Sending node.
        data : bytes
            Sent bytes.
        tx_power_dbm : float
            Transmission power.
        """
        ...

    def schedule(
        self,
        delay: float,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> None:
        """
        Schedule an event at a delay from
        the current time in the simulation.

        Parameters
        ----------
        delay : float
            Time delay.
        func : Callable[..., Any]
            Function to call after the delay.
        *args
            Positional arguments to pass to `func` when it is called.
        **kwargs
            Keyword arguments to pass to `func` when it is called.
        """
        heapq.heappush(
            self._events,
            Event(self.time + delay, self._next_priority, func, args, kwargs)
        )
        self._next_priority += 1

    def step(self, duration: float) -> None:
        """
        Run the simulation for a specific duration.

        Parameters
        ----------
        duration : float
            Duration to run for.
        """
        end_time = self.time + duration
        while self._events and self._events[0].time <= end_time:
            event = heapq.heappop(self._events)
            self.time = event.time
            event.action(*event.args, **event.kwargs)
        self.time = end_time

    @property
    def has_events_queued(self) -> bool:
        """
        Check if there are any events still queued.

        Returns
        -------
        bool
        """
        return len(self._events) > 0
