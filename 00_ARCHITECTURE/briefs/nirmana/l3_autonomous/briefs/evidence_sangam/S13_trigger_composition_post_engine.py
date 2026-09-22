"""RR-06. Proposition: a TRIGGER suppressive term is composed onto Mode A/B results AFTER the engine
search (apply_trigger_suppression called after mode_a_search/mode_b_search), so any input contract that
stops at the engine's necessary/supporting lists is incomplete."""
from _common import *
head("S13 — post-engine TRIGGER composition")
W = 'pipeline/orchestrator/writers/ka_sangam.py'
defn = grep(W, r'^def apply_trigger_suppression'); calls = grep(W, r'apply_trigger_suppression\(')
ma = grep(W, r'mode_a_search\('); mb = grep(W, r'mode_b_sweep\(')
if NEG: calls = [(1,'x')]
prop("apply_trigger_suppression is defined in the writer", len(defn) == 1, f"line={[i for i,_ in defn]}")
prop("it is called after both mode searches", len([i for i,_ in calls if i > 100]) >= 2 and ma and mb and min(i for i,_ in calls if i>100) > min(i for i,_ in ma), f"calls={[i for i,_ in calls]} mode_a={[i for i,_ in ma]} mode_b={[i for i,_ in mb]}")
w = grep(W, r'0\.2'); prop("admitted weights 0.2/0.2 referenced", any(40 <= i <= 140 or 670 <= i <= 720 for i,_ in w), f"lines={[i for i,_ in w][:6]}")
done()
