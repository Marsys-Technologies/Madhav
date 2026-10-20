# Executor table pin shards (SR-CHURN-CUT 3)

One NEW file per reviewed edit of `fleet/executor_ops.json`: `<ITEM>.json`, schema `ky.executor_pin_shard/1`
(format and rules: `fleet/executor_pin_shards.py`). `test_executor_table.py` compares the live table with its own
enumeration plus every shard here. A merged shard is never edited or removed (CI refuses it); the next change to the
same kind is a new shard that replaces the entry. Draft one with
`python3 fleet/executor_pin_shards.py scaffold --item <ITEM> --base <executor_ops.json at main>` and review every
entry against the item's brief: the draft is a proposal, not evidence.
