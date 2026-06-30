"""通用工具函数。"""

from .toml_io import toml_dump
from .cli import parse_args

__all__ = ["toml_dump", "parse_args"]
