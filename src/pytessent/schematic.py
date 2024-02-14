from pathlib import Path
from pytessent import PyTessent

class schematic:
    """Class for tessent flat schematic visulaizer functions"""

    # Function to create "tessent -shell" process and write log file to logfile argument
    def __init__ (self, logfileName : str):
        logfilePath = Path(logfileName)
        self.shell = PyTessent.launch(timeout=None, logfile=logfilePath, replace=1)

    # Function to display list of pins on the flat schematic 
    def displayPins (self, pins, message: str = "Component", levels: int = 0):
        pinList = '{{{}}}'.format(' '.join(map(str, pins)))
        result1 = self.shell.sendCommand(f"add_schematic_objects     {pinList} -highlight red")
        result2 = self.shell.sendCommand(f"add_schematic_callout     {pinList} -message \"{message}\"")
        if levels > 0:
            result3 = self.shell.sendCommand(f"add_schematic_connections {pinList} -forward  decision_point -distance_limit {levels} -highlight pink")
            result4 = self.shell.sendCommand(f"add_schematic_connections {pinList} -backward decision_point -distance_limit {levels} -highlight blue")
        else:
            result3 = ""
            result4 = ""
        result5 = self.shell.sendCommand(f"add_schematic_connections {pinList} -to {pinList} -distance_limit 3 -highlight green")
        print (result1 + result2 + result3 + result4 + result5)

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
    # TODO: If flat model is corrupted, raise exception
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

