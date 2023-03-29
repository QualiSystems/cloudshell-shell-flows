from __future__ import annotations

import pytest

from cloudshell.shell.flows.utils.str_helpers import normalize_path


@pytest.mark.parametrize(
    "path,expected",
    [
        ("' ftp://host '", "ftp://host"),
        ("'ftp://host' ", "ftp://host"),
        (" ftp://host ", "ftp://host"),
        (" 'ftp://host' ", "ftp://host"),
        (' "ftp://host" ', "ftp://host"),
        ('  "ftp://host" ', "ftp://host"),
    ],
)
def test_normalize_path(path: str, expected: str) -> None:
    assert normalize_path(path) == expected
