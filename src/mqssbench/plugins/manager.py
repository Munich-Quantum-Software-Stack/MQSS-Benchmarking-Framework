from __future__ import annotations

import importlib
import logging
import pkgutil
from importlib.metadata import entry_points

logger = logging.getLogger(__name__)

_plugins_loaded = False

BUILTIN_PACKAGES = (
    "mqssbench.library.providers",
    "mqssbench.library.adapters",
    "mqssbench.library.benchmarks",
    "mqssbench.library.pipelines",
)

ENTRY_POINT_GROUP = "mqssbench"

MAX_DEPTH = 3


def _discover_modules(package, depth: int = 0) -> None:
    """Recursively import all builtin plugin modules."""

    if depth > MAX_DEPTH:
        logger.warning("Maximum plugin discovery depth reached for %s", package.__name__)
        return

    for _, module_name, is_package in pkgutil.iter_modules(package.__path__):

        if module_name.startswith("_") or module_name.startswith("test"):
            continue

        full_name = f"{package.__name__}.{module_name}"

        try:
            module = importlib.import_module(full_name)

            register = getattr(module, "register", None)

            if callable(register):
                register()
                
        except Exception:
            logger.exception("Failed loading builtin module %s", full_name)
            continue

        logger.debug("Loaded builtin plugin module %s", full_name)

        if is_package:
            _discover_modules(module, depth + 1)


def load_builtin_plugins() -> None:
    """Load all builtin plugins."""

    for package_name in BUILTIN_PACKAGES:

        package = importlib.import_module(package_name)

        _discover_modules(package)

    logger.info("Builtin plugins loaded.")


def load_entry_point_plugins() -> None:
    """Load third-party plugins installed via Python entry points."""

    try:
        eps = entry_points(group=ENTRY_POINT_GROUP)
    except TypeError:
        eps = entry_points().get(ENTRY_POINT_GROUP, [])

    for ep in eps:
        try:
            register = ep.load()

            if callable(register):
                register()

            logger.info("Loaded plugin '%s'.", ep.name)

        except Exception:
            logger.exception("Failed loading plugin '%s'.", ep.name)


def load_plugins() -> None:
    """Load builtin plugins and installed third-party plugins."""
    global _plugins_loaded

    if _plugins_loaded:
        return

    load_builtin_plugins()
    load_entry_point_plugins()

    _plugins_loaded = True