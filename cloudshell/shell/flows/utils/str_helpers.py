from __future__ import annotations

import re


def normalize_path(path: str) -> str:
    # "' ftp://host '"   == "ftp://host"  noqa: E800
    # "'ftp://host' "    == "ftp://host"  noqa: E800
    # " ftp://host "     == "ftp://host"  noqa: E800
    # " 'ftp://host' "   == "ftp://host"  noqa: E800
    # ' "ftp://host" '   == "ftp://host"  noqa: E800
    # '  "ftp://host" '  == "ftp://host"  noqa: E800
    res = re.sub(r"^['\"\s]+(.+?)['\"\s]+", r"\g<1>", path)
    return res
