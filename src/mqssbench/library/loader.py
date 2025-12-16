import pkgutil
import importlib
import logging

logger = logging.getLogger(__name__)

ALLOWED_ROOT_PACKAGES = {
    "mqssbench.library.providers",
    "mqssbench.library.adapters",
    "mqssbench.library.benchmarks",
}

MAX_DEPTH = 3  # to prevent excessively deep recursion

def _load_submodules(pkg, depth=0):
    if depth > MAX_DEPTH:
        logger.warning("Skipping deeper import under %s", pkg.__name__)
        return

    if pkg.__name__ not in ALLOWED_ROOT_PACKAGES \
       and not any(pkg.__name__.startswith(p) for p in ALLOWED_ROOT_PACKAGES):
        logger.debug("Skipping unrelated namespace %s", pkg.__name__)
        return

    for _, name, is_pkg in pkgutil.iter_modules(pkg.__path__):
        module_name = f"{pkg.__name__}.{name}"

        if name.startswith("_") or name.startswith("test"):
            continue

        try:
            importlib.import_module(module_name)
            logger.info("Loaded builtin module: %s", module_name)
        except Exception as exc:
            logger.error("Failed to import module %s: %s", module_name, exc)

        # Recurse into subpackages
        if is_pkg:
            sub_pkg = importlib.import_module(module_name)
            _load_submodules(sub_pkg, depth + 1)


def auto_import_builtin_library():
    from . import providers, adapters, benchmarks
    for pkg in (providers, adapters, benchmarks):
        _load_submodules(pkg)
    logger.info("Auto import of builtin library completed")


# TODO: later add loading external plugins and plugin manager