from __future__ import annotations

import importlib
import pkgutil


class ModuleLoader:
    def load_all(self) -> list[str]:
        import app.modules as package
        loaded: list[str] = []
        for module in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            importlib.import_module(module.name)
            loaded.append(module.name)
        return loaded
