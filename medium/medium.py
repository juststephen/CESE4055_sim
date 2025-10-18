from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
import heapq
import numpy as np
from numpy.typing import NDArray
from typing import Any, Generic, TypeVar

N = TypeVar('N', bound='Node')

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

@dataclass
class Reception:
    """
    Reception data class.
    """
    node: 'Node'
    start_time: float
    end_time: float
    data: bytes
    frequency: float
    power_dbm: float

    def receive(self) -> None:
        """
        Finalise reception.
        """
        self.node.receive(
            self.data,
            self.frequency,
            self.power_dbm
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

        self.medium: Medium[N] | None = None

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
        self.medium.propagate(self, data, bitrate, frequency, tx_power_dbm)

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

        # Active receptions at receivers, keys are node ID
        self._active_receptions: dict[int, list[Reception]] = defaultdict(list)

        # Propogation parameters
        self.path_loss_exp: float = 2
        self.fading_std: float = 4
        self.sensitivity_dbm: float = -90
        self.search_radius: float = 1e3 # [m]
        self.light_speed: float = 299792458 # [m/s]

        # SINR parameters for colissions and noise
        self.noise_floor_dbm: float = -100
        self.sinr_threshold_db: float = 10

    @abstractmethod
    def propagate(
        self,
        sender: N,
        data: bytes,
        bitrate: float,
        frequency: float,
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
        bitrate : float
            The bitrate for the data transmission.
        frequency : float
            Transmission frequency.
        tx_power_dbm : float
            Transmission power.
        """
        ...

    def schedule(
        self,
        delay: float,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any
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
        *args : Any
            Positional arguments to pass to `func` when it is called.
        **kwargs : Any
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

    def _compute_sinr_db(
        self,
        signal_dbm: float,
        interferers_dbm: Sequence[float]
    ) -> float:
        """
        Compute the signal-to-interference-plus-noise ratio (SINR).

        Parameters
        ----------
        signal_dbm : float
            Signal's power.
        interferers_dbm : Sequence[float]
            Interfering signals' power.

        Returns
        -------
        sinr_db : float
        """
        # No interference, use SNR
        if not interferers_dbm:
            return signal_dbm - self.noise_floor_dbm

        # Convert to array
        interferers_dbm_array: NDArray[np.float64] = np.asarray(
            interferers_dbm,
            dtype=np.float64
        )

        # Relative interference power
        rel_interference = np.sum(
            10 ** ((interferers_dbm_array - signal_dbm) * 0.1)
        )
        # Relative noise
        rel_noise = 10 ** ((self.noise_floor_dbm - signal_dbm) * 0.1)

        # Compute SINR in [dB] directly
        return 10 * np.log10(rel_interference + rel_noise)

    def _complete_receive(
        self,
        reception: Reception
    ) -> None:
        """
        Handle the completion of a receiving signal.
        """
        receiver_id: int = reception.node.id

        # Remove completed reception
        ongoing_receptions = [
            r for r in self._active_receptions[receiver_id]
            if r.end_time >= self.time
        ]
        # Get earliest start time of ongoing receptios
        earliest = min(
            (*(r.start_time for r in ongoing_receptions), self.time)
        )
        # Both ongoing and overlapping are active
        self._active_receptions[receiver_id] = [
            r for r in self._active_receptions[receiver_id]
            if r in ongoing_receptions or r.end_time >= earliest
        ]

        # Find overlapping receptions
        overlapping = [
            r for r in self._active_receptions[receiver_id]
            if r != reception
            and r.frequency == reception.frequency
            and r.start_time <= reception.end_time
            and r.end_time >= reception.start_time
        ]

        # Compute SINR
        interferers_dbm = [r.power_dbm for r in overlapping]
        sinr_db = self._compute_sinr_db(reception.power_dbm, interferers_dbm)

        # The data is received if the SINR is above the threshold
        if sinr_db >= self.sinr_threshold_db:
            reception.receive()
