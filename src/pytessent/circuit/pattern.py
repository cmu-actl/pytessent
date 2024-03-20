from __future__ import annotations

from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from pytessent.circuit.circuit import Circuit
    from pytessent.circuit.pin import Pin
    from pytessent.circuit.pinpath import PinPath


class Pattern:
    """Represents a single pattern within the pattern set.

    Attributes
    ----------
    index : int
        Index (number) of pattern within pattern set.
    pinvalues : dict[Pin, tuple(Literal["0", "1", "X"])]
        Dictionary mapping Pin object to tuple of values on pin for pattern.
    simcontext : str
        Name of simulation context.

    Methods
    -------
    get_circuit_values(self, c: Circuit) -> None
        Get all values of circuit pins for given pattern, store in pinvalues dict.
    create_pattern_sim_context(self, c: Circuit, v: int = -1) -> None
        Simulate an X on a circuit pin, see where it propagates
    """

    def __repr__(self) -> str:
        return f"Pattern({self.index})"

    def __init__(self, index: int) -> None:
        self._index = index
        self._pinvalues: dict[Pin, tuple[Literal["0", "1", "X"], ...]] = {}
        self._simcontext = f"pattern_{self.index}"
        self._activatedpinpaths: list[PinPath] = []

    @property
    def index(self) -> int:
        """Get pattern index (number)"""
        return self._index

    @property
    def pinvalues(self) -> dict[Pin, tuple[Literal["0", "1", "X"], ...]]:
        """Get pin values dictionary."""
        return self._pinvalues

    @property
    def simcontext(self) -> str:
        """Get name of simulation context."""
        return self._simcontext

    @property
    def activatedpinpaths(self) -> list[PinPath]:
        """Get list of activated pin paths in pattern."""
        return self._activatedpinpaths

    def get_circuit_values(self, c: Circuit) -> None:
        """Get all values of circuit pins for given pattern, store in pinvalues dict.

        Parameters
        ----------
        c : Circuit
            Circuit with pins to check
        """
        c.pt.send_command(f"set_gate_report pattern_index {self.index} -external")
        for pin in c.pins:
            if pin not in self._pinvalues:
                self._pinvalues[pin] = pin.get_pin_value()

    def create_pattern_sim_context(self, c: Circuit, v: int = -1) -> None:
        """Create a simulation context representing the values for a given pattern.

        Parameters
        ----------
        c : Circuit
            Circuit with pins to apply simulation forces.
        v : int, optional
            Which value of pattern to use, by default -1 (last)
        """
        # get the circuit simulation values
        self.get_circuit_values(c)

        # create a new simulation context, using "stable_capture" context as template
        c.pt.send_command(
            f"add_simulation_context {self.simcontext} -copy_from stable_capture"
        )
        c.pt.send_command(f"set_current_simulation_context {self.simcontext}")

        # simulate the values on the circuit pins for the pattern
        for pin in c.inputs:
            c.pt.send_command(
                f"add_simulation_forces {{{pin.name}}} -value {self.pinvalues[pin][v]}"
            )

        c.pt.send_command("simulate_forces")

    def simulate_x_at_pin(self, c: Circuit, pin: Pin, v: int = -1):
        """Simulate an X on a circuit pin, see where it propagates.

        Parameters
        ----------
        c : Circuit
            Circuit to check pin results during simulation.
        pin : Pin
            Pin to simulate an X on.
        """

        # add an x on defined pin and simulate
        c.pt.send_command(f"add_simulation_forces {{{pin.name}}} -value X")
        c.pt.send_command("simulate_forces")

        # get the values of all pins in circuit
        sim_results = {}
        for p in c.pins:
            sim_results[p] = c.pt.send_command(
                f"get_simulation_value_list {{{p.name}}}"
            )

        # get results of x simulation: what pins get an x, does any output have a pin
        res = (
            set([p for p, val in sim_results.items() if val == "X"]),
            set([p for p in c.outputs if sim_results[p] == "X"]),
        )

        # revert pin value to original in simulation context
        c.pt.send_command(
            f"add_simulation_forces {{{pin.name}}} -value {self.pinvalues[pin][v]}"
        )

        return res

    def add_activated_pinpath(self, pinpath: PinPath) -> None:
        """Append an activated pinpath to pattern list."""
        self._activatedpinpaths.append(pinpath)
