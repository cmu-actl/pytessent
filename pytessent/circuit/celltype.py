from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pytessent import PyTessent
    from .gate import Gate


class CellType:
    """Represents cell type (Tessent module).

    Attributes
    ----------
    name : str
        Name of cell type.
    pt : PyTessent
        PyTessent instance for executing Tessent-related tasks.
    inputs : list[str]
        Names of input ports for cell type.
    outputs : list[str]
        Names of output ports for cell type.

    Class Methods
    -------------
    get_celltype(cls, name: str, pt: PyTessent) -> CellType
        Get CellType object from name of cell.
    from_gate(cls, gate: Gate) -> CellType
        Get CellType object from corresponding Gate object.
    """

    _celltypes = {}

    @classmethod
    def get_celltype(cls, name: str, pt: PyTessent) -> CellType:
        """Get CellType object from name of cell."""
        if name not in cls._celltypes:
            cls._celltypes[name] = CellType(name, pt)
        return cls._celltypes[name]

    @classmethod
    def from_gate(cls, gate: Gate) -> CellType:
        """Get CellType object from corresponding Gate object."""
        celltype_name = gate.pt.sendCommand(
            f"get_single_attribute_value {gate.name} -name module_name"
        )
        if celltype_name not in cls._celltypes:
            cls._celltypes[celltype_name] = CellType(celltype_name, gate.pt)
        return cls._celltypes[celltype_name]

    def __init__(self, name: str, pt: PyTessent) -> None:
        """Construct CellType object."""
        self._name: str = name
        self._pt: PyTessent = pt

        # input and output ports
        self._inputs: list[str] = []
        self._outputs: list[str] = []

    @property
    def name(self) -> str:
        """Get name of cell type."""
        return self._name

    @property
    def pt(self) -> str:
        """Get PyTessent instance associated with celltype."""
        return self._pt

    @property
    def inputs(self) -> list[str]:
        """Get list of input ports."""
        if not self._inputs:
            self._inputs = self._pt.sendCommand(
                f"get_ports -of_module {self.name} -direction input"
            )[1:-1].split()
        return self._inputs

    @property
    def outputs(self) -> list[str]:
        """Get list of output ports."""
        if not self._outputs:
            self._outputs = self._pt.sendCommand(
                f"get_ports -of_module {self.name} -direction output"
            )[1:-1].split()
        return self._outputs
