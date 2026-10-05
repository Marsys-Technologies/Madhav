'use client'

import { useMemo, useState } from 'react'
import { AlertCircle, CheckCircle2, CircleDashed, Clock3, Plus, ShieldAlert, Pencil, Trash2, RotateCw, Settings2 } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { AiChoiceRadio } from './AiChoiceRadio'
import { CatalogRefreshControl } from './CatalogRefreshControl'
import { providerEffortLevels } from '@/lib/ai-console/effort'
import {
  AI_ROLES, PROVIDER_LABELS, ROLE_LABELS, choicesEqual, formatCheckedAt, hasCurrentProviderConfirmation,
  type AiChoice, type AiConsoleStateDto, type ConsoleMutation, type ProviderConnectionDto, type ProviderId, type CatalogRefresh, type CatalogRefreshStatus,
} from './types'

// Direct Kimi onboarding is retired; existing connections remain visible for repair.
const PROVIDERS = (Object.entries(PROVIDER_LABELS) as [ProviderId, string][]).filter(([id]) =>
  id === 'openai' || id === 'anthropic' || id === 'google' || id === 'openrouter')
const STATUS_LABELS: Record<ProviderConnectionDto['validationState'], string> = {
  untested: 'Not tested', validating: 'Testing', validated: 'Validated', needs_attention: 'Needs attention',
  invalid: 'Credential rejected', unreachable: 'Provider unreachable',
}

const FAILURE_GUIDANCE: Record<string, string> = {
  AI_BILLING_UNAVAILABLE: 'API billing, credits, or a spending limit is blocking this connection. Check the provider account, then test again.',
  AI_CONNECTION_INVALID: 'The provider rejected this key. Replace it with a key for the correct API product, then test again.',
  AI_PERMISSION_DENIED: 'The provider denied access. Check this key’s workspace and model permissions.',
  AI_MODEL_UNAVAILABLE: 'The provider did not make the tested model available to this key.',
  AI_RATE_LIMITED: 'The provider rate limit was reached. Wait before testing again.',
  AI_PROVIDER_UNREACHABLE: 'The provider could not be reached. Test again when its service is available.',
  AI_EXECUTION_FAILED: 'The provider check failed, but the precise reason was not identified. Check the provider account and API access before testing again.',
}

function validationFeedback(result: unknown): string {
  const validation = result && typeof result === 'object' && 'validation' in result ? result.validation : null
  if (!validation || typeof validation !== 'object' || !('state' in validation)) return 'Connection test returned no readable verdict.'
  if (validation.state === 'validated') return 'Connection validated. Its compatible models are now available.'
  return 'Connection is not ready. Review the reason on its card.'
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
  | { kind: 'workspace'; connection: ProviderConnectionDto }
  | { kind: 'test'; connection: ProviderConnectionDto }
  | null

interface Props {
  state?: AiConsoleStateDto
  loading: boolean
  error: boolean
  mutationPending: boolean
  mutate: ConsoleMutation
  onSelectDefault: (choice: AiChoice) => Promise<unknown>
  onConfigureRoles: (connectionId: string) => void
  onRefreshCatalog: CatalogRefresh
  refreshStatus: Record<string, CatalogRefreshStatus>
}

type ProviderErrorTarget = 'name' | 'apiKey' | 'workspaceId' | 'acknowledgement' | 'form'
interface ProviderFieldError { message: string; target: ProviderErrorTarget }

export function ProviderConnectionsSection({ state, loading, error, mutationPending, mutate, onSelectDefault, onConfigureRoles, onRefreshCatalog, refreshStatus }: Props) {
  const [editor, setEditor] = useState<Editor>(null)
  const [name, setName] = useState('')
  const [providerId, setProviderId] = useState<ProviderId>('openai')
  const [apiKey, setApiKey] = useState('')
  const [workspaceId, setWorkspaceId] = useState('')
  const [acknowledgeCharge, setAcknowledgeCharge] = useState(false)
  const [fieldError, setFieldError] = useState<ProviderFieldError | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<ProviderConnectionDto | null>(null)
  const [deleteSummary, setDeleteSummary] = useState('')
  const [modelManager, setModelManager] = useState<ProviderConnectionDto | null>(null)
  const [modelQuery, setModelQuery] = useState('')
  const [modelRole, setModelRole] = useState('all')
  const [modelScope, setModelScope] = useState<'shortlist' | 'catalog'>('shortlist')
  const [visibleLimit, setVisibleLimit] = useState(30)
  const [modelCharge, setModelCharge] = useState(false)
  const providerDefault = state?.defaultChoice?.kind === 'provider_model' ? state.defaultChoice : null

  const connections = useMemo(() => (state?.connections ?? []).filter(connection =>
    !connection.deletedAt || providerDefault?.connectionId === connection.id), [state, providerDefault])

  function openEditor(next: Exclude<Editor, null>) {
    setEditor(next)
    setName(next.kind === 'rename' ? next.connection.name : '')
    setProviderId(next.kind === 'add' ? 'openai' : next.connection.providerId)
    setApiKey('')
    setWorkspaceId(next.kind === 'add' ? '' : next.connection.workspaceId ?? '')
    setAcknowledgeCharge(false)
    setFieldError(null)
  }

  async function submitEditor() {
    if (!editor) return
    if ((editor.kind === 'add' || editor.kind === 'rename') && !name.trim()) {
      setFieldError({ message: 'Enter a connection name.', target: 'name' })
      return
    }
    if ((editor.kind === 'add' || editor.kind === 'replace') && !apiKey.trim()) {
      setFieldError({ message: 'Enter the API key.', target: 'apiKey' })
      return
    }
    if ((editor.kind === 'workspace' || (editor.kind === 'add' && providerId === 'anthropic'))
      && workspaceId.trim() && !/^wrkspc_[A-Za-z0-9]{20,64}$/.test(workspaceId.trim())) {
      setFieldError({ message: 'Enter a valid Claude workspace ID, starting with wrkspc_.', target: 'workspaceId' })
      return
    }
    if (editor.kind !== 'rename' && !acknowledgeCharge) {
      setFieldError({ message: 'Acknowledge the provider charge disclosure to continue.', target: 'acknowledgement' })
      return
    }
    setFieldError(null)
    try {
      if (editor.kind === 'add') {
        await mutate('/api/ai-console/connections', {
          method: 'POST', body: JSON.stringify({ name: name.trim(), providerId, apiKey,
            ...(providerId === 'anthropic' ? { workspaceId: workspaceId.trim() || null } : {}), acknowledgeCharge: true }),
        }, validationFeedback)
      } else if (editor.kind === 'rename') {
        await mutate(`/api/ai-console/connections/${editor.connection.id}`, {
          method: 'PATCH', body: JSON.stringify({ name: name.trim() }),
        }, 'Connection renamed.')
      } else if (editor.kind === 'replace') {
        await mutate(`/api/ai-console/connections/${editor.connection.id}`, {
          method: 'PATCH', body: JSON.stringify({ apiKey, acknowledgeCharge: true }),
        }, validationFeedback)
      } else if (editor.kind === 'workspace') {
        await mutate(`/api/ai-console/connections/${editor.connection.id}`, {
          method: 'PATCH', body: JSON.stringify({ workspaceId: workspaceId.trim() || null, acknowledgeCharge: true }),
        }, validationFeedback)
      } else {
        await mutate(`/api/ai-console/connections/${editor.connection.id}/validate`, {
          method: 'POST', body: JSON.stringify({ acknowledgeCharge: true }),
        }, validationFeedback)
      }
      setApiKey('')
      setWorkspaceId('')
      setEditor(null)
    } catch (error) {
      const message = error instanceof Error ? error.message : 'The request could not be completed safely.'
      setFieldError({
        message,
        target: message.includes('name is already in use') ? 'name'
          : (editor.kind === 'add' || editor.kind === 'replace') && message.includes('credential') ? 'apiKey'
            : 'form',
      })
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

  const catalog = (state?.models ?? []).filter(model => modelManager && model.connectionId === modelManager.id && model.available)
  const filteredCatalog = catalog.filter(model => (modelScope === 'catalog' || model.userSelected || modelQuery.trim())
    && (modelRole === 'all' || model.compatibleRoles.includes(modelRole as typeof model.compatibleRoles[number]))
    && `${model.displayName} ${model.modelId}`.toLowerCase().includes(modelQuery.trim().toLowerCase()))
    .sort((a, b) => Number(Boolean(b.userSelected)) - Number(Boolean(a.userSelected)) || a.displayName.localeCompare(b.displayName))

  async function testAndAddModel(modelId: string) {
    if (!modelManager || !modelCharge) return
    try {
      await mutate(`/api/ai-console/connections/${modelManager.id}/models`, {
        method: 'POST', body: JSON.stringify({ modelId, acknowledgeCharge: true }),
      }, 'Model generation tested and added to your shortlist.')
    } catch { /* safe status is announced centrally */ }
  }

  async function removeModel(modelId: string) {
    if (!modelManager) return
    try {
      await mutate(`/api/ai-console/connections/${modelManager.id}/models`, {
        method: 'DELETE', body: JSON.stringify({ modelId }),
      }, 'Model removed from your shortlist. Existing saved choices were not changed.')
    } catch { /* safe status is announced centrally */ }
  }

  return (
    <section className="aic-section" aria-labelledby="aic-provider-heading">
      <div className="aic-section-head">
        <div>
          <h2 id="aic-provider-heading">API connections</h2>
          <p className="aic-section-copy">Connect a provider, then test and add only the models you intend to use. A catalog listing alone does not confirm access to every model. For Kimi models, use OpenRouter.</p>
        </div>
        {!error && state && <button className="aic-button" data-primary="true" type="button" onClick={() => openEditor({ kind: 'add' })}><Plus aria-hidden="true" className="inline size-4" /> Add connection</button>}
      </div>
      {state?.validationDisclosure && <p className="aic-disclosure"><strong>Charge notice.</strong> {state.validationDisclosure}</p>}
      {!error && providerDefault && <div className="aic-broken"><strong>{defaultMissing ? 'Broken default.' : 'Earlier direct-model default.'}</strong> {defaultMissing ? `Provider choice ${providerDefault.connectionId} / ${providerDefault.modelId} is no longer available. Choose another default below.` : 'This saved choice remains active until you replace it with a four-role setup.'}<div className="aic-model-row" data-default="true"><span className="aic-model-id">{providerDefault.modelId}</span><AiChoiceRadio choice={providerDefault} checked disabled unavailable={defaultMissing} label={`${providerDefault.connectionId} ${providerDefault.modelId}`} onSelect={onSelectDefault} /></div></div>}
      {error ? <div className="aic-error" role="alert">Provider connections could not be loaded. Refresh the page to try again.</div> : loading ? <div className="aic-empty">Loading provider connections…</div> : connections.length === 0 ? (
        <div className="aic-empty">No provider connections yet. Add one to validate its available models.</div>
      ) : (
        <div className="aic-grid">
          {connections.map(connection => {
            const catalogCount = (state?.models ?? []).filter(model => model.connectionId === connection.id && model.available).length
            const models = (state?.models ?? []).filter(model => model.connectionId === connection.id && (model.userSelected
              || (providerDefault?.connectionId === connection.id && providerDefault.modelId === model.modelId)))
            const preset = state?.configurations.find(item => !item.deletedAt && item.configurationKind === 'provider_preset'
              && item.ownerConnectionId === connection.id)
            const presetChoice = preset ? { kind: 'custom_configuration' as const, configurationId: preset.id } : null
            const presetChecked = presetChoice ? choicesEqual(state?.defaultChoice ?? null, presetChoice) : false
            const presetReady = Boolean(preset && !connection.deletedAt && connection.providerId !== 'kimi'
              && hasCurrentProviderConfirmation(connection) && AI_ROLES.every(role => {
                const target = preset.roles[role]
                if (target.kind !== 'provider_model' || target.connectionId !== connection.id) return false
                const model = state?.models.find(item => item.connectionId === connection.id && item.modelId === target.modelId)
                return Boolean(model?.available && model.userSelected && model.plainTestedAt && model.compatibleRoles.includes(role)
                  && (!target.effort || (model.supportedEfforts ?? providerEffortLevels(connection.providerId, target.modelId)).includes(target.effort)))
              }))
            const canConfigureRoles = connection.providerId !== 'kimi' && hasCurrentProviderConfirmation(connection)
              && AI_ROLES.every(role => (state?.models ?? []).some(model => model.connectionId === connection.id
                && model.available && model.userSelected && model.plainTestedAt && model.compatibleRoles.includes(role)))
            return (
              <article className="aic-card" key={connection.id}>
                <div className="aic-card-head">
                  <div className="aic-card-title-row">
                    <div><span className="aic-provider-name">{PROVIDER_LABELS[connection.providerId]}</span><h3>{connection.name}</h3></div>
                    <StatusMark state={connection.validationState} />
                  </div>
                  <p className="aic-mask" aria-label="Saved credential mask">{connection.maskedSuffix}</p>
                  {connection.providerId === 'anthropic' && !connection.workspaceId && connection.validationState !== 'validated' &&
                    <p className="aic-meta">Organization-wide Claude keys need a workspace ID. Set it here, then test the existing key.</p>}
                  {connection.providerId === 'anthropic' && connection.workspaceId && connection.validationState === 'needs_attention' &&
                    <p className="aic-meta">The key was retained. Check whether this workspace ID belongs to the key, then run Test connection. Replace the key only if the provider rejects it.</p>}
                  <p className="aic-meta">Last check · {formatCheckedAt(connection.lastCheckedAt ?? connection.lastValidatedAt)}</p>
                  {!connection.deletedAt && connection.providerId !== 'kimi' && hasCurrentProviderConfirmation(connection) && <CatalogRefreshControl
                    name={connection.name} kind="connection" refreshedAt={connection.catalogRefreshedAt}
                    errorCode={connection.catalogErrorCode} status={refreshStatus[`connection:${connection.id}`]}
                    onRefresh={() => void onRefreshCatalog('connection', connection.id, true)} />}
                  {connection.validationState !== 'validated' && connection.lastErrorCode && (
                    <p className="aic-failure-guidance">{FAILURE_GUIDANCE[connection.lastErrorCode] ?? FAILURE_GUIDANCE.AI_EXECUTION_FAILED}</p>
                  )}
                  {connection.deletedAt && <p className="aic-status"><AlertCircle aria-hidden="true" />Deleted connection — retained because a saved choice refers to it</p>}
                  {connection.providerId === 'kimi' && !connection.deletedAt && <p className="aic-failure-guidance">Direct Kimi API setup is retired. Use a Kimi model through OpenRouter. Existing saved choices remain visible until you replace or remove them.</p>}
                  {!connection.deletedAt && <div className="aic-actions">
                    {connection.providerId !== 'kimi' && <><button className="aic-button" data-primary="true" type="button" onClick={() => { setModelManager(connection); setModelQuery(''); setModelRole('all'); setModelScope('shortlist'); setVisibleLimit(30); setModelCharge(false) }}>Manage models ({models.length}/{catalogCount})</button>
                    <button className="aic-button" type="button" onClick={() => openEditor({ kind: 'replace', connection })}>Replace key</button>
                    <button className="aic-button" type="button" disabled={!preset && !canConfigureRoles} title={!preset && !canConfigureRoles ? 'Test and add models compatible with all four roles first' : undefined} onClick={() => onConfigureRoles(connection.id)}>{preset ? 'Edit four roles' : 'Set up four roles'}</button></>}
                    <div className="aic-card-menu" aria-label={`${connection.name} more actions`}>
                      {connection.providerId !== 'kimi' && <button className="aic-button aic-icon-button" type="button" aria-label={`Test ${connection.name} connection`} title="Test connection" onClick={() => openEditor({ kind: 'test', connection })}><RotateCw aria-hidden="true" /></button>}
                      <button className="aic-button aic-icon-button" type="button" aria-label={`Rename ${connection.name} connection`} title="Rename" onClick={() => openEditor({ kind: 'rename', connection })}><Pencil aria-hidden="true" /></button>
                      {connection.providerId === 'anthropic' && <button className="aic-button aic-icon-button" type="button" aria-label="Workspace ID" title="Workspace ID" onClick={() => openEditor({ kind: 'workspace', connection })}><Settings2 aria-hidden="true" /></button>}
                      <button className="aic-button aic-icon-button" data-danger="true" type="button" aria-label={`Delete ${connection.name} connection`} title="Delete" onClick={() => previewDelete(connection)}><Trash2 aria-hidden="true" /></button>
                    </div>
                  </div>}
                  {!connection.deletedAt && connection.providerId !== 'kimi' && !canConfigureRoles && hasCurrentProviderConfirmation(connection) && <p className="aic-meta">To set up four roles, test and add models that cover each role in Manage models.</p>}
                </div>
                {preset && <div className="aic-role-grid aic-card-roles">{AI_ROLES.map(role => <div className="aic-role-row" key={role}><span className="aic-role-label">{ROLE_LABELS[role]}</span><span className="aic-model-id">{preset.roles[role].modelId ?? 'Built-in default'} · Effort: {preset.roles[role].effort ?? 'model default'}</span></div>)}</div>}
                <div className="aic-model-row" data-default={presetChecked}><div><span className="aic-model-name">{preset ? 'Provider role setup' : 'Role setup needed'}</span><span className="aic-model-id">{presetReady ? 'All four roles use tested models from this provider' : connection.providerId === 'kimi' ? 'Direct Kimi API retired · use OpenRouter' : 'Set up four roles with tested models before selecting as default'}</span></div>{presetChoice && <AiChoiceRadio choice={presetChoice} checked={presetChecked} disabled={!presetReady || mutationPending} unavailable={presetChecked && !presetReady} label={connection.name} onSelect={onSelectDefault} />}</div>
                <div className="aic-model-list" aria-label={`${connection.name} models`}>
                  {models.length === 0 ? <div className="aic-model-row"><span className="aic-model-id">No models in your shortlist. Open Manage models to test and add one.</span></div> : models.map(model => {
                    return <div className="aic-model-row" key={model.modelId}>
                      <div><span className="aic-model-name">{model.displayName}</span><span className="aic-model-id">{model.modelId} · {model.lastProbeErrorCode ? `Latest test failed · ${model.lastProbeErrorCode}` : model.plainTestedAt ? `Generation tested ${formatCheckedAt(model.plainTestedAt)}` : 'Saved before individual model testing'}{model.lastProbeInputTokens != null || model.lastProbeOutputTokens != null ? ` · test tokens ${model.lastProbeInputTokens ?? '?'}/${model.lastProbeOutputTokens ?? '?'} in/out` : ''}</span></div>
                    </div>
                  })}
                </div>
              </article>
            )
          })}
        </div>
      )}

      <Dialog open={modelManager !== null} onOpenChange={open => { if (!open) setModelManager(null) }}>
        <DialogContent className="pp-root aic-dialog aic-model-manager">
          <DialogHeader><DialogTitle>Manage {modelManager?.name} models</DialogTitle><DialogDescription>Browse this provider’s catalog. Only models you test and add appear in your shortlist and the question picker. A successful generation check does not verify every role or structured response.</DialogDescription></DialogHeader>
          <div className="aic-manager-controls">
            <div className="aic-field"><label htmlFor="aic-model-scope">View</label><select id="aic-model-scope" value={modelScope} onChange={event => { setModelScope(event.target.value as 'shortlist' | 'catalog'); setVisibleLimit(30) }}><option value="shortlist">My shortlist</option><option value="catalog">Full catalog</option></select></div>
            <div className="aic-field"><label htmlFor="aic-model-search">Find a model</label><input id="aic-model-search" type="search" value={modelQuery} onChange={event => { setModelQuery(event.target.value); setVisibleLimit(30) }} placeholder="Search model name or ID" /></div>
            <div className="aic-field"><label htmlFor="aic-model-role">Role support</label><select id="aic-model-role" value={modelRole} onChange={event => { setModelRole(event.target.value); setVisibleLimit(30) }}><option value="all">Any role</option><option value="synthesizer">Synthesizer</option><option value="planner">Planner</option><option value="deep_planner">Deep Planner</option><option value="worker">Worker</option></select></div>
          </div>
          <p className="aic-meta">Showing {Math.min(visibleLimit, filteredCatalog.length)} of {filteredCatalog.length} matching models. Your shortlist is shown first; search or choose Full catalog to explore other models. Catalog entries have not all been individually tested.</p>
          <label className="aic-disclosure" htmlFor="aic-model-charge"><input id="aic-model-charge" type="checkbox" checked={modelCharge} onChange={event => setModelCharge(event.target.checked)} /> I understand each model test makes a tiny provider request and may create a small charge.</label>
          <div className="aic-manager-results">
            {filteredCatalog.length === 0 && <p className="aic-empty">{modelScope === 'shortlist' && !modelQuery.trim() ? 'Your shortlist is empty. Choose Full catalog, then test and add only the models you want to use.' : 'No matching models in the current catalog.'}</p>}
            {filteredCatalog.slice(0, visibleLimit).map(model => <div className="aic-manager-row" key={model.modelId}>
              <div><span className="aic-model-name">{model.displayName}</span><span className="aic-model-id">{model.modelId}</span><span className="aic-model-id">{model.lastProbeErrorCode ? `Last test failed · ${model.lastProbeErrorCode}` : model.plainTestedAt ? `Generation tested ${formatCheckedAt(model.plainTestedAt)}` : 'Listed · not individually tested'}{model.lastProbeInputTokens != null || model.lastProbeOutputTokens != null ? ` · test tokens ${model.lastProbeInputTokens ?? '?'}/${model.lastProbeOutputTokens ?? '?'} in/out` : ''}</span></div>
              {model.userSelected ? <div className="aic-actions"><button className="aic-button" type="button" aria-label={`${model.plainTestedAt ? 'Retest' : 'Test'} ${model.displayName}`} disabled={!modelCharge || mutationPending || !modelManager || !hasCurrentProviderConfirmation(modelManager)} onClick={() => testAndAddModel(model.modelId)}>{model.plainTestedAt ? 'Retest' : 'Test'}</button><button className="aic-button" type="button" aria-label={`Remove ${model.displayName} from shortlist`} disabled={mutationPending} onClick={() => removeModel(model.modelId)}>Remove</button></div>
                : <button className="aic-button" data-primary="true" type="button" aria-label={`Test and add ${model.displayName}`} disabled={!modelCharge || mutationPending || !modelManager || !hasCurrentProviderConfirmation(modelManager)} onClick={() => testAndAddModel(model.modelId)}>Test and add</button>}
            </div>)}
          </div>
          {visibleLimit < filteredCatalog.length && <button className="aic-button" type="button" onClick={() => setVisibleLimit(limit => limit + 30)}>Show 30 more</button>}
        </DialogContent>
      </Dialog>

      <Dialog open={editor !== null} onOpenChange={open => { if (!open) { setEditor(null); setApiKey('') } }}>
        <DialogContent className="pp-root aic-dialog">
          <DialogHeader>
            <DialogTitle>{editor?.kind === 'add' ? 'Add provider connection' : editor?.kind === 'rename' ? 'Rename connection' : editor?.kind === 'replace' ? 'Replace API key' : editor?.kind === 'workspace' ? 'Set Claude workspace' : 'Test connection'}</DialogTitle>
            <DialogDescription>{editor?.kind === 'rename' ? 'Names distinguish multiple credentials from the same provider.' : state?.validationDisclosure}</DialogDescription>
          </DialogHeader>
          <div className="aic-form">
            {editor?.kind === 'add' && <div className="aic-field"><label htmlFor="aic-provider">Provider</label><select id="aic-provider" value={providerId} onChange={event => setProviderId(event.target.value as ProviderId)}>{PROVIDERS.map(([id, label]) => <option key={id} value={id}>{label}</option>)}</select></div>}
            {(editor?.kind === 'add' || editor?.kind === 'rename') && <div className="aic-field"><label htmlFor="aic-connection-name">Connection name</label><input id="aic-connection-name" value={name} onChange={event => { setName(event.target.value); if (fieldError?.target === 'name') setFieldError(null) }} aria-invalid={fieldError?.target === 'name' || undefined} aria-describedby={fieldError?.target === 'name' ? 'aic-provider-error' : undefined} autoComplete="off" /></div>}
            {(editor?.kind === 'add' || editor?.kind === 'replace') && <div className="aic-field"><label htmlFor="aic-api-key">API key</label><input id="aic-api-key" type="password" value={apiKey} onChange={event => { setApiKey(event.target.value); if (fieldError?.target === 'apiKey') setFieldError(null) }} aria-invalid={fieldError?.target === 'apiKey' || undefined} aria-describedby={fieldError?.target === 'apiKey' ? 'aic-provider-error' : undefined} autoComplete="new-password" /></div>}
            {((editor?.kind === 'add' && providerId === 'anthropic') || editor?.kind === 'workspace') && <div className="aic-field"><label htmlFor="aic-workspace-id">Claude workspace ID (for organization-wide keys)</label><input id="aic-workspace-id" value={workspaceId} onChange={event => { setWorkspaceId(event.target.value); if (fieldError?.target === 'workspaceId') setFieldError(null) }} aria-invalid={fieldError?.target === 'workspaceId' || undefined} aria-describedby={fieldError?.target === 'workspaceId' ? 'aic-provider-error' : undefined} placeholder="wrkspc_…" autoComplete="off" /><p className="aic-meta">Find the ID in Claude Platform → Settings → Workspaces. Leave blank for a workspace-scoped key.</p></div>}
            {editor?.kind !== 'rename' && <label className="aic-disclosure" htmlFor="aic-charge-acknowledgement"><input id="aic-charge-acknowledgement" type="checkbox" checked={acknowledgeCharge} onChange={event => { setAcknowledgeCharge(event.target.checked); if (fieldError?.target === 'acknowledgement') setFieldError(null) }} aria-invalid={fieldError?.target === 'acknowledgement' || undefined} aria-describedby={fieldError?.target === 'acknowledgement' ? 'aic-provider-error' : undefined} /> I understand that testing makes a tiny provider request and may create a small charge.</label>}
            {fieldError && <p id="aic-provider-error" className="aic-field-error" role="alert">{fieldError.message}</p>}
          </div>
          <DialogFooter><button className="aic-button" type="button" onClick={() => setEditor(null)}>Cancel</button><button className="aic-button" data-primary="true" type="button" disabled={mutationPending} onClick={submitEditor}>{mutationPending ? 'Working…' : editor?.kind === 'test' ? 'Test connection' : 'Save'}</button></DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteTarget !== null} onOpenChange={open => { if (!open) setDeleteTarget(null) }}>
        <AlertDialogContent className="pp-root aic-dialog">
          <AlertDialogHeader><AlertDialogTitle>Delete {deleteTarget?.name}?</AlertDialogTitle><AlertDialogDescription>{deleteSummary} The credential is removed from use; saved references are not silently changed.</AlertDialogDescription></AlertDialogHeader>
          <AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel><AlertDialogAction disabled={mutationPending} onClick={confirmDelete}>Delete connection</AlertDialogAction></AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  )
}
