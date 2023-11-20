from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pin import Pin


class PinPath:
    """Object representing a circuit path of Pin objects.

    Attributes
    ----------
    pins: list[Pin]

    index: int
        Index of pin path within larger

    Methods
    -------
    is_activated(self, x_pins: set[Pin]) -> bool)
        Was path activated for set of pins receiving X?
    """

    def __repr__(self) -> str:
        return f"PinPath({'->'.join([p.name for p in self.pins])})"

    def __init__(self, pins: list[Pin], index: int = None) -> None:
        self._pins: list[Pin] = pins
        self._index: int = index

    @property
    def pins(self) -> list[Pin]:
        return self._pins

    @property
    def index(self) -> int:
        return self._index

    def is_activated(self, x_pins: set[Pin]) -> bool:
        return set(self.pins) <= x_pins


    def get_pdf_string(self) -> str:
        """Get string for Tessent PDF fault definition for path.

        Returns
        -------
        str
            String to write to PDF fault site file.
        """
        pdf_str = f'PATH "path_{self.index}" = \n'
        for pin in self.pins:
            pdf_str += f"  PIN {pin.name} ;\n"
        pdf_str += "END ;"

        return pdf_str