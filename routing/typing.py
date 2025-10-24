from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .base import Routing
    from medium.node import Node

TRouting = TypeVar('TRouting', bound='Routing[Node]')
