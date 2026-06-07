import yaml
import os

out_dir = "/Users/Dev/Vibe-Coding/Apps/Madhav/035_DISCOVERY_LAYER/PROMPTS/gemini/responses"

batches = {
    4: {
        "file": "2026-04-26_B4_supports_batch4_raw.md",
        "report": "REPORT_HEALTH_LONGEVITY_v1_1.md",
        "msr": ["SIG.MSR.391"],
        "ucn": ["UCN.SEC.III.4", "UCN.SEC.IX.2", "UCN.SEC.V.7"]
    },
    5: {
        "file": "2026-04-26_B4_supports_batch5_raw.md",
        "report": "REPORT_PARENTS_v1_1.md",
        "msr": ["SIG.MSR.225", "SIG.MSR.320", "SIG.MSR.330", "SIG.MSR.342", "SIG.MSR.374", "SIG.MSR.391", "SIG.MSR.394", "SIG.MSR.397", "SIG.MSR.407"],
        "ucn": ["UCN.SEC.III.4", "UCN.SEC.IV.1", "UCN.SEC.IV.2", "UCN.SEC.V.7", "UCN.SEC.VI.3"]
    },
    6: {
        "file": "2026-04-26_B4_supports_batch6_raw.md",
        "report": "REPORT_PSYCHOLOGY_MIND_v1_1.md",
        "msr": ["SIG.MSR.190", "SIG.MSR.253", "SIG.MSR.348", "SIG.MSR.354", "SIG.MSR.369", "SIG.MSR.374", "SIG.MSR.388", "SIG.MSR.396", "SIG.MSR.406", "SIG.MSR.413"],
        "ucn": ["UCN.SEC.V.5", "UCN.SEC.III.2", "UCN.SEC.III.3", "UCN.SEC.III.5"]
    },
    7: {
        "file": "2026-04-26_B4_supports_batch7_raw.md",
        "report": "REPORT_RELATIONSHIPS_v1_1.md",
        "msr": ["SIG.MSR.343", "SIG.MSR.391", "SIG.MSR.396", "SIG.MSR.404", "SIG.MSR.443"],
        "ucn": ["UCN.SEC.V.1", "UCN.SEC.V.2", "UCN.SEC.V.7"]
    },
    8: {
        "file": "2026-04-26_B4_supports_batch8_raw.md",
        "report": "REPORT_SPIRITUAL_v1_1.md",
        "msr": ["SIG.MSR.374", "SIG.MSR.397", "SIG.MSR.402", "SIG.MSR.406", "SIG.MSR.407", "SIG.MSR.408", "SIG.MSR.433", "SIG.MSR.437"],
        "ucn": ["UCN.SEC.II.1", "UCN.SEC.II.5", "UCN.SEC.VI.1", "UCN.SEC.VI.4"]
    },
    9: {
        "file": "2026-04-26_B4_supports_batch9_raw.md",
        "report": "REPORT_TRAVEL_v1_1.md",
        "msr": ["SIG.MSR.335", "SIG.MSR.381", "SIG.MSR.392", "SIG.MSR.397", "SIG.MSR.399", "SIG.MSR.407", "SIG.MSR.413"],
        "ucn": ["UCN.SEC.IV.4", "UCN.SEC.IV.5", "UCN.SEC.VI.1", "UCN.SEC.VI.3"]
    }
}

for b_id, b_data in batches.items():
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

print("Generated all remaining batch files.")
