
import sys
import log
import importlib

for code in sys.argv[1:]:
    if "." in code:
        modname, funcname = code.rsplit(".")
        mod = importlib.import_module(modname)
        getattr(mod, funcname)()
    else:
        log.error("loader run %s no dot", code)


