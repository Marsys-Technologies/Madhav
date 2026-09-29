import sys; sys.path.insert(0, "platform/scripts/governance")
import asset_census as ac
tot = flips = mention = decl = 0
for layer, cfg in ac.LAYERS.items():
    for f in sorted((ac.ROOT / cfg["caps"]).glob("*.ts")):
        if f.name.endswith(".test.ts"):
            continue
        tot += 1
        txt = f.read_text(encoding="utf-8", errors="replace")
        old = "density_contract" in txt
        new = bool(ac._DENSITY_DECL.search(ac._ts_code(txt, blank_strings=True)))
        mention += old; decl += new
        if old != new:
            flips += 1; print("FLIP", layer, f.name, old, "->", new)
print(f"capability modules scanned (6 layers, .test.ts excluded): {tot}")
print(f"modules mentioning density_contract anywhere (old substring rule): {mention}")
print(f"modules declaring a density_contract property in code (R232 rule): {decl}")
print(f"modules whose 'declares' answer changes: {flips}")
print("=> no module's declaring flag moves, so no asset's Dens.served declaring-count or verdict can move from R232 today")
