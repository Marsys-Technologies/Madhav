import sys
import os
import re
from pathlib import Path
import json

# Add platform/scripts to path to import corpus_common
sys.path.append(str(Path(__file__).parent))
import corpus_common

MSR_V3 = "/Users/Dev/Vibe-Coding/Apps/Madhav/025_HOLISTIC_SYNTHESIS/MSR_v3_0.md"
FORENSIC_V8 = "/Users/Dev/Vibe-Coding/Apps/Madhav/99_ARCHIVE/01_FACTS_LAYER/FORENSIC_DATA_v8_0_SUPPLEMENT.md"

def run_l1_verification():
    results = {}
    
    print("Loading MSR signals from MSR_v3_0.md...")
    signals = corpus_common.extract_msr_signals(MSR_V3)
    print(f"Loaded {len(signals)} signals.")
    
    # Authoritative data with Chalit alternatives
    auth_data = {
        "Jupiter":       {"houses": ["9"], "signs": ["Sagittarius"]},
        "Sun":           {"houses": ["10", "11"], "signs": ["Capricorn"]}, # 11 is Chalit
        "Moon":          {"houses": ["11", "12"], "signs": ["Aquarius"]}, # 12 is Chalit
        "Mars":          {"houses": ["7"], "signs": ["Libra"]},
        "Mercury":       {"houses": ["10"], "signs": ["Capricorn"]},
        "Venus":         {"houses": ["9"], "signs": ["Sagittarius"]},
        "Saturn":        {"houses": ["7"], "signs": ["Libra"]},
        "Rahu":          {"houses": ["2"], "signs": ["Taurus"]},
        "Ketu":          {"houses": ["8"], "signs": ["Scorpio"]},
        "Lagna":         {"houses": ["1"], "signs": ["Aries"]},
        "Shree Lagna":   {"houses": ["7"], "signs": ["Libra"]},
        "Ghati Lagna":   {"houses": ["9"], "signs": ["Sagittarius"]},
        "Varnada Lagna": {"houses": ["4"], "signs": ["Cancer"]},
        "Hora Lagna":    {"houses": ["3"], "signs": ["Gemini"]},
    }
    
    with open(FORENSIC_V8, 'r') as f:
        forensic_content = f.read()

    # --- F1: Positional Invariants ---
    
    def check_f1_01():
        """INV.L1.F1.01: Sign-House under Aries Lagna consistency."""
        failed = []
        for sig_id, raw_content in signals.items():
            yaml_data = corpus_common.parse_yaml_block(raw_content)
            
            # Skip divisional patterns
            if "divisional-pattern" in raw_content: continue
            
            for field in ['signal_name', 'supporting_rules']:
                if field not in yaml_data: continue
                val = yaml_data[field]
                lines = val if isinstance(val, list) else [val]
                
                for line in lines:
                    low_line = line.lower()
                    # Skip common false positive patterns
                    if any(w in low_line for w in ["transit", "transiting", "aspect", "rules", "lord", "d9", "d10", "d12", "d24", "d30", "d40", "d60"]):
                        continue
                    # Skip "If ..." conditional lines
                    if low_line.startswith("if "): continue
                    if re.search(r"\b\d+L\b", line): continue
                    
                    for planet, data in auth_data.items():
                        # Tight match for "Planet in XH" or "Planet in Sign"
                        p_match = re.search(rf"\b{planet}\b", line, re.IGNORECASE)
                        if not p_match: continue
                        
                        # House check
                        house_match = re.search(rf"\bin\s+(\d+)\s*H\b", line, re.IGNORECASE)
                        if house_match:
                            h_found = house_match.group(1)
                            if h_found not in data['houses']:
                                failed.append(f"{sig_id}: {planet} claimed in {h_found}H (expected {data['houses']}) in: '{line.strip()}'")
                                
                        # Sign check
                        sign_match = re.search(rf"\bin\s+({'|'.join(corpus_common.SIGNS)})\b", line, re.IGNORECASE)
                        if sign_match:
                            s_found = corpus_common.normalize_sign(sign_match.group(1))
                            if s_found not in data['signs']:
                                failed.append(f"{sig_id}: {planet} claimed in {s_found} (expected {data['signs']}) in: '{line.strip()}'")
        return failed

    results["INV.L1.F1.01"] = check_f1_01()

    # --- F3: Numeric Aggregate Invariants ---

    def check_f3_01():
        """INV.L1.F3.01: SAV Grand Total Exactly 337."""
        match = re.search(r"AVG\.SAV\.TOTAL.*?\|\s*(\d+)\s*\|", forensic_content)
        if match:
            total = int(match.group(1))
            if total != 337:
                return [f"SAV Total is {total}, expected 337"]
        else:
            return ["Could not find SAV Total in Forensic file"]
        return []

    results["INV.L1.F3.01"] = check_f3_01()

    def check_f3_02():
        """INV.L1.F3.02: BAV Row Sums per planet."""
        expected = {"SUN":48,"MOON":49,"MARS":39,"MERCURY":54,"JUPITER":56,"VENUS":52,"SATURN":39}
        failed = []
        for planet, exp_val in expected.items():
            match = re.search(rf"AVG\.BAV\.{planet}.*?\|\s*(\d+)\s*\|$", forensic_content, re.MULTILINE)
            if match:
                val = int(match.group(1))
                if val != exp_val:
                    failed.append(f"BAV {planet} sum is {val}, expected {exp_val}")
            else:
                failed.append(f"Could not find BAV {planet} row")
        return failed

    results["INV.L1.F3.02"] = check_f3_02()

    # --- F4: Derivation Rule Invariants ---

    def check_f4_06():
        """INV.L1.F4.06: Chara Karaka 8-Order (Atmakaraka = Moon)."""
        failed = []
        # Check Forensic v8.0 IDs: KRK.C.ATMA or KRK.C8.ATMA
        if not re.search(r"KRK\.C\.ATMA.*?\|\s*Moon\s*\|", forensic_content) and \
           not re.search(r"KRK\.C8\.ATMA.*?\|\s*Moon\s*\|", forensic_content):
            failed.append("Forensic v8.0 does not explicitly list Moon as AK in §10.1 or §10.3")
            
        for sid, c in signals.items():
            # Strict AK check (not AmK)
            # Exclude "AK indicator" or "AK-indicator" or "indicator of AK"
            if re.search(r"\bAK\b|\bAtmakaraka\b", c):
                if re.search(r"\bAK[- ]?indicator\b|indicator of AK", c, re.IGNORECASE):
                    continue
                
                # Ensure it's not AmK or Amatyakaraka
                if re.search(r"\bAmK\b|\bAmatyakaraka\b", c) and not re.search(r"\bAK\b|\bAtmakaraka\b", c.replace("AmK", "").replace("Amatyakaraka", "")):
                    continue
                
                # Simple check: does the signal mention Moon or PLN.MOON if it mentions AK?
                # This is a proxy.
                if "Moon" not in c and "PLN.MOON" not in c:
                    # Ignore if it mentions another planet as AmK/BK/etc. and AK is just in a list
                    # But if it specifically discusses AK, it should be Moon.
                    if "AmK" in c or "BK" in c or "MK" in c:
                         continue # likely a list of karakas
                    failed.append(f"{sid} mentions AK but not Moon")
                    
        return failed

    results["INV.L1.F4.06"] = check_f4_06()

    # --- F5: Structural Invariants ---

    def check_f5_01():
        """INV.L1.F5.01: MET.DASHA.CURRENT Window Check."""
        failed = []
        match = re.search(r"MET\.DASHA\.CURRENT.*?\|\s*Mercury MD – Saturn AD\s*\|", forensic_content)
        if not match: failed.append("Current dasha mismatch in MET.DASHA.CURRENT")
        
        if "2024-12-12" not in forensic_content: failed.append("Current AD start date mismatch (expected 2024-12-12)")
        if "2027-08-21" not in forensic_content: failed.append("Current AD end date mismatch (expected 2027-08-21)")
        
        return failed

    results["INV.L1.F5.01"] = check_f5_01()

    # --- Final Report ---

    report_path = "/Users/Dev/Vibe-Coding/Apps/Madhav/verification_artifacts/L1_REPORT.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)

    print("\nL1 Verification Results Summary:")
    all_passed = True
    hard_block_failed = False
    for inv, errors in results.items():
        if errors:
            print(f"❌ {inv}: {len(errors)} errors")
            all_passed = False
            # F3 and F5 are hard blocks
            if "F3" in inv or "F5" in inv:
                hard_block_failed = True
        else:
            print(f"✅ {inv}: PASSED")
            
    if hard_block_failed:
        print("\nVERDICT: NO-GO (Hard Block Invariants Failed)")
    elif not all_passed:
        print("\nVERDICT: WARNING (Soft Block Invariants Failed)")
    else:
        print("\nVERDICT: GO")

if __name__ == "__main__":
    run_l1_verification()
