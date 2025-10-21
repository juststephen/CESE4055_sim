from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .base import MAC
    from medium.node import Node

TMAC = TypeVar('TMAC', bound='MAC[Node]')
