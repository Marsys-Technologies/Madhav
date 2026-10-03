import sys, importlib
from gen_brief import render
mod, name = sys.argv[1], sys.argv[2]
c = getattr(importlib.import_module(mod), name)
out = render(c)
print(out[:200])
print(len(out))
