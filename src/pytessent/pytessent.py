from __future__ import annotations

import re
from pathlib import Path
from shutil import which

import pexpect  # type: ignore


class PyTessent:
    """Class for interacting with Tessent shell process."""

    _defaultexpectlist: list[str] = ["SETUP> ", "ANALYSIS> "]
    _pytessents: list[PyTessent] = []

    def __init__(
        self,
        process: pexpect.pty_spawn.spawn,
        tessentpath: Path,
        expectlist: list[str],
        timeout: int | None,
    ):
        self._process = process
        self._tessentpath = tessentpath
        self._expectlist = expectlist
        self._timeout = timeout

    @property
    def process(self) -> pexpect.pty_spawn.spawn:
        """PyTessent process."""
        return self._process

    @property
    def tessentpath(self) -> Path:
        """Path to the Tessent executable used by PyTessent."""
        return self._tessentpath

    @property
    def expectlist(self) -> list[str]:
        """List of strings to expect from the Tessent shell."""
        return self._expectlist

    @property
    def timeout(self) -> int | None:
        """Timeout limit for process.expect() calls."""
        return self._timeout

    @timeout.setter
    def timeout(self, timeout: int | None) -> None:
        self._timeout = timeout

    @classmethod
    def launch(
        cls,
        dofile: Path | str | None = None,
        logfile: Path | str | None = None,
        replace: bool = False,
        arguments: dict[str, str] | None = None,
        timeout: int | None = None,
        tessentpath: Path | None = None,
        expectlist: list[str] | None = None,
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
            tessentpath (str or pathlib.Path, optional): path to tessent executable
                Defaults to None (use "tessent" from PATH).
            timeout (int, optional): timeout limit for process.expect() calls of created PyTessent object
                Defaults to None for no timeout.

        Returns:
            PyTessent: object for interacting with tessent -shell process

        Notes:
            - if tessentpath is defined, use that directly
            - if tessentpath is None, use from $PATH
            - if expectlist is None, will use default expectlist
        """

        if not tessentpath:
            if which("tessent"):  # if tessent in PATH, use it
                tessentpath = Path("tessent")

        if not tessentpath or (
            tessentpath != Path("tessent") and not tessentpath.exists()
        ):
            raise FileNotFoundError(
                f"Could not find Tessent executable path at {tessentpath}"
            )

        if not expectlist:
            expectlist = cls._defaultexpectlist

        command_list = [tessentpath, "-shell"]
        if dofile:
            command_list.append(f"-dofile {dofile}")
        if logfile:
            command_list.append(f"-logfile {logfile}")
        if logfile and replace:
            command_list.append("-replace")
        if arguments:
            command_list.append("-arguments")
            for k, v in arguments.items():
                command_list.append(f"{k}={v}")

        command_str = " ".join([str(c) for c in command_list])
        child = pexpect.spawn(command_str)
        child.expect(expectlist, timeout=timeout)
        pt = PyTessent(
            process=child,
            tessentpath=tessentpath,
            expectlist=expectlist,
            timeout=timeout,
        )

        cls._pytessents.append(pt)

        return pt

    def closeall(cls) -> None:
        """Close all PyTessent Processes."""
        while cls._pytessents:
            cls._pytessents.pop().close()

    def sendCommand(self, command: str, timeout: int | None = None) -> str:
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
            self.expectlist, timeout=timeout if timeout else self.timeout
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
        except (
            pexpect.exceptions.EOF
        ):  # pexpect will throw exception, but we want to ignore it
            pass

        self.process.close(force=force)

        PyTessent._pytessents.remove(self)

    def __exit__(self):
        self.close()