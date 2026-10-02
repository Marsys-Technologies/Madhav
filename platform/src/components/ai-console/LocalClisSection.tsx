'use client'

import { useState } from 'react'
import { AlertCircle, CheckCircle2, CircleDashed, Clock3, ShieldX, TerminalSquare } from 'lucide-react'
import { AiChoiceRadio } from './AiChoiceRadio'
import { AI_ROLES, ROLE_LABELS, choicesEqual, formatCheckedAt, type AiChoice, type AiConsoleStateDto, type CliCardDto, type ConsoleMutation } from './types'

const STATE_LABELS: Record<CliCardDto['state'], string> = {
  not_granted: 'Not granted', untested: 'Not tested', validating: 'Testing', reachable: 'Reachable',
  not_installed: 'Not installed', auth_unavailable: 'Authentication unavailable', unreachable: 'Unreachable', needs_attention: 'Needs attention',
}

function CliStatus({ state }: { state: CliCardDto['state'] }) {
  const Icon = state === 'reachable' ? CheckCircle2 : state === 'validating' ? CircleDashed : state === 'untested' ? Clock3
    : state === 'not_granted' ? ShieldX : AlertCircle
  return <span className="aic-status"><Icon aria-hidden="true" />{STATE_LABELS[state]}</span>
}

interface Props {
  state?: AiConsoleStateDto
  clis: CliCardDto[]
  loading: boolean
  error: boolean
  aggregateStatus: 'loading' | 'error' | 'ready'
  mutationPending: boolean
  mutate: ConsoleMutation
  onSelectDefault: (choice: AiChoice) => Promise<unknown>
  onConfigureRoles?: (cliId: CliCardDto['cliId']) => void
}

export function LocalClisSection({ state, clis, loading, error, aggregateStatus, mutationPending, mutate, onSelectDefault, onConfigureRoles }: Props) {
  const [candidateIds, setCandidateIds] = useState<Record<string, string>>({})
  async function testCli(cli: CliCardDto) {
    try {
      await mutate(`/api/ai-console/clis/${cli.cliId}/validate`, { method: 'POST', body: JSON.stringify({}) }, `${cli.productName} validation completed.`)
    } catch { /* safe status is announced centrally */ }
  }
  async function addCandidate(cli: CliCardDto) {
    const modelId = candidateIds[cli.cliId]?.trim()
    if (!modelId) return
    try {
      await mutate(`/api/ai-console/clis/${cli.cliId}/models`, {
        method: 'POST', body: JSON.stringify({ modelId }),
      }, `${cli.productName} model tested and added.`)
      setCandidateIds(current => ({ ...current, [cli.cliId]: '' }))
    } catch { /* safe status is announced centrally */ }
  }
  const cliDefault = state?.defaultChoice?.kind === 'local_cli' ? state.defaultChoice : null

  const defaultMissing = aggregateStatus === 'ready' && !loading && !error && cliDefault !== null
    && !clis.some(cli => cli.cliId === cliDefault.cliId
      && cli.state === 'reachable' && cli.models.some(model => model.modelId === cliDefault.modelId))

  return (
    <section className="aic-section" aria-labelledby="aic-cli-heading">
      <div className="aic-section-head"><div><h2 id="aic-cli-heading">Local CLIs</h2><p className="aic-section-copy">Use administrator-granted subscriptions available to this local server. Authentication material is never copied into Madhav.</p></div></div>
      {!error && aggregateStatus === 'ready' && !loading && cliDefault && <div className="aic-broken"><strong>{defaultMissing ? 'Broken default.' : 'Earlier direct-model default.'}</strong> {defaultMissing ? `${cliDefault.cliId} / ${cliDefault.modelId ?? 'Built-in default'} is not currently reachable or authorized. Choose another default.` : 'This saved choice remains active until you replace it with a four-role setup.'}<div className="aic-model-row" data-default="true"><span className="aic-model-id">{cliDefault.modelId ?? 'Built-in default'}</span><AiChoiceRadio choice={cliDefault} checked disabled unavailable={defaultMissing} label={`${cliDefault.cliId} ${cliDefault.modelId ?? 'Built-in default'}`} onSelect={onSelectDefault} /></div></div>}
      {error ? <div className="aic-error" role="alert">Local CLI access could not be loaded. Refresh the page to try again.</div> : loading ? <div className="aic-empty">Checking local CLI access…</div> : clis.length === 0 ? <div className="aic-empty">No local CLI products are registered on this server.</div> : (
        <div className="aic-grid">{clis.map(cli => {
          const isPrivate = cli.state === 'not_granted'
          const models = isPrivate ? [] : cli.models
          const preset = state?.configurations.find(item => !item.deletedAt && item.configurationKind === 'cli_preset'
            && item.ownerCliId === cli.cliId)
          const presetChoice = preset ? { kind: 'custom_configuration' as const, configurationId: preset.id } : null
          const presetChecked = presetChoice ? choicesEqual(state?.defaultChoice ?? null, presetChoice) : false
          const presetReady = Boolean(preset && cli.state === 'reachable' && AI_ROLES.every(role => {
            const target = preset.roles[role]
            return target.kind === 'local_cli' && target.cliId === cli.cliId
              && cli.models.some(model => model.modelId === target.modelId && model.compatibleRoles.includes(role))
          }))
          return <article className="aic-card" key={cli.cliId}>
            <div className="aic-card-head">
              <div className="aic-card-title-row"><div><span className="aic-provider-name">Local subscription</span><h3><TerminalSquare aria-hidden="true" className="mr-2 inline size-4" />{cli.productName}</h3></div><CliStatus state={cli.state} /></div>
              {isPrivate ? <p className="aic-section-copy">An administrator must grant access before host availability can be shown.</p> : <>
                <p className="aic-meta">{cli.detectedProduct ?? 'Product not detected'}{cli.detectedVersion ? ` · ${cli.detectedVersion}` : ''}</p>
                <p className="aic-meta">Last check · {formatCheckedAt(cli.lastCheckedAt)}</p>
                <div className="aic-actions"><button className="aic-button" type="button" disabled={mutationPending} onClick={() => testCli(cli)}>Test local CLI</button>{cli.state === 'reachable' && cli.cliId !== 'kimi_code' && <button className="aic-button" data-primary="true" type="button" onClick={() => onConfigureRoles?.(cli.cliId)}>{preset ? 'Edit four roles' : 'Set up four roles'}</button>}</div>
                {cli.cliId === 'kimi_code' && <p className="aic-meta">Kimi Code currently supports synthesis only. It can be the synthesizer in a mixed custom CLI configuration, but cannot fill all four roles by itself.</p>}
                {cli.state === 'reachable' && (cli.cliId === 'codex' || cli.cliId === 'claude_code') && <div className="aic-cli-manual">
                  <p className="aic-section-copy">This CLI does not publish a model catalog here. Enter an exact model ID to test it through the local subscription, then assign it to roles in a configuration.</p>
                  <div className="aic-field"><label htmlFor={`aic-cli-model-${cli.cliId}`}>Exact model ID for {cli.productName}</label><input id={`aic-cli-model-${cli.cliId}`} value={candidateIds[cli.cliId] ?? ''} onChange={event => setCandidateIds(current => ({ ...current, [cli.cliId]: event.target.value }))} placeholder="Model ID from this CLI" autoComplete="off" /></div>
                  <button className="aic-button" type="button" disabled={mutationPending || !candidateIds[cli.cliId]?.trim()} onClick={() => addCandidate(cli)}>Test and add CLI model</button>
                </div>}
              </>}
            </div>
            {preset && !isPrivate && <div className="aic-role-grid aic-card-roles">{AI_ROLES.map(role => <div className="aic-role-row" key={role}><span className="aic-role-label">{ROLE_LABELS[role]}</span><span className="aic-model-id">{preset.roles[role].modelId ?? 'Built-in default'} · Effort: {preset.roles[role].effort ?? 'model default'}</span></div>)}</div>}
            {!isPrivate && cli.cliId !== 'kimi_code' && <div className="aic-model-row" data-default={presetChecked}><div><span className="aic-model-name">{preset ? 'CLI role setup' : 'Role setup needed'}</span><span className="aic-model-id">{presetReady ? 'All four roles use this local subscription' : 'Set up four compatible roles before selecting as default'}</span></div>{presetChoice && <AiChoiceRadio choice={presetChoice} checked={presetChecked} disabled={!presetReady || aggregateStatus !== 'ready' || mutationPending} unavailable={presetChecked && !presetReady} label={cli.productName} onSelect={onSelectDefault} />}</div>}
            {!isPrivate && <div className="aic-model-list" aria-label={`${cli.productName} models`}>
              {models.length === 0 ? <div className="aic-model-row"><span className="aic-model-id">{cli.state === 'reachable' ? 'No compatible models available' : 'This CLI is not available for execution'}</span></div> : models.map(model => {
                return <div className="aic-model-row" key={model.modelId ?? '__builtin__'}><div><span className="aic-model-name">{model.displayName}</span><span className="aic-model-id">{model.modelId ?? 'Built-in default'} · {model.isBuiltinDefault ? 'Validated with this CLI' : cli.cliId === 'codex' || cli.cliId === 'claude_code' ? 'Individually tested with this CLI' : 'Discovered by CLI · not individually tested'}</span></div></div>
              })}
            </div>}
          </article>
        })}</div>
      )}
    </section>
  )
}
