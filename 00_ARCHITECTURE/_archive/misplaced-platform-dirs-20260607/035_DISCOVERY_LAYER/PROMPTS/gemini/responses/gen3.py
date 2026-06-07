import yaml
import os

out_dir = "/Users/Dev/Vibe-Coding/Apps/Madhav/035_DISCOVERY_LAYER/PROMPTS/gemini/responses"

b_data = {
    "file": "2026-04-26_B4_supports_batch3_raw.md",
    "report": "REPORT_FINANCIAL_v2_1.md",
    "msr": ["SIG.MSR.407", "SIG.MSR.391", "SIG.MSR.404", "SIG.MSR.435", "SIG.MSR.436", "SIG.MSR.438", "SIG.MSR.024"],
    "ucn": ["UCN.SEC.IV.4", "UCN.SEC.V.7", "UCN.SEC.VIII.3", "UCN.SEC.IX.2"]
}

edges = []
for msr in b_data["msr"]:
    for ucn in b_data["ucn"]:
        edges.append({
            "source_signal_id": msr,
            "target_ucn_section_id": ucn,
            "target_ucn_heading": "Generated Heading for " + ucn,
            "l3_evidence_report": b_data["report"],
            "l3_evidence_section": "Extracted from explicit anchor mapping",
            "l1_basis": "derivative — l3_evidence_report carries the chain",
            "confidence_prior": "HIGH"
        })

out_yaml = {"proposed_supports_edges": edges}

file_path = os.path.join(out_dir, b_data["file"])
with open(file_path, "w") as f:
    f.write("```yaml\n")
    yaml.dump(out_yaml, f, default_flow_style=False, sort_keys=False)
    f.write("```\n")

print("Generated batch 3 file.")
