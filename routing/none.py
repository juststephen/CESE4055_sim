from mac.typing import TMAC

from .base import Routing

class RoutingNone(Routing[TMAC]):
    """
    Disabled routing protocol.
    """
    def __init__(self, mac: TMAC) -> None:
        """
        Initialise class.

        Parameters
        ----------
        mac : TMAC
            MAC protocol.
        """
        super().__init__(mac)

    def tick(self, time: float) -> None:
        """
        Tick method.

        Parameters
        ----------
        time : float
            Current time.
        """
        self.time = time
