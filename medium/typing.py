from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .node import Node
    from .medium import Medium

N = TypeVar('N', bound='Node[Medium]')
M = TypeVar('M', bound='Medium[Node]')
