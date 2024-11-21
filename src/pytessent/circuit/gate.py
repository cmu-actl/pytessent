from __future__ import annotations

from typing import TYPE_CHECKING

from pytessent.circuit.celltype import CellType
from pytessent.circuit.utils import CircuitElementNotFoundException

if TYPE_CHECKING:
    from pytessent import PyTessent
    from pytessent.circuit.pin import GatePin


class Gate:
    """Represents a gate instance within a circuit.

    Attributes
    ----------
    name : str
        Name of pin.
    pt : PyTessent
        PyTessent instance for executing Tessent-related tasks.
    celltype : CellType
        Cell type for gate instance.
    inputs : list[Pin]
        Input pins.
    outputs : list[Pin]
        Output pins.

    Class Methods
    -------------
    get_gate(cls, name: str, pt: PyTessent) -> Gate
        Get gate object from name of gate.
    from_pin(cls, pin: Pin) -> Gate
        Get gate object from corresponding Pin object.
    """

    _gates: dict[str, Gate] = {}

    @classmethod
    def get_gate(cls, name: str, pt: PyTessent) -> Gate:
        """Get gate object from name of gate."""
        if name not in cls._gates:
            cls._gates[name] = Gate(name, pt)
        return cls._gates[name]

    @classmethod
    def from_pin(cls, pin: GatePin) -> Gate:
        """Get gate object from corresponding Pin object."""
        gatename = "/".join(pin.name.split("/")[:-1])  # extract gate name from pin name
        gate = cls.get_gate(gatename, pin.pt)

        # add pin as gate input or output
        if pin.direction == "input" and pin not in gate.inputs:
            gate._inputs.append(pin)
        if pin.direction == "output" and pin not in gate.outputs:
            gate._outputs.append(pin)

        return gate

    @staticmethod
    def verify_gate(gate: str, pt: PyTessent) -> bool:
        """Verify that gate exists in the design."""
        return "Error" not in pt.send_command(f"get_instance {gate}")

    def __repr__(self) -> str:
        return f"Gate({self.name})"

    def __init__(self, name: str, pt: PyTessent) -> None:
        """Construct Gate object."""
        if not self.verify_gate(name, pt):
            raise CircuitElementNotFoundException(f"Gate {name} not found in design.")
        self._name: str = name
        self._pt: PyTessent = pt
        self._celltype: CellType | None = None
        self._inputs: list[GatePin] = []
        self._outputs: list[GatePin] = []

    @property
    def name(self) -> str:
        """Get name of gate."""
        return self._name

    @property
    def vname(self) -> str:
        """Get name of gate."""
        return self.name.replace("/", "__")

    @property
    def pt(self) -> PyTessent:
        """Get PyTessent instance associated with pin."""
        return self._pt

    @property
    def celltype(self) -> CellType:
        """Get CellType object corresponding to gate."""
        if not self._celltype:
            self._celltype = CellType.from_gate(self)
        return self._celltype

    @property
    def inputs(self) -> list[GatePin]:
        """Get input Pin objects of gate."""
        return self._inputs

    @property
    def outputs(self) -> list[GatePin]:
        """Get output Pin objects of gate."""
        return self._outputs
