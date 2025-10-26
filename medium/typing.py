from typing import Any, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from mac import MAC
    from routing import Routing
    from .node import Node
    from .medium import Medium

N = TypeVar('N', bound='Node[Medium[Any], MAC, Routing]')
M = TypeVar('M', bound='Medium[Node]')
