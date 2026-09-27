'use client'

import { AlertCircle, CheckCircle2, CircleDashed, Clock3, ShieldX, TerminalSquare } from 'lucide-react'
import { AiChoiceRadio } from './AiChoiceRadio'
import { choicesEqual, formatCheckedAt, supportsEveryRole, type AiChoice, type AiConsoleStateDto, type CliCardDto, type ConsoleMutation } from './types'

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
  mutationPending: boolean
  mutate: ConsoleMutation
  onSelectDefault: (choice: AiChoice) => Promise<unknown>
}

export function LocalClisSection({ state, clis, loading, error, mutationPending, mutate, onSelectDefault }: Props) {
  async function testCli(cli: CliCardDto) {
    try {
      await mutate(`/api/ai-console/clis/${cli.cliId}/validate`, { method: 'POST', body: JSON.stringify({}) }, `${cli.productName} validation completed.`)
    } catch { /* safe status is announced centrally */ }
  }
  const cliDefault = state?.defaultChoice?.kind === 'local_cli' ? state.defaultChoice : null

  const defaultMissing = cliDefault !== null
    && !clis.some(cli => cli.cliId === cliDefault.cliId
      && cli.state === 'reachable' && cli.models.some(model => model.modelId === cliDefault.modelId))

  return (
    <section className="aic-section" aria-labelledby="aic-cli-heading">
      <div className="aic-section-head"><div><h2 id="aic-cli-heading">Local CLIs</h2><p className="aic-section-copy">Use administrator-granted subscriptions available to this local server. Authentication material is never copied into Madhav.</p></div></div>
      {!error && defaultMissing && cliDefault && <div className="aic-broken"><strong>Broken default.</strong> {cliDefault.cliId} / {cliDefault.modelId ?? 'Built-in default'} is not currently reachable or authorized. Choose another default.<div className="aic-model-row" data-default="true"><span className="aic-model-id">Unavailable local CLI choice</span><AiChoiceRadio choice={cliDefault} checked disabled unavailable label={`${cliDefault.cliId} ${cliDefault.modelId ?? 'Built-in default'}`} onSelect={onSelectDefault} /></div></div>}
      {error ? <div className="aic-error" role="alert">Local CLI access could not be loaded. Refresh the page to try again.</div> : loading ? <div className="aic-empty">Checking local CLI access…</div> : clis.length === 0 ? <div className="aic-empty">No local CLI products are registered on this server.</div> : (
        <div className="aic-grid">{clis.map(cli => {
          const isPrivate = cli.state === 'not_granted'
          const models = isPrivate ? [] : cli.models
          return <article className="aic-card" key={cli.cliId}>
            <div className="aic-card-head">
              <div className="aic-card-title-row"><div><span className="aic-provider-name">Local subscription</span><h3><TerminalSquare aria-hidden="true" className="mr-2 inline size-4" />{cli.productName}</h3></div><CliStatus state={cli.state} /></div>
              {isPrivate ? <p className="aic-section-copy">An administrator must grant access before host availability can be shown.</p> : <>
                <p className="aic-meta">{cli.detectedProduct ?? 'Product not detected'}{cli.detectedVersion ? ` · ${cli.detectedVersion}` : ''}</p>
                <p className="aic-meta">Last check · {formatCheckedAt(cli.lastCheckedAt)}</p>
                <div className="aic-actions"><button className="aic-button" type="button" disabled={mutationPending} onClick={() => testCli(cli)}>Test local CLI</button></div>
              </>}
            </div>
            {!isPrivate && <div className="aic-model-list" aria-label={`${cli.productName} models`}>
              {models.length === 0 ? <div className="aic-model-row"><span className="aic-model-id">{cli.state === 'reachable' ? 'No compatible models available' : 'This CLI is not available for execution'}</span></div> : models.map(model => {
                const choice = { kind: 'local_cli' as const, cliId: cli.cliId, modelId: model.modelId }
                const checked = choicesEqual(state?.defaultChoice ?? null, choice)
                const usable = cli.state === 'reachable' && supportsEveryRole(model.compatibleRoles)
                return <div className="aic-model-row" data-default={checked} key={model.modelId ?? '__builtin__'}><div><span className="aic-model-name">{model.displayName}</span><span className="aic-model-id">{model.modelId ?? 'Built-in default'}{!usable ? ' · unavailable for all four roles' : ''}</span></div><AiChoiceRadio choice={choice} checked={checked} disabled={!usable || mutationPending} unavailable={checked && !usable} label={`${cli.productName} ${model.displayName}`} onSelect={onSelectDefault} /></div>
              })}
            </div>}
          </article>
        })}</div>
      )}
    </section>
  )
}
