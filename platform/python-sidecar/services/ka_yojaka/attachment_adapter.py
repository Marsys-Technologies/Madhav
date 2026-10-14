"""Typed source consultation without guessing L2-to-mechanism bindings."""
from collections import defaultdict
from dataclasses import asdict, replace

from services.kala_core.promise import AttachmentInput, AttachmentSource, FactState, load_l2_attachments


def attach_sources(output, available, signals, cgm, pratijna):
    inputs = defaultdict(list)
    for source, records, id_key in ((AttachmentSource.MSR, signals, 'signal_id'),
                                    (AttachmentSource.CGM, cgm, 'edge_id'),
                                    (AttachmentSource.PRATIJNA, pratijna, 'pratijna_id')):
        for record in records:
            raw = record.get('constituent_facts_array') if source == AttachmentSource.MSR else None
            refs = tuple(sorted({str(fid) for fid in raw})) if isinstance(raw, (list, tuple)) else ()
            inputs[str(record['ayanamsha_id'])].append(AttachmentInput(str(record[id_key]), source, refs))

    loaded, summaries, reasons, msr_by_id, msr_by_fact = {}, {}, {}, {}, {}
    for ayan in set(available) | set(inputs) | {r['ayanamsha_id'] for r in output}:
        # Load each actual source exactly once per convention. Bound attachments
        # below acquire their real mechanism id only after root resolution.
        loaded[ayan] = load_l2_attachments(f'{ayan}:source_consultation', inputs[ayan], available.get(ayan, {}))
        summaries[ayan], reasons[ayan] = {}, {}
        msr_by_id[ayan], msr_by_fact[ayan] = {}, defaultdict(set)
        for a in loaded[ayan]:
            if a.source == AttachmentSource.MSR:
                msr_by_id[ayan][a.attachment_id] = a
                for fid in a.fact_ids:
                    msr_by_fact[ayan][fid].add(a.attachment_id)
        for name, source in (('msr', AttachmentSource.MSR), ('cgm', AttachmentSource.CGM),
                             ('pratijna', AttachmentSource.PRATIJNA)):
            attachments = [a for a in loaded[ayan] if a.source == source]
            missing = [a for a in attachments if a.state == FactState.MISSING_FACT]
            summaries[ayan][name] = ('missing_fact' if not attachments or missing else
                'evaluated_empty' if all(a.state == FactState.EVALUATED_EMPTY for a in attachments) else 'present')
            reasons[ayan][name] = (missing[0].null_reason if missing else
                'no_source_rows_without_evaluated_empty_marker' if not attachments else None)

    # (I) INTERPRETATION: without fact roots there is no earned binding to an
    # L1 mechanism. Keep these records in source-level testimony audit rows;
    # carry consultation states on mechanisms without inventing a causal link.
    for ayan in sorted(loaded):
        for source, table in ((AttachmentSource.CGM, 'bodha_cgm_edges'),
                              (AttachmentSource.PRATIJNA, 'bodha_pratijna')):
            attachments = [a for a in loaded[ayan] if a.source == source]
            if not attachments:
                continue
            mid = f'{ayan}:source_consultation:{source.value}'
            output.append(dict(mechanism_id=mid, conclusion_id=f'{mid}:conclusion',
                canonical_id=None, ayanamsha_id=ayan, event_class_id=None,
                route='testimony', operator_role='testimony', weight=0,
                formation_state='proposed', fact_state='missing_fact', fact_ids=[],
                rule_version='unadmitted', source=table, binding=None,
                qualification='no_fact_root_identity_in_l2_source', effective_state='unresolved',
                scored=False, defeats=[], excepts=[], cancellation_unqualified=[],
                target=None, constituent_planets=[], attachments=[],
                l2_attachments=[asdict(replace(a, mechanism_id=mid)) for a in attachments]))

    for row in output:
        ayan = row['ayanamsha_id']
        local = available.get(ayan, {})
        if 'l2_attachments' not in row:
            matches = set(row['attachments'])
            if row['fact_ids']:
                candidates = [msr_by_fact[ayan][fid] for fid in row['fact_ids']]
                matches |= set.intersection(*candidates)
            row['l2_attachments'] = [asdict(replace(msr_by_id[ayan][sid], mechanism_id=row['mechanism_id']))
                                      for sid in sorted(matches) if sid in msr_by_id[ayan]]
        row['sources_consulted'] = ['msr', 'cgm', 'pratijna']
        row['source_states'] = dict(summaries[ayan])
        row['source_null_reasons'] = dict(reasons[ayan])
        row['constituent_fact_tiers'] = {fid: local[fid].get('verification_pass_status')
                                         for fid in row['fact_ids'] if fid in local}
