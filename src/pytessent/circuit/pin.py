from __future__ import annotations

from typing import Literal, TYPE_CHECKING

from .gate import Gate

if TYPE_CHECKING:
    from ..pytessent import PyTessent


class Pin:
    """Represents pin object.

    Attributes
    ----------
    name : str
        Name of pin.
    pt : PyTessent
        PyTessent instance for executing Tessent-related tasks.
    direction : str
        Is pin "input" or "output" of gate?
    fanin : set[Pin]
        Other pins on fanin of given pin.
    fanout : set[Pin]
        Other pins on fanout of given pin.
    gate : Gate
        Gate that pin is a part of.
    leaf : str
        Leaf name of pin (ex: "z" for "<gate>/z")

    Methods
    -------
    get_pin_value(self) -> tuple(Literal["0", "1", "X"])
        From a given pin name, find its value for the current gate report.

    Class Methods
    -------------
    get_pin(cls, name: str, pt: PyTessent) -> Pin
        Get pin object from name of pin.
    """

    _pins: dict[str, Pin] = {}

    @classmethod
    def get_pin(cls, name: str, pt: PyTessent) -> Pin:
        """Get pin object from name of pin."""
        if name not in cls._pins:  # get pin if it has already been created
            cls._pins[name] = Pin(name, pt)  # otherwise, create
        return cls._pins[name]

    def __repr__(self) -> str:
        return f"Pin({self.name})"

    def __init__(self, name: str, pt: PyTessent) -> None:
        """Construct Pin object."""
        self._name: str = name
        self._pt: PyTessent = pt
        self._direction: str = pt.sendCommand(f"get_single_attribute_value {name} -name direction")

        # leave fanin/fanout blank, will fill when called
        self._fanin: set[Pin] = set()
        self._fanout: set[Pin] = set()

        self._gate: Gate = Gate.from_pin(self)
        self._leaf = name.split("/")[-1]

    @property
    def name(self) -> str:
        """Get name of pin."""
        return self._name

    @property
    def vname(self) -> str:
        """Get verilog name of pin."""
        return self.name.replace("/", "__")

    @property
    def pt(self) -> PyTessent:
        """Get PyTessent instance associated with pin."""
        return self._pt

    @property
    def direction(self) -> str:
        """Get direction (input or output) of pin."""
        return self._direction

    @property
    def leaf(self) -> str:
        """Leaf name of pin."""
        return self._leaf

    @property
    def fanin(self) -> set[Pin]:
        """Get fanin Pin objects from pin."""
        if not self._fanin:
            self._fanin = set([
                self.get_pin(p, self.pt)
                for p in self.pt.sendCommand(f"get_fanin {self.name}")[1:-1].split()
            ])

        return self._fanin

    @property
    def fanout(self) -> set[Pin]:
        """Get fanout Pin objects from pin."""
        if not self._fanout:
            self._fanout = set([
                self.get_pin(p, self.pt)
                for p in self.pt.sendCommand(f"get_fanout {self.name}")[1:-1].split()
            ])

        return self._fanout

    @property
    def gate(self) -> Gate:
        """Get Gate object that pin is on."""
        return self._gate

    def get_pin_value(self) -> tuple[Literal["0", "1", "X"]]:
        """From a given pin name, find its value for the current gate report.

        Returns
        -------
        tupl[Literal["0", "1", "X"]]
            Tuple of values found in gate report string.

        Raises
        ------
        ValueError
            If pin name could not be found in gate report
        """
        gate_rpt_str = self._pt.sendCommand(f"report_gate {self.name}")
        pinname = self.name.split("/")[-1]
        gate_rpt_fields = gate_rpt_str.split()
        try:
            value_str = gate_rpt_fields[gate_rpt_fields.index(pinname) + 2]
        except ValueError:
            raise ValueError(f'Could not find pin {pinname} in gate report "{gate_rpt_str}"')

        val_tuple = tuple([v[0] for v in value_str[1:-1].split("-") if v.isnumeric()])

        return val_tuple
