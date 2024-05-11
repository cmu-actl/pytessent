import asyncio

import pytest

from pytessent import PyTessent


def test_pytessent():
    pt = PyTessent()
    response = pt.send_command("puts 'test'")
    assert response == "'test'"


@pytest.mark.asyncio
async def test_async():
    pt0 = PyTessent()
    pt1 = PyTessent()

    first_processed = False

    task0 = pt0.send_command_async("exec sleep 3; puts 0")
    task1 = pt1.send_command_async("exec sleep 1; puts 1")

    for task in asyncio.as_completed([task0, task1]):
        result = await task
        if not first_processed:
            assert result == "1"
            first_processed = True
        else:
            assert result == "0"
            break
