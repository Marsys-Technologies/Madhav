'use client'

import { useMemo, useState } from 'react'
import { AlertCircle, CheckCircle2, CircleDashed, Clock3, Plus, ShieldAlert } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { AiChoiceRadio } from './AiChoiceRadio'
import {
  PROVIDER_LABELS, choicesEqual, formatCheckedAt, supportsEveryRole,
  type AiChoice, type AiConsoleStateDto, type ConsoleMutation, type ProviderConnectionDto, type ProviderId,
} from './types'

const PROVIDERS = Object.entries(PROVIDER_LABELS) as [ProviderId, string][]
const STATUS_LABELS: Record<ProviderConnectionDto['validationState'], string> = {
  untested: 'Not tested', validating: 'Testing', validated: 'Validated', needs_attention: 'Needs attention',
  invalid: 'Credential rejected', unreachable: 'Provider unreachable',
}

function StatusMark({ state }: { state: ProviderConnectionDto['validationState'] }) {
  const Icon = state === 'validated' ? CheckCircle2 : state === 'validating' ? CircleDashed
    : state === 'untested' ? Clock3 : state === 'invalid' ? ShieldAlert : AlertCircle
  return <span className="aic-status"><Icon aria-hidden="true" />{STATUS_LABELS[state]}</span>
}

type Editor =
  | { kind: 'add' }
  | { kind: 'rename'; connection: ProviderConnectionDto }
  | { kind: 'replace'; connection: ProviderConnectionDto }
  | { kind: 'test'; connection: ProviderConnectionDto }
  | null

interface Props {
  state?: AiConsoleStateDto
  loading: boolean
  mutationPending: boolean
  mutate: ConsoleMutation
  onSelectDefault: (choice: AiChoice) => Promise<unknown>
}

export function ProviderConnectionsSection({ state, loading, mutationPending, mutate, onSelectDefault }: Props) {
  const [editor, setEditor] = useState<Editor>(null)
  const [name, setName] = useState('')
  const [providerId, setProviderId] = useState<ProviderId>('openai')
  const [apiKey, setApiKey] = useState('')
  const [acknowledgeCharge, setAcknowledgeCharge] = useState(false)
  const [fieldError, setFieldError] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<ProviderConnectionDto | null>(null)
  const [deleteSummary, setDeleteSummary] = useState('')
  const providerDefault = state?.defaultChoice?.kind === 'provider_model' ? state.defaultChoice : null

  const connections = useMemo(() => (state?.connections ?? []).filter(connection =>
    !connection.deletedAt || providerDefault?.connectionId === connection.id), [state, providerDefault])

  function openEditor(next: Exclude<Editor, null>) {
    setEditor(next)
    setName(next.kind === 'rename' ? next.connection.name : '')
    setProviderId(next.kind === 'add' ? 'openai' : next.connection.providerId)
    setApiKey('')
    setAcknowledgeCharge(false)
    setFieldError('')
  }

  async function submitEditor() {
    if (!editor) return
    if ((editor.kind === 'add' || editor.kind === 'rename') && !name.trim()) {
      setFieldError('Enter a connection name.')
      return
    }
    if ((editor.kind === 'add' || editor.kind === 'replace') && !apiKey.trim()) {
      setFieldError('Enter the API key.')
      return
    }
    if (editor.kind !== 'rename' && !acknowledgeCharge) {
      setFieldError('Acknowledge the provider charge disclosure to continue.')
      return
    }
    setFieldError('')
    try {
      if (editor.kind === 'add') {
        await mutate('/api/ai-console/connections', {
          method: 'POST', body: JSON.stringify({ name: name.trim(), providerId, apiKey, acknowledgeCharge: true }),
        }, 'Connection saved and tested.')
      } else if (editor.kind === 'rename') {
        await mutate(`/api/ai-console/connections/${editor.connection.id}`, {
          method: 'PATCH', body: JSON.stringify({ name: name.trim() }),
        }, 'Connection renamed.')
      } else if (editor.kind === 'replace') {
        await mutate(`/api/ai-console/connections/${editor.connection.id}`, {
          method: 'PATCH', body: JSON.stringify({ apiKey, acknowledgeCharge: true }),
        }, 'Credential replaced and tested.')
      } else {
        await mutate(`/api/ai-console/connections/${editor.connection.id}/validate`, {
          method: 'POST', body: JSON.stringify({ acknowledgeCharge: true }),
        }, 'Connection test completed.')
      }
      setApiKey('')
      setEditor(null)
    } catch (error) {
      setFieldError(error instanceof Error ? error.message : 'The request could not be completed safely.')
    }
  }

  async function previewDelete(connection: ProviderConnectionDto) {
    try {
      const result = await mutate(`/api/ai-console/connections/${connection.id}`, { method: 'GET' }, 'Connection dependencies reviewed.') as {
        dependencies?: { configurations?: unknown[]; conversations?: unknown[]; defaultAffected?: boolean }
      }
      const dependencies = result.dependencies
      const parts = [
        dependencies?.defaultAffected ? 'the current default' : null,
        dependencies?.configurations?.length ? `${dependencies.configurations.length} configuration(s)` : null,
        dependencies?.conversations?.length ? `${dependencies.conversations.length} conversation selection(s)` : null,
      ].filter(Boolean)
      setDeleteSummary(parts.length ? `This will leave ${parts.join(', ')} unavailable.` : 'No saved choices currently depend on this connection.')
      setDeleteTarget(connection)
    } catch { /* the root live region already contains the safe message */ }
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    try {
      await mutate(`/api/ai-console/connections/${deleteTarget.id}`, {
        method: 'DELETE', body: JSON.stringify({ confirm: true }),
      }, 'Connection deleted. Dependent choices were left visible for repair.')
      setDeleteTarget(null)
    } catch { /* safe status is announced centrally */ }
  }

  const defaultMissing = providerDefault !== null
    && !(state?.models ?? []).some(model => model.connectionId === providerDefault.connectionId && model.modelId === providerDefault.modelId)

  return (
    <section className="aic-section" aria-labelledby="aic-provider-heading">
      <div className="aic-section-head">
        <div>
          <h2 id="aic-provider-heading">Provider connections</h2>
          <p className="aic-section-copy">Add named API connections. A model becomes available only after the server validates the credential and its compatible catalog.</p>
        </div>
        <button className="aic-button" data-primary="true" type="button" onClick={() => openEditor({ kind: 'add' })}><Plus aria-hidden="true" className="inline size-4" /> Add connection</button>
      </div>
      {state?.validationDisclosure && <p className="aic-disclosure"><strong>Charge notice.</strong> {state.validationDisclosure}</p>}
      {defaultMissing && providerDefault && <div className="aic-broken"><strong>Broken default.</strong> Provider choice {providerDefault.connectionId} / {providerDefault.modelId} is no longer available. Choose another default below.<div className="aic-model-row" data-default="true"><span className="aic-model-id">Unavailable provider choice</span><AiChoiceRadio choice={providerDefault} checked disabled unavailable label={`${providerDefault.connectionId} ${providerDefault.modelId}`} onSelect={onSelectDefault} /></div></div>}
      {loading ? <div className="aic-empty">Loading provider connections…</div> : connections.length === 0 ? (
        <div className="aic-empty">No provider connections yet. Add one to validate its available models.</div>
      ) : (
        <div className="aic-grid">
          {connections.map(connection => {
            const models = (state?.models ?? []).filter(model => model.connectionId === connection.id && (model.available
              || (providerDefault?.connectionId === connection.id && providerDefault.modelId === model.modelId)))
            return (
              <article className="aic-card" key={connection.id}>
                <div className="aic-card-head">
                  <div className="aic-card-title-row">
                    <div><span className="aic-provider-name">{PROVIDER_LABELS[connection.providerId]}</span><h3>{connection.name}</h3></div>
                    <StatusMark state={connection.validationState} />
                  </div>
                  <p className="aic-mask" aria-label="Saved credential mask">{connection.maskedSuffix}</p>
                  <p className="aic-meta">Last check · {formatCheckedAt(connection.lastCheckedAt ?? connection.lastValidatedAt)}</p>
                  {connection.deletedAt && <p className="aic-status"><AlertCircle aria-hidden="true" />Deleted connection — retained because a saved choice refers to it</p>}
                  {!connection.deletedAt && <div className="aic-actions">
                    <button className="aic-button" type="button" onClick={() => openEditor({ kind: 'test', connection })}>Test connection</button>
                    <button className="aic-button" type="button" onClick={() => openEditor({ kind: 'rename', connection })}>Rename</button>
                    <button className="aic-button" type="button" onClick={() => openEditor({ kind: 'replace', connection })}>Replace key</button>
                    <button className="aic-button" data-danger="true" type="button" onClick={() => previewDelete(connection)}>Delete</button>
                  </div>}
                </div>
                <div className="aic-model-list" aria-label={`${connection.name} models`}>
                  {models.length === 0 ? <div className="aic-model-row"><span className="aic-model-id">No compatible models available</span></div> : models.map(model => {
                    const choice = { kind: 'provider_model' as const, connectionId: connection.id, modelId: model.modelId }
                    const checked = choicesEqual(state?.defaultChoice ?? null, choice)
                    const usable = !connection.deletedAt && connection.validationState === 'validated' && model.available && supportsEveryRole(model.compatibleRoles)
                    return <div className="aic-model-row" data-default={checked} key={model.modelId}>
                      <div><span className="aic-model-name">{model.displayName}</span><span className="aic-model-id">{model.modelId}{!usable ? ' · unavailable for all four roles' : ''}</span></div>
                      <AiChoiceRadio choice={choice} checked={checked} disabled={!usable || mutationPending} unavailable={checked && !usable} label={`${connection.name} ${model.displayName}`} onSelect={onSelectDefault} />
                    </div>
                  })}
                </div>
              </article>
            )
          })}
        </div>
      )}

      <Dialog open={editor !== null} onOpenChange={open => { if (!open) { setEditor(null); setApiKey('') } }}>
        <DialogContent className="aic-dialog">
          <DialogHeader>
            <DialogTitle>{editor?.kind === 'add' ? 'Add provider connection' : editor?.kind === 'rename' ? 'Rename connection' : editor?.kind === 'replace' ? 'Replace API key' : 'Test connection'}</DialogTitle>
            <DialogDescription>{editor?.kind === 'rename' ? 'Names distinguish multiple credentials from the same provider.' : state?.validationDisclosure}</DialogDescription>
          </DialogHeader>
          <div className="aic-form">
            {editor?.kind === 'add' && <div className="aic-field"><label htmlFor="aic-provider">Provider</label><select id="aic-provider" value={providerId} onChange={event => setProviderId(event.target.value as ProviderId)}>{PROVIDERS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></div>}
            {(editor?.kind === 'add' || editor?.kind === 'rename') && <div className="aic-field"><label htmlFor="aic-connection-name">Connection name</label><input id="aic-connection-name" value={name} onChange={event => setName(event.target.value)} aria-invalid={fieldError.includes('name') || undefined} aria-describedby={fieldError ? 'aic-provider-error' : undefined} autoComplete="off" /></div>}
            {(editor?.kind === 'add' || editor?.kind === 'replace') && <div className="aic-field"><label htmlFor="aic-api-key">API key</label><input id="aic-api-key" type="password" value={apiKey} onChange={event => setApiKey(event.target.value)} aria-invalid={fieldError.includes('API key') || undefined} aria-describedby={fieldError ? 'aic-provider-error' : undefined} autoComplete="new-password" /></div>}
            {editor?.kind !== 'rename' && <label className="aic-disclosure"><input type="checkbox" checked={acknowledgeCharge} onChange={event => setAcknowledgeCharge(event.target.checked)} /> I understand that testing makes a tiny provider request and may create a small charge.</label>}
            {fieldError && <p id="aic-provider-error" className="aic-field-error" role="alert">{fieldError}</p>}
          </div>
          <DialogFooter><button className="aic-button" type="button" onClick={() => setEditor(null)}>Cancel</button><button className="aic-button" data-primary="true" type="button" disabled={mutationPending} onClick={submitEditor}>{mutationPending ? 'Working…' : editor?.kind === 'test' ? 'Test connection' : 'Save'}</button></DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteTarget !== null} onOpenChange={open => { if (!open) setDeleteTarget(null) }}>
        <AlertDialogContent className="aic-dialog">
          <AlertDialogHeader><AlertDialogTitle>Delete {deleteTarget?.name}?</AlertDialogTitle><AlertDialogDescription>{deleteSummary} The credential is removed from use; saved references are not silently changed.</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel><AlertDialogAction disabled={mutationPending} onClick={confirmDelete}>Delete connection</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  )
}
