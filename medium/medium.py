from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
import heapq
import numpy as np
from scipy.spatial import KDTree
from typing import Any, Generic

from .node import NodeStatus
from .typing import N

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
class Reception(Generic[N]):
    """
    Reception data class.
    """
    node: N
    start_time: float
    end_time: float
    data: bytes
    frequency: float
    power_dbm: float

    def receive(self) -> None:
        """
        Finalise reception.
        """
        self.node.antenna_receive(
            self.data,
            self.frequency,
            self.power_dbm
        )

class Medium(Generic[N]):
    """
    Simulation medium base class.
    """
    _next_priority: int = 0

    def __init__(self) -> None:
        """
        Initialise medium object.
        """
        self.nodes: list[N] = []
        self._tree: KDTree | None = None

        # Time and events
        self.time: float = 0.0
        self._events: list[Event] = []

        # Active receptions at receivers, keys are node ID
        self._active_receptions: dict[int, list[Reception[N]]] = defaultdict(list)

        # Propogation parameters
        self.path_loss_exp: float = 2
        self.fading_std: float = 4
        self.sensitivity_dbm: float = -90
        self.search_radius: float = 1e5 # [m]
        self.light_speed: float = 299792458 # [m/s]

        # SINR parameters for colissions and noise
        self.noise_floor_dbm: float = -100
        self.sinr_threshold_db: float = 20

    def add_node(self, node: N) -> None:
        """
        Add a node to the medium.

        Parameters
        ----------
        node : N
            Node to add.
        """
        node.medium = self
        self.nodes.append(node)
        # Invalidate tree
        self._tree = None

    def _ensure_tree(self):
        """
        Ensure a tree exists, otherwise generate it.
        """
        if self._tree is None and self.nodes:
            self._tree = KDTree([n.pos for n in self.nodes])

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
        self._ensure_tree()
        if not self._tree:
            return

        # Query potential receivers near the sender
        indices: list[int] = self._tree.query_ball_point(
            sender.pos,
            self.search_radius
        )
        # Select receivers, excluding the sender
        receivers = [
            self.nodes[i] for i in indices if self.nodes[i] is not sender
        ]
        if not receivers:
            return

        # Get positions of receivers
        rx_positions = np.array([rx.pos for rx in receivers])

        # Compute distances
        diffs = rx_positions - np.array(sender.pos)
        distances = np.linalg.norm(diffs, axis=1)

        # Prevent extremely short distances by clipping them to a minimum
        np.clip(distances, 1e-6, None, distances)

        # Path loss and fading
        path_loss = 10 * self.path_loss_exp * np.log10(distances)
        fading = np.random.normal(np.zeros(distances.shape), self.fading_std)

        # Multipath factor (Rayleigh fading)
        multipath_factor = 20 * np.log10(
            np.random.rayleigh(np.ones(distances.shape))
        )

        # Compute final power at receivers
        rx_power = tx_power_dbm - path_loss + fading + multipath_factor * 0.1
        # Signal to noise ratio
        rx_snr = rx_power - self.noise_floor_dbm

        # Compute propagation delays and airtime
        delays = distances / self.light_speed
        airtime: float = len(data) * 8 / bitrate
        event_time = delays + airtime

        # Set transmitter to idle status after airtime
        self.schedule(airtime, self._set_node_status, sender, NodeStatus.IDLE)

        # Transmission start and end time for colission detection
        start = self.time + delays
        end = start + airtime

        # Deliver data to receivers using events
        for i, rx in enumerate(receivers):
            snr = rx_snr[i]
            if snr < self.sinr_threshold_db:
                continue
            reception = Reception(
                rx,
                start[i],
                end[i],
                data,
                frequency,
                rx_power[i]
            )
            self.schedule(
                delays[i],
                self._set_node_status,
                rx,
                NodeStatus.RECEIVING
            )
            self.schedule(event_time[i], self._complete_receive, reception)
            self._active_receptions[rx.id].append(reception)

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

        # Tick every node
        for n in self.nodes:
            n.tick(self.time)

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
        interferers_dbm_array = np.asarray(interferers_dbm)

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
        reception: Reception[N]
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

        # Set status to idle when this is the only ongoing reception
        if all(r.end_time <= self.time for r in overlapping):
            self._set_node_status(reception.node, NodeStatus.IDLE)

    def _set_node_status(self, node: N, status: NodeStatus) -> None:
        """
        Set a node's status.

        Parameters
        ----------
        status : NodeStatus
            Status to set.
        """
        node.status = status
