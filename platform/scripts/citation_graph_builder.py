import os
import re
from pathlib import Path
import json

# platform/scripts/citation_graph_builder.py → parents[2] = repo root
ROOT = str(Path(__file__).resolve().parents[2])
MSR_V3 = f"{ROOT}/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md"
UCN_V4 = f"{ROOT}/025_HOLISTIC_SYNTHESIS/UCN_v4_0.md"
CDLM_V1 = f"{ROOT}/025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md"
RM_V2 = f"{ROOT}/025_HOLISTIC_SYNTHESIS/RM_v2_0.md"

def build_citation_graph():
    # 1. Define nodes (all potential IDs)
    nodes = set()
    defined_ids = set()
    edges = []
    
    # helper to find latest version of a file
    def find_latest(dir_path, prefix):
        files = [f for f in os.listdir(f"{ROOT}/{dir_path}") if f.startswith(prefix) and f.endswith(".md")]
        if not files: return None
        # Sort by version (naive)
        files.sort()
        return f"{ROOT}/{dir_path}/{files[-1]}"

    # Define targets
    targets = {
        "MSR": MSR_V3,
        "UCN": UCN_V4,
        "CDLM": CDLM_V1,
        "RM": RM_V2,
    }
    
    # Extract defined IDs from targets
    for key, path in targets.items():
        if not os.path.exists(path): continue
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if key == "MSR":
                matches = re.findall(r'^SIG\.MSR\.([0-9a-z.]+):', content, flags=re.MULTILINE)
                for m in matches: defined_ids.add(f"SIG.MSR.{m}")
            elif key == "CDLM":
                matches = re.findall(r'^CDLM\.D\d+\.D\d+:', content, flags=re.MULTILINE)
                for m in matches: defined_ids.add(m.strip(':'))
            elif key == "RM":
                matches = re.findall(r'^RM\.E\d+:', content, flags=re.MULTILINE)
                for m in matches: defined_ids.add(m.strip(':'))
            elif key == "UCN":
                # UCN sections?
                pass

    print(f"Defined IDs: {len(defined_ids)}")

    # 2. Discover all claim-bearing files
    discovery_dirs = [
        "025_HOLISTIC_SYNTHESIS",
        "03_DOMAIN_REPORTS",
    ]
    
    files_to_scan = []
    for d in discovery_dirs:
        path = f"{ROOT}/{d}"
        if not os.path.exists(path): continue
        for f in os.listdir(path):
            if f.endswith(".md") and "_v" in f:
                # Basic version filter (only latest)
                # Actually, let's scan all to see total references
                files_to_scan.append(f"{path}/{f}")

    # 3. Scan for references
    dangling = []
    for fpath in files_to_scan:
        fname = os.path.basename(fpath)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find references: SIG.MSR.XXX, CDLM.DX.DY, RM.EXXX
            refs = re.findall(r'(SIG\.MSR\.[0-9a-z.]+|CDLM\.D\d+\.D\d+|RM\.E\d+)', content)
            
            for ref in refs:
                if ref not in defined_ids:
                    # Check if it's a definition (skip if we are in the source file)
                    is_def = False
                    if "MSR" in ref and "MSR" in fname: is_def = True
                    if "CDLM" in ref and "CDLM" in fname: is_def = True
                    if "RM" in ref and "RM" in fname: is_def = True
                    
                    if not is_def:
                        dangling.append({"file": fname, "ref": ref})
                else:
                    edges.append({"source": fname, "target": ref})

    # 4. Generate GraphML (simplified)
    # Just a JSON for now as requested or GraphML if really needed
    graphml = """<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <graph id="G" edgedefault="directed">
"""
    # Nodes
    all_nodes = set([e['source'] for e in edges] + [e['target'] for e in edges])
    for n in all_nodes:
        graphml += f'    <node id="{n}"/>\n'
    # Edges
    for e in edges:
        graphml += f'    <edge source="{e["source"]}" target="{e["target"]}"/>\n'
    graphml += "  </graph>\n</graphml>"

    output_path = f"{ROOT}/verification_artifacts/CITATION_GRAPH.graphml"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(graphml)

    # Dangling report
    with open(f"{ROOT}/verification_artifacts/DANGLING_REFERENCES.json", 'w') as f:
        json.dump(dangling, f, indent=2)

    print(f"Graph built with {len(edges)} edges.")
    print(f"Dangling references found: {len(dangling)}")

if __name__ == "__main__":
    build_citation_graph()
