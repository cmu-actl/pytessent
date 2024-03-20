from pytessent import PyTessent


def test_pytessent():
    pt = PyTessent()
    response = pt.send_command("puts 'test'")
    assert response == "'test'"
