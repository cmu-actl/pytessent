import re
import pexpect
from pathlib import Path
from typing import Union

from typing import Optional


class PyTessent:
    def __init__(
        self,
        process: pexpect.pty_spawn.spawn,
        expect_list: list,
        timeout: Optional[int],
    ):
        self.process = process
        self.expect_list = expect_list
        self.timeout = timeout

    def sendCommand(self, command: str, timeout: Optional[int] = None) -> str:
        """send command to active tessent shell process, get back resulting message

        Args:
            command (str): command to send to active tessent shell

        Raises:
            Exception: raised if command not found in string returned by self.process.before

        Returns:
            str: resulting message printed to shell after running command
        """

        self.process.sendline(command)
        self.process.expect(
            self.expect_list, timeout=timeout if timeout else self.timeout
        )

        # remove \r (leave \n)
        result = self.process.before.decode("utf-8").replace("\r", "")
        # remove weird backspace characters
        result = re.sub(r".\x08", "", result)

        # remove echoed command
        if command not in result:
            raise Exception(f"Command not found in result '{result}'")

        return result.split(f"{command}\n", 1)[1].rstrip()

    def close(self, force: bool = True):
        """close tessent shell process"""

        try:  # exit Tessent shell
            self.sendCommand("exit -force")
        except pexpect.exceptions.EOF:  # pexpect will throw exception, but we want to ignore it
            pass

        self.process.close(force=force)


class PyTessentFactory:
    def __init__(self, expect_list: list = ["SETUP> ", "ANALYSIS> "]) -> None:
        self.expect_list = expect_list
        self.open_procs = []

        return None

    def launch(
        self,
        dofile: Optional[Union[str, Path]] = None,
        logfile: Optional[Union[str, Path]] = None,
        replace: bool = False,
        arguments: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> PyTessent:
        """launch a tessent shell process using given options, returning corresponding PyTessent object

        Args:
            dofile (str or pathlib.Path, optional): path to TCL dofile to be used tessent -shell run
                Defaults to None (no dofile used, just launch tessent -shell).
            logfile (str or pathlib.Path, optional): path to logfile for tessent -shell run
                Defaults to None (do not create logfile).
            replace (bool, optional): should we include a "-replace" option, replacing logfile if it exists?
                Defaults to False (no replace flag).
            arguments (dict, optional): arguments passed to tessent -shell using "-arguments" option
                Defaults to None (no arguments).
            timeout (int, optional): timeout limit for process.expect() calls of created PyTessent object
                Defaults to None for no timeout.

        Returns:
            PyTessent: object for interacting with tessent -shell process
        """

        command_list = ["tessent -shell"]
        if dofile:
            command_list.append(f"-dofile {dofile}")
        if logfile:
            command_list.append(f"-logfile {logfile}")
        if replace:
            command_list.append("-replace")
        if arguments:
            command_list.append("-arguments")
            for k, v in arguments.items():
                command_list.append(f"{k}={v}")

        child = pexpect.spawn(" ".join(command_list))
        child.expect(self.expect_list, timeout=timeout)
        tessent_proc = PyTessent(child, expect_list=self.expect_list, timeout=timeout)
        self.open_procs.append(tessent_proc)

        return tessent_proc
