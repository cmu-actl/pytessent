import re
import pexpect


class PyTessent:
    def __init__(
        self, process: pexpect.pty_spawn.spawn, expect_list: list, timeout: int
    ):
        self.process = process
        self.expect_list = expect_list
        self.timeout = timeout

    def sendCommand(self, command: str, timeout: int = None) -> str:
        """send command to active tessent shell process, get back resulting message

        Args:
            command (str): command to send to active tessent shell

        Raises:
            Exception: raised if command not found in string returned by self.process.before

        Returns:
            str: resulting message printed to shell after running command
        """

        self.process.sendline(command)  # send command
        if not timeout:  # overwrite timeout if specified for specific command
            timeout = self.timeout
        self.process.expect(self.expect_list, timeout=timeout)  # wait for it to finish

        byte_result = self.process.before  # pull result
        str_result = byte_result.decode("utf-8")

        str_result = str_result.replace("\r", "")  # remove \r (leave \n)
        str_result = re.sub(
            r".\x08", "", str_result
        )  # remove weird backspace characters...

        # remove command from return string...
        if not str_result.find(f"{command}\n") == 0:
            raise Exception(f"Command not found in before string... ({str_result})")

        str_result = str_result.replace(f"{command}\n", "", 1).rstrip()

        return str_result

    def close(self):
        """close tessent shell process"""
        self.process.close()


class PyTessentFactory:
    def __init__(self, expect_list: list = ["SETUP> ", "ANALYSIS> "]) -> None:
        self.expect_list = expect_list
        self.pytessents = []

        return None

    def launch(
        self,
        dofile: str = None,
        logfile: str = None,
        replace: bool = False,
        arguments: dict = None,
        timeout: int = 10000,
    ) -> PyTessent:
        """launch a tessent shell process using given options, returning corresponding PyTessent object

        Args:
            dofile (str, optional): path to TCL dofile to be used tessent -shell run
                Defaults to None (no dofile used, just launch tessent -shell).
            logfile (str, optional): path to logfile for tessent -shell run
                Defaults to None (do not create logfile).
            replace (bool, optional): should we include a "-replace" option, replacing logfile if it exists?
                Defaults to False (no replace flag).
            arguments (dict, optional): arguments passed to tessent -shell using "-arguments" option
                Defaults to None (no arguments).
            timeout (int, optional): timeout limit for process.expect() calls of created PyTessent object
                Defaults to 120.

        Returns:
            PyTessent: object for interacting with tessent -shell process
        """

        command_list = ["tessent -shell"]
        if dofile:  # dofile path
            command_list.append(f"-dofile {dofile}")
        if logfile:  # logfile path
            command_list.append(f"-logfile {logfile}")
        if replace:  # replace flag
            command_list.append("-replace")
        if arguments:  # handle input arguments
            command_list.append("-arguments")
            for k, v in arguments.items():
                command_list.append(f"{k}={v}")

        command = " ".join(command_list)  # construct command
        child = pexpect.spawn(command)  # create process
        child.expect(self.expect_list, timeout=timeout)  # wait for it to be ready for commands
        tessent_process = PyTessent(
            child, expect_list=self.expect_list, timeout=timeout
        )  # create PyTessent object

        self.pytessents.append(tessent_process)  # track open processes

        return tessent_process
