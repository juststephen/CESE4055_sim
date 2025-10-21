from medium.typing import N

from .base import MAC

class MACAloha(MAC[N]):
    """
    ALOHA MAC protocol class.
    """
    def __init__(self, node: N) -> None:
        """
        Initialise class.

        Parameters
        ----------
        node : N
            Node.
        """
        super().__init__(node)

    def tick(self, time: float) -> None:
        """
        Tick method.

        Parameters
        ----------
        time : float
            Current time.
        """
        self.time = time
