from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal

from pytessent.circuit.gate import Gate
from pytessent.circuit.utils import parse_name, parse_name_list, CircuitElementNotFoundException, verilog_name

if TYPE_CHECKING:
    from pytessent import PyTessent


class Pin(ABC):
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
    net_itr_limit = 3

    @classmethod
    def get_pin(cls, name: str, pt: PyTessent) -> Pin:
        """Get pin object from name of pin."""
        if name not in cls._pins:  # get pin if it has already been created
            if cls.verify_pin(name, pt): # otherwise, create
                cls._pins[name] = GatePin(name, pt)
            elif cls.verify_primarypin(name, pt):
                pin_direction = cls.pin_direction(name, pt)
                if pin_direction == "input":
                    cls._pins[name] = PrimaryInput(name, pt)
                elif pin_direction == "output":
                    cls._pins[name] = PrimaryOutput(name, pt)
            else:
                raise CircuitElementNotFoundException(f"Pin {name} not found in design.")

        return cls._pins[name]

    @staticmethod
    def pin_direction(name: str, pt: PyTessent) -> str:
        """Get direction of pin."""
        pin_direction = pt.send_command(f"get_single_attribute_value {name} -name direction")
        if pin_direction not in ["input", "output"]:
            raise ValueError(f"Unknown pin direction: {pin_direction}")
        return pin_direction

    def __init__(self, name: str, pt: PyTessent) -> None:
        """Construct Pin object."""
        self._name: str = name
        self._pt: PyTessent = pt
        self._direction: str = self.pin_direction(name, pt)

    @staticmethod
    def verify_pin(pin: str, pt: PyTessent) -> bool:
        """Verify that pin exists in the design."""
        return "Error" not in pt.send_command(f"get_pin {pin}")

    @staticmethod
    def verify_primarypin(pin: str, pt: PyTessent) -> bool:
        """Verify that primary input/output pin exists in the design."""
        return "Error" not in pt.send_command(f"get_port {pin}")

    @property
    def name(self) -> str:
        """Get name of pin."""
        return self._name

    @property
    def vname(self) -> str:
        """Get verilog name of pin."""
        return verilog_name(self.name)

    @property
    def netname(self) -> str:
        """Get net name corresponding to pin."""
        return f"{verilog_name(self.name)}_net"

    @property
    def pt(self) -> PyTessent:
        """Get PyTessent instance associated with pin."""
        return self._pt

    @property
    def direction(self) -> str:
        """Get direction (input or output) of pin."""
        return self._direction

    @property
    def net(self) -> str:
        """Get net name of pin."""
        if self.direction == "output":
            return self.netname
        elif self.direction == "input":
            return self.fanin.pop().netname
        else:
            raise ValueError(f"Unknown pin direction: {self.direction}")

    @property
    def fanin(self) -> set[Pin]:
        """Get fanin Pin objects from pin."""
        if not self._fanin:
            name_list_str = self.pt.send_command(f"get_name_list [get_fanin {self.name}]")
            fanin_pins = parse_name_list(name_list_str)
            self._fanin = set(
                [
                    self.get_pin(p, self.pt)
                    for p in fanin_pins
                ]
            )
            if self.direction == "input" and len(self.fanin) > 1:
                raise ValueError(f"Input pin {self.name} has multiple fanin pins: {self.fanin}")

        return self._fanin

    @property
    def fanout(self) -> set[Pin]:
        """Get fanout Pin objects from pin."""
        if not self._fanout:
            name_list_str = self.pt.send_command(f"get_name_list [get_fanout {self.name}]")
            fanout_pins = parse_name_list(name_list_str)
            self._fanout = set(
                [
                    self.get_pin(p, self.pt)
                    for p in fanout_pins
                    if not self.pt.send_command(f"get_attribute_value_list {p} -name object_type") == "net"
                ]
            )

        return self._fanout


class GatePin(Pin):
    """Represents pin on a gate instance."""

    def __repr__(self) -> str:
        return f"GatePin({self.name})"

    def __init__(self, name: str, pt: PyTessent) -> None:
        if not self.verify_pin(name, pt):
            raise CircuitElementNotFoundException(f"Pin {name} not found in design.")

        super().__init__(name, pt)

        # leave fanin/fanout blank, will fill when called
        self._fanin: set[Pin] = set()
        self._fanout: set[Pin] = set()

        self._gate: Gate = Gate.from_pin(self)
        self._leaf = name.split("/")[-1]

    @property
    def leaf(self) -> str:
        """Leaf name of pin."""
        return self._leaf

    @property
    def gate(self) -> Gate:
        """Get Gate object that pin is on."""
        return self._gate

    def get_pin_value(self) -> tuple[Literal["0", "1", "X"], ...]:
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
        gate_rpt_str = self._pt.send_command(f"report_gate {self.name}")
        pinname = self.name.split("/")[-1]
        gate_rpt_fields = gate_rpt_str.split()
        try:
            value_str = gate_rpt_fields[gate_rpt_fields.index(pinname) + 2]
        except ValueError:
            raise ValueError(
                f'Could not find pin {pinname} in gate report "{gate_rpt_str}"'
            )

        return tuple(
            [v[0] for v in value_str[1:-1].split("-") if v.isnumeric()]  # type: ignore
        )


class PrimaryInput(Pin):
    """Represents a primary input pin."""

    def __repr__(self) -> str:
        return f"PrimaryInput({self.name})"

    def __init__(self, name: str, pt: PyTessent) -> None:
        super().__init__(name, pt)

        # leave fanin/fanout blank, will fill when called
        self._fanout: set[Pin] = set()

    @property
    def fanin(self) -> set[Pin]:
        return set([])

    @property
    def net(self) -> str:
        """Get net name of pin."""
        return self.netname


class PrimaryOutput(Pin):
    """Represents a primary ourtput pin."""

    def __repr__(self) -> str:
        return f"PrimaryOutput({self.name})"

    def __init__(self, name: str, pt: PyTessent) -> None:
        # leave fanin/fanout blank, will fill when called
        self._fanin: set[Pin] = set()
        super().__init__(name, pt)

    @property
    def fanout(self) -> set[Pin]:
        return set([])

    @property
    def net(self) -> str:
        """Get net name of pin."""
        return self.fanin.pop().netname
