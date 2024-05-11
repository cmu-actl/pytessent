from __future__ import annotations

import re
import weakref
from pathlib import Path
from shutil import which
from typing import Awaitable, Literal, overload

import pexpect

_TESSENT_ENCODING = "utf-8"


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

        launch_command_parts = [self.tessent_exe, "-shell"]
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
        launch_command = " ".join(launch_command_parts)

        self._process = pexpect.spawn(launch_command)
        self._finalizer = weakref.finalize(self, self._close_process)
        self._expect()

    @property
    def process(self) -> pexpect.pty_spawn.spawn[bytes]:
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

    @overload
    def _expect(
        self, timeout: int | None = None, *, async_: Literal[False] = False
    ) -> int:
        ...

    @overload
    def _expect(
        self, timeout: int | None = None, *, async_: Literal[True]
    ) -> Awaitable[int]:
        ...

    def _expect(
        self, timeout: int | None = None, *, async_: bool = False
    ) -> int | Awaitable[int]:
        return self._process.expect(
            self._expect_patterns,  # type: ignore
            timeout=timeout if timeout is not None else self.timeout,
            async_=async_,  # type: ignore
        )

    def _clean_result(self, command: str, result: bytes | None) -> str:
        if result is None:
            raise TessentCommandError(f"No output returned from command '{command}'")
        result_str = result.decode(_TESSENT_ENCODING)
        # remove \r (leave \n)
        result_str = result_str.replace("\r", "")
        # remove weird backspace characters
        result_str = re.sub(r".\x08", "", result_str)
        # remove echoed command
        if command not in result_str:
            raise TessentCommandError(
                f"Command '{command}' not found in result '{result_str}'"
            )
        return result_str.split(f"{command}\n", 1)[1].rstrip()

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
        self._expect(timeout)
        return self._clean_result(command, self.process.before)

    async def send_command_async(self, command: str, timeout: int | None = None):
        self.process.sendline(command)
        await self._expect(timeout, async_=True)
        return self._clean_result(command, self.process.before)

    def _close_process(self) -> None:
        """Close the open tessent shell process.

        Should only be used by `weakref.finalize` in the intializer.
        """
        try:
            self.send_command("exit -force")
        # ignore pexpect exception
        except pexpect.exceptions.EOF:
            pass
        self.process.close(force=True)

    def close(self) -> None:
        """Close the tessent shell process."""
        self._finalizer()

    @property
    def closed(self):
        return not self._finalizer.alive

    def __enter__(self) -> "PyTessent":
        return self

    def __exit__(self, *args, **kwargs):
        self.close()
