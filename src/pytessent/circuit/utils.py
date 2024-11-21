import re


class CircuitElementNotFoundException(Exception):
    pass


def verilog_name(name: str) -> str:
    name = name.replace("/", "__")
    if any([c in name for c in "[](){}$"]):
        name = f"\\{name}"
    return name


def parse_name(name_str: str) -> str:
    return name_str.replace(" ", "").replace("\\", "").replace("{", "").replace("}", "")


def parse_name_list(name_list: str) -> list[str]:
    return [
        p.replace(" ", "").replace("\\", "").replace("{", "").replace("}", "")
        for p in re.findall(r"{[^}]+}|[^{\s]+", name_list)
    ]
