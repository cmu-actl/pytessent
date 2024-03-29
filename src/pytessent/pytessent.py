from __future__ import annotations

import re
from pathlib import Path
from shutil import which

import pexpect  # type: ignore


class TessentCommandError(Exception):
    pass


def get_tessent_exe(specified_exe: str | Path | None = None) -> str:
    """Get the path to the Tessent executable to use.

    If `specified_exe` is not `None`, it will be used. Otherwise, the exe will be
    queried using `which`. In either case, if the exe does not exist, a
    `FileNotFoundError` will be raised.
    """
    if not specified_exe:
        # Check for tessent exe on $PATH
        if not which("tessent"):
            raise FileNotFoundError("Could not find 'tessent' executable in path")
        return "tessent"
    elif str(specified_exe) != "tessent" and not Path(specified_exe).exists():
        raise FileNotFoundError(
            f"Could not find Tessent executable at '{specified_exe}'"
        )
    return str(specified_exe)


class PyTessent:
    """Class for interacting with a Tessent shell process."""

    _default_expect_patterns: list[str] = ["SETUP> ", "ANALYSIS> "]

    def __init__(
        self,
        do_file: Path | str | None = None,
        log_file: Path | str | None = None,
        replace: bool = False,
        arguments: dict[str, str] | None = None,
        timeout: int | None = None,
        tessent_exe: Path | str | None = None,
        expect_patterns: list[str] | None = None,
    ) -> None:
        """Launch a new tessent shell process using given options.

        Can also be used as a context manager to automatically close the Tessent process
        on exit.

        Args:
            do_file: path to TCL script to run in Tessent.
            log_file: path to save Tessent log file to.
            replace: replace existing log file if it already exists.
            arguments: arguments passed to Tessent -shell using "-arguments" option.
            timeout: timeout limit for each Tessent command. If `None`, no timeout.
            tessent_exe: tessent executable to launch Tessent from. If `None`, queried
                from the $PATH variable.
            expect_patterns: patterns to expect from Tessent indicating it is ready for
                input. If `None`, checks for "SETUP> " and "ANALYSIS> ".
        """
        self.timeout = timeout
        self._tessent_exe = get_tessent_exe(specified_exe=tessent_exe)

        if not expect_patterns:
            self._expect_patterns = self._default_expect_patterns
        else:
            self._expect_patterns = expect_patterns

        launch_command_parts = [self._tessent_exe, "-shell"]
        if do_file:
            launch_command_parts.append(f"-dofile {do_file}")
        if log_file:
            launch_command_parts.append(f"-logfile {log_file}")
            if replace:
                launch_command_parts.append("-replace")
        if arguments:
            launch_command_parts.append("-arguments")
            for k, v in arguments.items():
                launch_command_parts.append(f"{k}={v}")

        self._process = pexpect.spawn(" ".join(launch_command_parts))
        self._process.expect(self._expect_patterns, timeout=self.timeout)  # type: ignore

    @property
    def process(self) -> pexpect.pty_spawn.spawn:
        """The Tessent process."""
        return self._process

    @property
    def tessent_exe(self) -> str:
        """The Tessent executable used by PyTessent."""
        return self._tessent_exe

    @property
    def expect_patterns(self) -> list[str]:
        """Patterns expected from the Tessent shell."""
        return self._expect_patterns

    def send_command(self, command: str, timeout: int | None = None) -> str:
        """Send a command to tessent and get back the resulting message.

        Args:
            command: command to send to active tessent shell.

        Raises:
            TessentCommandError: raised if the command was not found echoed in the
                resulting output.

        Returns:
            resulting message printed to shell after running command.
        """
        self.process.sendline(command)
        self.process.expect(
            self.expect_patterns,  # type: ignore
            timeout=timeout if timeout else self.timeout,
        )

        # remove \r (leave \n)
        result = self.process.before.decode("utf-8").replace("\r", "")  # type: ignore
        # remove weird backspace characters
        result = re.sub(r".\x08", "", result)

        # remove echoed command
        if command not in result:
            raise TessentCommandError(f"Command not found in result '{result}'")

        return result.split(f"{command}\n", 1)[1].rstrip()

    def close(self, force: bool = True):
        """Close the tessent shell process."""
        try:
            self.send_command("exit -force")
        # ignore pexpect exception
        except pexpect.exceptions.EOF:
            pass

        self.process.close(force=force)

    def __enter__(self) -> "PyTessent":
        return self

    def __exit__(self, *args, **kwargs):
        self.close()
