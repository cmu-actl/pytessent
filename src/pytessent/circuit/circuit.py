from __future__ import annotations

from pathlib import Path
import networkx as nx
import pickle

from pytessent import PyTessent
from pytessent.circuit.celltype import CellType
from pytessent.circuit.gate import Gate
from pytessent.circuit.pin import Pin
from pytessent.circuit.pinpath import PinPath
from pytessent.circuit.pattern import Pattern


class Circuit:
    """Represents a subcircuit from a larger Tessent flat model.

    Here, a circuit is defined as a collection of logically-related pins and gates

    Attributes
    ----------
    name : str
        Name given to circuit.
    pt : PyTessent
        PyTessent instance for executing Tessent-related tasks.
    pins : set[Pin]
        Pins in circuit.
    gates : set[Gate]
        Gates in circuit.
    celltypes : set[CellType]
        CellTypes used in circuit.
    inputs : set[Pin]
        Input pins to circuit.
    outputs : set[Pin]
        Output pins to circuit.
    defectsites : set[Pin]
        Defined defect sites in circuit.

    Methods
    -------
    add_pin(self, pin: Pin) -> None
        Add a pre-existing Pin object to the circuit.
    get_pin(self, name: str) -> Pin
        Get Pin object from name of pin, add to circuit pins.
    get_gate(self, name: str) -> Gate
        Get Gate object from name of gate, add to circuit gates.
    get_celltype(self, name: str) -> CellType
        Get CellType object from name of cell type, add to circuit cell types.
    define_input(self, pin: Pin) -> None
        Define a given pin as an input (add to input set).
    define_output(self, pin: Pin) -> None
        Define a given pin as an output (add to output set).
    define_defectsite(self, pin: Pin) -> None
        Define a given pin as a defect site (add to defectsite set).

    Class Methods
    -------------
    empty(cls, name: str, pt: PyTessent) -> Circuit
        Define a new empty circuit.
    """

    _circuits = []

    @classmethod
    def empty(cls, name: str, pt: PyTessent) -> Circuit:
        """Define a new empty circuit."""
        c = Circuit(name, pt)
        cls._circuits.append(c)
        return c

    def __repr__(self) -> str:
        return f"Circuit({self.name})"

    def __init__(self, name: str, pt: PyTessent) -> None:
        """Construct a Circuit object."""
        self._name: str = name
        self._pt: PyTessent = pt

        # all pins, gates, and celltypes in circuit
        self._pins: dict[str, Pin] = {}
        self._gates: dict[str, Gate] = {}
        self._celltypes: dict[str, CellType] = {}

        # sets of special pins
        self._inputs: set[Pin] = set()
        self._outputs: set[Pin] = set()
        self._defectsites: set[Pin] = set()

        # NetworkX graph
        self._gate_graph: nx.DiGraph = nx.DiGraph()
        self._pin_graph: nx.DiGraph = nx.DiGraph()
        self._pinpaths: list[PinPath] = []

    @property
    def name(self) -> str:
        """Get name of circuit."""
        return self._name

    @property
    def pt(self) -> PyTessent:
        """Get PyTessent instance associated with circuit."""
        return self._pt

    @property
    def pins(self) -> set[Pin]:
        """Get list of Pin objects present in circuit."""
        return set(self._pins.values())

    @property
    def gates(self) -> set[Gate]:
        """Get list of Gate objects present in circuit."""
        return set(self._gates.values())

    @property
    def celltypes(self) -> set[CellType]:
        """Get list of CellType objects used on Gates within circuit."""
        return set(self._celltypes.values())

    @property
    def inputs(self) -> set[Pin]:
        """Get defined inputs for circuit."""
        return self._inputs

    @property
    def outputs(self) -> set[Pin]:
        """Get defined outputs for circuit."""
        return self._outputs

    @property
    def defectsites(self) -> set[Pin]:
        """Get defined defect sites for circuit."""
        return self._defectsites

    @property
    def gate_graph(self) -> nx.DiGraph:
        """Get networkx graph of circuit."""
        if not self._gate_graph:
            self._gate_graph = self._to_gate_graph()
        return self._gate_graph

    @property
    def pin_graph(self) -> nx.DiGraph:
        """Get networkx graph of circuit."""
        if not self._pin_graph:
            self._pin_graph = self._to_pin_graph()
        return self._pin_graph

    def add_pin(self, pin: Pin, update: bool = True) -> None:
        """Add a pre-existing Pin object to the circuit."""
        if pin not in self.pins:
            self._pins[pin.name] = pin
            if update:  # add gate and celltype
                pin_gate = pin.gate
                self._gates[pin_gate.name] = pin_gate
                self._celltypes[pin_gate.celltype.name] = pin_gate.celltype

    def get_pin(self, name: str, update: bool = True) -> Pin:
        """Get Pin object from name of pin, add to circuit pins if new."""
        if name not in self._pins:
            self._pins[name] = Pin.get_pin(name, self.pt)
            if update:  # add gate and celltype
                pin_gate = self._pins[name].gate
                self._gates[pin_gate.name] = pin_gate
                self._celltypes[pin_gate.celltype.name] = pin_gate.celltype
        return self._pins[name]

    def get_gate(self, name: str, update: bool = True) -> Gate:
        """Get Gate object from name of gate, add to circuit gates."""
        if name not in self._gates:
            self._gates[name] = Gate(name, self.pt)
            if update:  # add gate and celltype
                gate_celltype = self._gates[name].celltype
                self._celltypes[gate_celltype.name] = gate_celltype
        return self._gates[name]

    def get_celltype(self, name: str) -> CellType:
        """Get CellType object from name of cell type, add to circuit cell types."""
        if name not in self._celltypes:
            self._celltypes[name] = CellType(name, self.pt)
        return self._celltypes[name]

    def define_input(self, pin: Pin) -> None:
        """Define a given pin as an input (add to input set)."""
        if pin not in self.pins:
            raise KeyError
        self._inputs.add(pin)

    def define_output(self, pin: Pin) -> None:
        """Define a given pin as an output (add to output set)."""
        if pin not in self.pins:
            raise KeyError
        self._outputs.add(pin)

    def define_defectsite(self, pin: Pin) -> None:
        """Define a given pin as a defect site (add to defectsite set)."""
        if pin not in self.pins:
            raise KeyError
        self._defectsites.add(pin)

    def _to_gate_graph(self) -> nx.DiGraph:
        """From circuit, produce NetworkX DiGraph."""
        # create empty graph
        G = nx.DiGraph()

        # use pins to add normal (non-io) nodes to graph
        G.add_nodes_from(
            [
                (
                    pin.gate.name,
                    {
                        "celltype": pin.gate.celltype.name,
                        "inputs": [p.name for p in pin.gate.inputs],
                        "outputs": [p.name for p in pin.gate.outputs],
                        "io": None,
                    },
                )
                for pin in self.pins - (self.inputs | self.outputs)
            ]
        )

        # use pins to add io nodes to graph
        G.add_nodes_from(
            [
                (
                    pin.name,
                    {
                        "celltype": pin.gate.celltype.name,
                        "inputs": [p.name for p in pin.gate.inputs],
                        "outputs": [p.name for p in pin.gate.outputs],
                        "io": "INPUT",
                    },
                )
                for pin in self.inputs
            ]
        )

        G.add_nodes_from(
            [
                (
                    pin.name,
                    {
                        "celltype": pin.gate.celltype.name,
                        "inputs": [p.name for p in pin.gate.inputs],
                        "outputs": [p.name for p in pin.gate.outputs],
                        "io": "OUTPUT",
                    },
                )
                for pin in self.outputs
            ]
        )

        # add edges
        for pin in self.pins - self.inputs:
            if pin.direction == "input":
                sink = pin.name if pin in self.outputs else pin.gate.name

                for ipin in pin.fanin:
                    source = ipin.name if ipin in self.inputs else ipin.gate.name
                    G.add_edge(source, sink)

        return G

    def _to_pin_graph(self) -> nx.DiGraph:
        """From circuit, produce NetworkX DiGraph."""
        # create empty graph
        G = nx.DiGraph()

        # use pins to add normal (non-io) nodes to graph
        G.add_nodes_from(self.pins)

        # add edges
        for pin in self.pins - self.inputs:
            [G.add_edge(ipin, pin) for ipin in pin.fanin]

        return G

    def plot_graph(
        self, outfile: Path | None = None, pattern: Pattern | None = None
    ) -> None:
        if not outfile:
            if pattern:
                outfile = Path(f"{self.name}_pattern{pattern.index}_graph.png")
            else:
                outfile = Path(f"{self.name}_graph.png")

        G = self.gate_graph

        A = nx.nx_agraph.to_agraph(G)

        A.add_subgraph(
            [k for k, v in G.nodes.items() if v["io"] == "INPUT"], rank="same"
        )
        A.add_subgraph(
            [k for k, v in G.nodes.items() if v["io"] == "OUTPUT"], rank="same"
        )
        A.add_subgraph([k for k, v in G.nodes.items() if not v["io"]])

        # plt.figure(figsize=(20, 20))
        for a in A.nodes_iter():
            # different colors for different node types
            if a.attr["io"] == "INPUT":
                a.attr["fillcolor"] = "blue"
            elif a.attr["io"] == "OUTPUT":
                a.attr["fillcolor"] = "red"
            else:
                a.attr["fillcolor"] = "gray"

            # labels as celltypes
            a.attr["label"] = a.attr["celltype"]
            a.attr["shape"] = "box"

        A.node_attr["style"] = "filled"

        A.draw(outfile, prog="dot", args='-Grankdir="LR" -Efontsize=5')

    def to_verilog(self, outfile: Path | None = None) -> None:
        """From a circuit with a set of defined pins, write out a Verilog netlist.

        Parameters
        ----------
        outfile : Path, optional
            File to write Verilog, by default None
        """
        if not outfile:
            outfile = Path(f"{self.name}_backcone.v")

        verilog_lines = []

        # define module line
        verilog_lines.append(
            f"module {self.name}({', '.join([p.vname for p in list(self.inputs) + list(self.outputs)])});"
        )

        # define inputs and outputs
        for opin in self.outputs:
            verilog_lines.append(f"  output {opin.vname};")
        for ipin in self.inputs:
            verilog_lines.append(f"  input {ipin.vname};")

        verilog_lines.append("")

        # get all nets
        pin2net = {
            p: self.pt.send_command(f"get_fanout {p.name} -stop_on net")[1:-1]
            for p in self.pins
            if p.direction == "output"
        } | {
            p: self.pt.send_command(f"get_fanin {p.name} -stop_on net")[1:-1]
            for p in self.pins
            if p.direction == "input"
        }

        nets = set(pin2net.values())
        for net in nets:
            verilog_lines.append(f"  wire {net};")

        verilog_lines.append("")

        # connect subcircuit inputs and outputs to nets
        for opin in self.outputs:
            verilog_lines.append(f"  assign {opin.vname} = {pin2net[opin]};")
        for ipin in self.inputs:
            verilog_lines.append(f"  assign {pin2net[ipin]} = {ipin.vname};")

        verilog_lines.append("")

        # write out gates
        for gate in self.gates:
            if (self.inputs & set(gate.outputs)) or (self.outputs & set(gate.inputs)):
                continue
            pinstr = ", ".join(
                [f".{p.leaf} ({pin2net[p]})" for p in gate.inputs + gate.outputs]
            )
            verilog_lines.append(f"  {gate.celltype.name} {gate.vname} ({pinstr});")

        verilog_lines.append("")

        verilog_lines.append("endmodule")
        with open(outfile, "w") as f:
            f.write("\n".join(verilog_lines))

    def _get_all_pinpaths(self) -> list[PinPath]:
        """From Circuit pin graph, get all paths from inputs to outputs."""
        all_pinpaths = []
        for ipin in self.inputs:
            for opin in self.outputs:
                for path in nx.all_simple_paths(self.pin_graph, ipin, opin):
                    all_pinpaths.append(PinPath(path, len(all_pinpaths)))

        return all_pinpaths

    @property
    def pinpaths(self) -> list[PinPath]:
        if not self._pinpaths:
            self._pinpaths = self._get_all_pinpaths()
        return self._pinpaths

    def get_pinpaths(
        self,
        from_pin: Pin | None = None,
        to_pin: Pin | None = None,
        through_pins: list[Pin] | None = None,
    ) -> list[PinPath]:
        """Get list of paths meeting specified requirements.

        Parameters
        ----------
        from_pin : Pin, optional
            First pin in path, by default None
        to_pin : Pin, optional
            Last pin in path, by default None
        through_pins : list[Pin], optional
            List of pins that must be in path, by default None

        Returns
        -------
        list[PinPath]
            List of filtered paths
        """

        # start with all paths
        filter_pinpaths = self.pinpaths

        # filter based on from pin
        if from_pin:
            filter_pinpaths = [
                pinpath for pinpath in filter_pinpaths if pinpath.pins[0] == from_pin
            ]

        # filter based on to pin
        if to_pin:
            filter_pinpaths = [
                pinpath for pinpath in filter_pinpaths if pinpath.pins[-1] == to_pin
            ]

        # filter based on to pin
        if through_pins:
            filter_pinpaths = [
                pinpath
                for pinpath in filter_pinpaths
                if all([t in pinpath.pins for t in through_pins])
            ]

        return filter_pinpaths

    def to_pickle(self, outfile: Path, patterns: list[Pattern] | None = None) -> None:
        """Write out a pickle file for the circuit (for easier reloading).

        Has format:
            {"name": str,
            "pins": [{"name": str, "direction": str, "input": bool, "output": bool, "defectsite": bool, "fanin" [int, ..], "fanout": [int, ..]}, {}],
            "patterns": {int: {"pins": [(str, str), ..], "activatedpinpaths":  [int, ..]},
            "pinpaths": [[int, ..], []..]

        Parameters
        ----------
        outfile : Path
            File to write pickle file.
        patterns : list[Pattern], optional
            List of patterns to write to pickle (related to circuit), by default None
        """

        circuit_dict = {}

        circuit_dict["name"] = self.name

        # store pins
        pin_list = list(self.pins)
        circuit_dict["pins"] = []
        for pin in pin_list:
            pin_dict = {
                "name": pin.name,
                "direction": pin.direction,
                "input": pin in self.inputs,
                "output": pin in self.outputs,
                "defectsite": pin in self.defectsites,
                "fanin": [
                    pin_list.index(fpin) for fpin in pin.fanin if fpin in pin_list
                ],
                "fanout": [
                    pin_list.index(fpin) for fpin in pin.fanout if fpin in pin_list
                ],
            }

            circuit_dict["pins"].append(pin_dict)

        # store pinpaths
        circuit_dict["pinpaths"] = []
        for pinpath in self.pinpaths:
            circuit_dict["pinpaths"].append(
                [pin_list.index(pin) for pin in pinpath.pins]
            )

        # store patterns
        if patterns:
            circuit_dict["patterns"] = {}
            for pattern in patterns:
                circuit_dict["patterns"][pattern.index] = {}
                circuit_dict["patterns"][pattern.index]["pins"] = [
                    pattern.pinvalues[pin] for pin in pin_list
                ]
                circuit_dict["patterns"][pattern.index]["activatedpinpaths"] = [
                    self.pinpaths.index(pinpath)
                    for pinpath in pattern.activatedpinpaths
                ]

        # write to pickle file
        with open(outfile, "wb") as f:
            pickle.dump(circuit_dict, f)

    @classmethod
    def from_pickle(
        cls, infile: Path, pt: PyTessent, name: str | None = None
    ) -> tuple[Circuit, list[Pattern]]:
        """Read in a circuit pickle file and return Circuit and Pattern objects.

        Parameters
        ----------
        infile : Path
            Circuit pickle file
        pt : PyTessent
            Active PyTessent instance for querying
        name : str, optional
            Circuit name, by default use name in pickle file

        Returns
        -------
        tuple[Circuit, list[Pattern]]
            Circuit object and list of Pattern objects
        """
        with open(infile, "rb") as f:
            circuit_dict = pickle.load(f)

        name = name if name else circuit_dict["name"]
        if not name:
            raise ValueError("Could not get circuit name")

        c = Circuit(name, pt)

        # initialize pins
        pin_list = [c.get_pin(pin_dict["name"]) for pin_dict in circuit_dict["pins"]]

        # define inputs, outputs, defectsites
        [
            c.define_input(c.get_pin(pin_dict["name"]))
            for pin_dict in circuit_dict["pins"]
            if pin_dict["input"]
        ]
        [
            c.define_output(c.get_pin(pin_dict["name"]))
            for pin_dict in circuit_dict["pins"]
            if pin_dict["output"]
        ]
        [
            c.define_defectsite(c.get_pin(pin_dict["name"]))
            for pin_dict in circuit_dict["pins"]
            if pin_dict["defectsite"]
        ]

        # define pinpaths
        pinpath_list = [
            PinPath([pin_list[pin_ind] for pin_ind in pinpath], i)
            for i, pinpath in enumerate(circuit_dict["pinpaths"])
        ]
        c._pinpaths = pinpath_list

        # define patterns
        patterns = []
        if "patterns" in circuit_dict:
            for pattern_ind, pattern_dict in circuit_dict["patterns"].items():
                pat = Pattern(pattern_ind)
                pat._pinvalues = {
                    pin_list[pin_ind]: v
                    for pin_ind, v in enumerate(pattern_dict["pins"])
                }
                [
                    pat.add_activated_pinpath(pinpath_list[pinpath_ind])
                    for pinpath_ind in pattern_dict["activatedpinpaths"]
                ]
                patterns.append(pat)

        return c, patterns
