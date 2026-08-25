"""LUMEN — a contract-driven, budget-aware AI film crew."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("lumen-film-agent")
except PackageNotFoundError:  # pragma: no cover - editable source checkout
    __version__ = "0.1.0"

__all__ = ["__version__"]
