"""Interface. O pipeline só conhece isto; Azure real ou mock são intercambiáveis."""
from typing import Protocol

from .modelo import Ticket


class FonteDeTickets(Protocol):
    def listar_bugs_abertos(self) -> list[Ticket]:
        """Bugs abertos do time, já com detalhes e comentários."""
        ...
