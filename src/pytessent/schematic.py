from pathlib import Path
from pytessent import PyTessent

class schematic:
    """Class for tessent flat schematic visualizer functions"""

    # Function to create "tessent -shell" process and write log file to logfile argument
    def __init__ (self, logfileName : str):
        logfilePath = Path(logfileName)
        self.shell = PyTessent.launch(timeout=None, logfile=logfilePath, replace=1)

    # Function to display list of pins on the flat schematic 
    def displayPins (self, pin_dict: dict, message: str = "Component", levels: int = 1, enEP: bool = False,
                     voxelColor: str = "pink", fwdColor: str = "green", bwdColor: str = "blue", 
                     ipinColor: str = "red", iopinColor: str = "orange", opinColor: str = "yellow"):
        pins  = pin_dict.get('pinPath'  , [])
        ipins = pin_dict.get('I_pinpath', [])
        opins = pin_dict.get('O_pinpath', [])
        io_pins = list(set(ipins).intersection(set(opins)))
        pinList = '{{{}}}'.format(' '.join(map(str, pins)))
        ipinList = '{{{}}}'.format(' '.join(map(str, ipins)))
        opinList = '{{{}}}'.format(' '.join(map(str, opins)))
        iopinList = '{{{}}}'.format(' '.join(map(str, io_pins)))
        result = "\nDisplaying Pins: \n"
        result += self.shell.sendCommand(f"add_schematic_objects     {pinList} -highlight {voxelColor}")
        result += self.shell.sendCommand(f"add_schematic_callout     {pinList} -message \"{message}\"")
        if enEP:
            result += self.shell.sendCommand(f"add_schematic_connections {pinList} -forward  end_point      -distance_limit {levels} -highlight {fwdColor}")
            result += self.shell.sendCommand(f"add_schematic_connections {pinList} -backward end_point      -distance_limit {levels} -highlight {bwdColor}")
        result += self.shell.sendCommand(f"add_schematic_connections {pinList} -forward  decision_point -distance_limit {levels} -highlight {fwdColor}")
        result += self.shell.sendCommand(f"add_schematic_connections {pinList} -backward decision_point -distance_limit {levels} -highlight {bwdColor}")
        result += self.shell.sendCommand(f"add_schematic_objects     {ipinList} -highlight {ipinColor}")
        result += self.shell.sendCommand(f"add_schematic_objects     {opinList} -highlight {opinColor}")
        result += self.shell.sendCommand(f"add_schematic_objects     {iopinList}  -highlight {iopinColor}")
        # result += self.shell.sendCommand(f"add_schematic_connections {pinList} -to {pinList} -distance_limit 1 -highlight {voxelColor}")
        if (result != "\nDisplaying Pins: \n"):
            print (f"{result}\n")

    # Clear all schematic objects
    def clearSchm (self):
        self.shell.sendCommand("delete_schematic_objects -all")

    # send tessent command to set context
    def setContxt (self, context : str):
        self.shell.sendCommand(f"set_context patterns -{context}")

    # send tessent command as is
    def shellCommand (self, command : str) -> str:
        return self.shell.sendCommand(command)

    # Read Tessent flat model
    def readFlatModel (self, flat_model_path : str):
        flatModelPath = Path(flat_model_path)
        result = self.shell.sendCommand(f"read_flat_model {flatModelPath}")
        print (result)

    # Read pattern file
    def readPattFile (self, pattern_file_path : str):
        patternFilePath = Path(pattern_file_path)
        result = self.shell.sendCommand(f"read_patterns {patternFilePath}")
        print (result)

    # Read delay data from sdf file
    def readSDFfile (self, sdf_file_path : str):
        sdfFilePath = Path(sdf_file_path)
        self.shell.sendCommand("set_fault_type transition")
        result = self.shell.sendCommand(f"read_sdf {sdfFilePath}")
        print (result)

    # set gate report with arguments
    def setGateReport (self, *args):
        switches = " ".join(args)
        print (f"Setting gate report with : {switches}")
        result = self.shell.sendCommand(f"set_gate_report {switches}")
        print (result)

    # close tessent -shell process
    def closeShell (self):
        self.shell.close()

