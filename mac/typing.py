from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .base import MAC

TMAC = TypeVar('TMAC', bound='MAC')
