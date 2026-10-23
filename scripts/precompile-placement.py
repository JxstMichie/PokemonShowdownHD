import json
import re
import subprocess
from pathlib import Path

'''
This script is just to pre-compile a the list of all placement.jsons, this helps for reducing unecessary traffic to github
You would need to download the entirety of the 9 repos so I dont actually recommend using this
'''


HERE = Path(__file__).resolve().parent.parent
ANI = HERE.parent / "Asset Creator" / "Assets" / "Ani"
SOURCE = HERE / "source"
DATA = HERE / "data"
FILES = ("", "tap_", "physical_")
VIEWS = ("", "-back", "-shiny", "-back-shiny")

ALIASES = """
const { aliases = [] } = require(process.argv[1]);
const { names, folders } = JSON.parse(require("fs").readFileSync(0, "utf8"));
const have = new Set(folders), result = {};
for (const name of names) {
  if (have.has(name)) continue;
  for (const rule of aliases) {
    if (!rule.match.test(name)) continue;
    const folder = typeof rule.folder === "function" ? rule.folder(name.match(rule.match)) : name.replace(rule.match, rule.folder);
    if (have.has(folder)) { result[name] = folder; break; }
  }
}
console.log(JSON.stringify(result));
"""

folders = [(g.name, d, re.sub(r"^\d{4}_", "", d.name)) for g in sorted(ANI.glob("gen[1-9]")) for d in sorted(g.glob("[0-9][0-9][0-9][0-9]_*")) if d.is_dir()]
names = (HERE / "ani-list" / "Showdown-Ani.txt").read_text(encoding="utf-8").split()
known = [n for _, _, n in folders]
alias = json.loads(subprocess.run(["node", "-e", ALIASES, str(SOURCE / "exceptions.js")], input=json.dumps({"names": names, "folders": known}),
                                  capture_output=True, text=True, check=True).stdout)
alias = {k: v for k, v in sorted(alias.items()) if v in set(known)}

gens, placements = {}, {}
for gen, d, name in folders:
    have = {f.name for f in d.glob("*.png")}
    mask = sum(1 << (k * 4 + v) for k, kind in enumerate(FILES) for v, view in enumerate(VIEWS) if f"{kind}{name}{view}.png" in have)
    gens.setdefault(gen, []).append(f"{d.name}:{mask:03x}")
    if (d / "placement.json").exists():
        data = json.loads((d / "placement.json").read_text(encoding="utf-8"))
        boxes = {v: {k: round(data[v][k], 1) for k in "xywh"} for v in ("front", "back") if v in data}
        if boxes:
            placements[name] = boxes
sprites = "".join(f"{g}: {' '.join(items)}\n" for g, items in gens.items()) + "aliases: " + " ".join(f"{k}={v}" for k, v in alias.items()) + "\n"

(DATA / "sprites.txt").write_text(sprites, encoding="utf-8")
(DATA / "placements.json").write_text(json.dumps(placements, separators=(",", ":")), encoding="utf-8")
print(f"{len(folders)} species, {len(alias)} aliases")
