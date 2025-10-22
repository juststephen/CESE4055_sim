from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .base import Routing
    from mac.base import MAC

TRouting = TypeVar('TRouting', bound='Routing[MAC]')
