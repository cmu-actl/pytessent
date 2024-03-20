
from pytessent import schematic

# create "tessent -shell" process and write log file to tessent.log
log_file_name = "tessent.log"
pt_shell = schematic(log_file_name)

# send tessent command to set context
schematic.setContxt(pt_shell, "scan")

# Read Tessent flat model
flat_model_path = "/storage/akachint/git/pepr/bms/s1196/s1196.flat.gz"
schematic.readFlatModel(pt_shell, flat_model_path)

# Pins to display
pins = [ "s1196_i_g5717__9945/Y", "s1196_i_g5781__8246/Y", "G4_flop_i_qi_reg/Q", ]
#['g10194/Y', 'g10158__7098/Y', 'g10208__1617/Y']

# Display pins 
schematic.displayPins(pt_shell, pins)

# # add faults to design, create patterns
# pt.sendCommand("add_faults -all")
# pt.sendCommand("create_patterns")

# # report coverage stats, store in string (for parsing, etc...)
# stats_str = pt.sendCommand("report_statistics")

# close tessent -shell process
while True:
    user_input = input("Type 'close' to exit or command to execute on Tshell: ")

    if user_input.lower() == 'close' or user_input.lower() == 'exit':
        print("Closing the program.")
        schematic.clearSchm(pt_shell)
        schematic.closeShell(pt_shell)
        break  # Exit the loop and end the program
    else:
        schematic.shellCommand(pt_shell, user_input)

