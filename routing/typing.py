from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .base import Routing

TRouting = TypeVar('TRouting', bound='Routing')
