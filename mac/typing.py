from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .base import MAC
    from medium.node import Node
    from routing.base import Routing

TMAC = TypeVar('TMAC', bound='MAC[Node, Routing]')
