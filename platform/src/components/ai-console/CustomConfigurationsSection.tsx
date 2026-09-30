'use client'

import { useMemo, useState } from 'react'
import { AlertCircle, Copy, Plus } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { AiChoiceRadio } from './AiChoiceRadio'
import {
  AI_ROLES, PROVIDER_LABELS, ROLE_LABELS, choicesEqual, hasCurrentProviderConfirmation,
  type AiChoice, type AiConsoleStateDto, type AiRole, type CliCardDto, type ConfigurationDto, type ConfigurationKind,
  type ConsoleMutation, type RoleTarget,
} from './types'

interface Props {
  mode: 'api' | 'cli'
  state?: AiConsoleStateDto
  clis: CliCardDto[]
  loading: boolean
  error: boolean
  cliStatus: 'loading' | 'error' | 'ready'
  mutationPending: boolean
  mutate: ConsoleMutation
  onSelectDefault: (choice: AiChoice) => Promise<unknown>
  seed?: { sourceId: string; nonce: number } | null
  onSeedDismiss?: () => void
}

interface RoleDraft { source: string; model: string }
type Drafts = Record<AiRole, RoleDraft>
const EMPTY_DRAFTS = (): Drafts => Object.fromEntries(AI_ROLES.map(role => [role, { source: '', model: '' }])) as Drafts
const encodeModel = (value: string | null) => value === null ? '__builtin__' : value

function sourceFor(target: RoleTarget) {
  return target.kind === 'provider_model' ? `provider:${target.connectionId}` : `cli:${target.cliId}`
}

type ConfigurationAvailability = 'usable' | 'unusable' | 'unknown'

function configurationAvailability(
  configuration: ConfigurationDto,
  state: AiConsoleStateDto | undefined,
  clis: CliCardDto[],
  cliStatus: Props['cliStatus'],
): ConfigurationAvailability {
  if (configuration.deletedAt) return 'unusable'
  let unknown = false
  const usable = AI_ROLES.every(role => {
    const target = configuration.roles[role]
    if (target.kind === 'provider_model') {
      const connection = state?.connections.find(item => item.id === target.connectionId)
      const model = state?.models.find(item => item.connectionId === target.connectionId && item.modelId === target.modelId)
      return Boolean(connection && hasCurrentProviderConfirmation(connection) && !connection.deletedAt && model?.available === true
        && model.userSelected && model.plainTestedAt && model.compatibleRoles.includes(role))
    }
    if (cliStatus !== 'ready') { unknown = true; return true }
    const cli = clis.find(item => item.cliId === target.cliId)
    return cli?.state === 'reachable' && cli.models.some(model => model.modelId === target.modelId && model.compatibleRoles.includes(role))
  })
  return !usable ? 'unusable' : unknown ? 'unknown' : 'usable'
}

interface ConfigurationFieldError { message: string; target: 'name' | 'roles' | 'form' }

export function CustomConfigurationsSection({ mode, state, clis, loading, error, cliStatus, mutationPending, mutate, onSelectDefault, seed, onSeedDismiss }: Props) {
  const seedCli = mode === 'cli' && seed && cliStatus === 'ready'
    ? clis.find(item => item.cliId === seed.sourceId && item.state === 'reachable') : null
  const seedConnection = mode === 'api' && seed
    ? state?.connections.find(item => item.id === seed.sourceId && !item.deletedAt) : null
  const seededPreset = seed ? state?.configurations.find(item => !item.deletedAt && (mode === 'api'
    ? item.configurationKind === 'provider_preset' && item.ownerConnectionId === seed.sourceId
    : item.configurationKind === 'cli_preset' && item.ownerCliId === seed.sourceId)) ?? null : null
  const [editorOpen, setEditorOpen] = useState(Boolean(seedCli || seedConnection))
  const [editing, setEditing] = useState<ConfigurationDto | null>(seededPreset)
  const [name, setName] = useState(seededPreset?.name ?? (seedCli ? `${seedCli.productName} roles` : seedConnection ? `${seedConnection.name} roles` : ''))
  const [drafts, setDrafts] = useState<Drafts>(() => {
    const next = EMPTY_DRAFTS()
    if (seededPreset) {
      for (const role of AI_ROLES) next[role] = { source: sourceFor(seededPreset.roles[role]), model: encodeModel(seededPreset.roles[role].modelId) }
      return next
    }
    if (seedCli?.state === 'reachable') for (const role of AI_ROLES) {
      const model = seedCli.models.find(item => item.isBuiltinDefault && item.compatibleRoles.includes(role))
      if (model) next[role] = { source: `cli:${seedCli.cliId}`, model: encodeModel(model.modelId) }
    }
    if (seedConnection) for (const role of AI_ROLES) {
      const model = state?.models.find(item => item.connectionId === seedConnection.id && item.available
        && item.userSelected && item.plainTestedAt && item.compatibleRoles.includes(role))
      if (model) next[role] = { source: `provider:${seedConnection.id}`, model: encodeModel(model.modelId) }
    }
    return next
  })
  const [fieldError, setFieldError] = useState<ConfigurationFieldError | null>(null)
  const [duplicateTarget, setDuplicateTarget] = useState<ConfigurationDto | null>(null)
  const [duplicateName, setDuplicateName] = useState('')
  const [duplicateError, setDuplicateError] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<ConfigurationDto | null>(null)
  const [deleteSummary, setDeleteSummary] = useState('')
  const configurationDefault = state?.defaultChoice?.kind === 'custom_configuration' ? state.defaultChoice : null

  const configurations = useMemo(() => (state?.configurations ?? []).filter(configuration =>
    (mode === 'api' ? configuration.configurationKind === 'custom_api' || configuration.configurationKind === 'legacy_mixed'
      : configuration.configurationKind === 'custom_cli')
    && (!configuration.deletedAt || configurationDefault?.configurationId === configuration.id)), [state, configurationDefault, mode])

  const sources = useMemo(() => {
    const providerSources = mode === 'api' ? (state?.connections ?? []).filter(connection => !connection.deletedAt
      && connection.providerId !== 'kimi'
      && hasCurrentProviderConfirmation(connection) && (!seedConnection || connection.id === seedConnection.id))
      .map(connection => ({ value: `provider:${connection.id}`, label: `${connection.name} · ${PROVIDER_LABELS[connection.providerId]}` }))
      : []
    const cliSources = mode === 'cli' && cliStatus === 'ready' ? clis.filter(cli => cli.state === 'reachable'
      && (!seedCli || cli.cliId === seedCli.cliId))
      .map(cli => ({ value: `cli:${cli.cliId}`, label: cli.productName }))
      : []
    return [...providerSources, ...cliSources]
  }, [state, clis, cliStatus, mode, seedConnection, seedCli])
  const selectableSourceValues = useMemo(() => new Set(sources.map(source => source.value)), [sources])

  function modelOptions(source: string, role: AiRole) {
    if (!selectableSourceValues.has(source)) return []
    const [kind, id] = source.split(':', 2)
    if (kind === 'provider') return (state?.models ?? []).filter(model => model.connectionId === id && model.available
      && model.userSelected && model.plainTestedAt && model.compatibleRoles.includes(role))
      .map(model => ({ value: encodeModel(model.modelId), label: model.displayName, target: { kind: 'provider_model' as const, connectionId: id, modelId: model.modelId } }))
    if (kind === 'cli') {
      const cli = clis.find(item => item.cliId === id)
      if (cli?.state !== 'reachable') return []
      return cli.models.filter(model => model.compatibleRoles.includes(role)).map(model => ({ value: encodeModel(model.modelId),
        label: `${model.displayName}${model.isBuiltinDefault ? ' · validated default' : cli.cliId === 'codex' || cli.cliId === 'claude_code' ? ' · individually tested' : ' · discovered, not individually tested'}`,
        target: { kind: 'local_cli' as const, cliId: cli.cliId, modelId: model.modelId } }))
    }
    return []
  }

  function openNew() {
    const suggested = Object.fromEntries(AI_ROLES.map(role => {
      const source = sources.find(item => modelOptions(item.value, role).length > 0)?.value ?? ''
      return [role, { source, model: source ? modelOptions(source, role)[0].value : '' }]
    })) as Drafts
    setEditing(null); setName(''); setDrafts(suggested); setFieldError(null); setEditorOpen(true)
  }

  function openEdit(configuration: ConfigurationDto) {
    const next = EMPTY_DRAFTS()
    for (const role of AI_ROLES) next[role] = { source: sourceFor(configuration.roles[role]), model: encodeModel(configuration.roles[role].modelId) }
    setEditing(configuration); setName(configuration.name); setDrafts(next); setFieldError(null); setEditorOpen(true)
  }

  function updateDraft(role: AiRole, field: keyof RoleDraft, value: string) {
    setDrafts(current => ({ ...current, [role]: field === 'source' ? { source: value, model: '' } : { ...current[role], model: value } }))
  }

  function targetFor(role: AiRole): RoleTarget | null {
    const draft = drafts[role]
    return modelOptions(draft.source, role).find(option => option.value === draft.model)?.target ?? null
  }

  function sourceUnavailable(role: AiRole): boolean {
    return Boolean(drafts[role].source) && !selectableSourceValues.has(drafts[role].source)
  }

  function modelUnavailable(role: AiRole): boolean {
    const draft = drafts[role]
    return Boolean(draft.source && !sourceUnavailable(role) && draft.model
      && !modelOptions(draft.source, role).some(option => option.value === draft.model))
  }

  function targetLabel(target: RoleTarget): string {
    if (target.kind === 'provider_model') {
      const connection = state?.connections.find(item => item.id === target.connectionId)
      const model = state?.models.find(item => item.connectionId === target.connectionId && item.modelId === target.modelId)
      return `${connection?.name ?? 'Unavailable connection'} · ${model?.displayName ?? target.modelId}`
    }
    const cli = clis.find(item => item.cliId === target.cliId)
    const model = cli?.state === 'reachable' ? cli.models.find(item => item.modelId === target.modelId) : null
    return `${cli?.productName ?? target.cliId} · ${model?.displayName ?? target.modelId ?? 'Built-in default'}`
  }

  const complete = Boolean(name.trim()) && AI_ROLES.every(role => targetFor(role) !== null)
  const hasUnavailableSource = AI_ROLES.some(sourceUnavailable)
  const hasUnavailableModel = AI_ROLES.some(modelUnavailable)
  const fillAllTarget = targetFor('synthesizer')
  const canFillAll = fillAllTarget !== null && AI_ROLES.every(role => modelOptions(drafts.synthesizer.source, role).some(option => option.value === drafts.synthesizer.model))

  function fillAllRoles() {
    if (!canFillAll) return
    setDrafts(Object.fromEntries(AI_ROLES.map(role => [role, { ...drafts.synthesizer }])) as Drafts)
  }

  async function saveConfiguration() {
    if (!complete) { setFieldError({ message: 'Name the configuration and choose a compatible source and model for all four roles.', target: name.trim() ? 'roles' : 'name' }); return }
    const roles = Object.fromEntries(AI_ROLES.map(role => [role, targetFor(role)])) as Record<AiRole, RoleTarget>
    const configurationKind: ConfigurationKind = editing?.configurationKind ?? (seed
      ? mode === 'api' ? 'provider_preset' : 'cli_preset'
      : mode === 'api' ? 'custom_api' : 'custom_cli')
    const scope = { configurationKind,
      ownerConnectionId: configurationKind === 'provider_preset' ? seed?.sourceId ?? editing?.ownerConnectionId ?? null : null,
      ownerCliId: configurationKind === 'cli_preset' ? seed?.sourceId ?? editing?.ownerCliId ?? null : null }
    try {
      await mutate(editing ? `/api/ai-console/configurations/${editing.id}` : '/api/ai-console/configurations', {
        method: editing ? 'PATCH' : 'POST',
        body: JSON.stringify(editing ? { name: name.trim(), expectedVersion: editing.version, roles, ...scope }
          : { name: name.trim(), roles, ...scope }),
      }, editing ? 'Configuration updated.' : 'Configuration created.')
      setEditorOpen(false)
      onSeedDismiss?.()
    } catch (error) {
      const message = error instanceof Error ? error.message : 'The request could not be completed safely.'
      setFieldError({ message, target: message.includes('name is already in use') ? 'name' : 'form' })
    }
  }

  async function duplicateConfiguration() {
    if (!duplicateTarget || !duplicateName.trim()) return
    try {
      await mutate('/api/ai-console/configurations', { method: 'POST', body: JSON.stringify({ name: duplicateName.trim(), duplicateFrom: duplicateTarget.id }) }, 'Configuration duplicated.')
      setDuplicateTarget(null)
      setDuplicateError('')
    } catch (error) { setDuplicateError(error instanceof Error ? error.message : 'The request could not be completed safely.') }
  }

  async function previewDelete(configuration: ConfigurationDto) {
    try {
      const result = await mutate(`/api/ai-console/configurations/${configuration.id}`, { method: 'GET' }, 'Configuration dependencies reviewed.') as { dependencies?: { conversations?: unknown[]; defaultAffected?: boolean } }
      const parts = [result.dependencies?.defaultAffected ? 'the current default' : null,
        result.dependencies?.conversations?.length ? `${result.dependencies.conversations.length} conversation selection(s)` : null].filter(Boolean)
      setDeleteSummary(parts.length ? `This will leave ${parts.join(' and ')} unavailable.` : 'No saved choice currently depends on this configuration.')
      setDeleteTarget(configuration)
    } catch { /* safe status is announced centrally */ }
  }

  async function confirmDelete() {
    if (!deleteTarget) return
    try {
      await mutate(`/api/ai-console/configurations/${deleteTarget.id}`, { method: 'DELETE', body: JSON.stringify({ confirm: true }) }, 'Configuration deleted. Saved references remain visible for repair.')
      setDeleteTarget(null)
    } catch { /* safe status is announced centrally */ }
  }

  const defaultMissing = mode === 'api' && configurationDefault !== null
    && !(state?.configurations ?? []).some(configuration => configuration.id === configurationDefault.configurationId)

  return (
    <section className="aic-section aic-subsection" aria-labelledby={`aic-config-heading-${mode}`}>
      <div className="aic-section-head"><div><h2 id={`aic-config-heading-${mode}`}>Custom {mode === 'api' ? 'API' : 'CLI'} configurations</h2><p className="aic-section-copy">{mode === 'api' ? 'Combine generation-tested models from your connected API providers across the four roles.' : 'Combine reachable local subscriptions across the four roles. A discovered model is not necessarily individually tested.'}</p></div>{!error && state && <button className="aic-button" data-primary="true" type="button" onClick={openNew}><Plus aria-hidden="true" className="inline size-4" /> New configuration</button>}</div>
      {!error && defaultMissing && configurationDefault && <div className="aic-broken"><strong>Broken default.</strong> Configuration {configurationDefault.configurationId} is no longer available. Choose another default.<div className="aic-model-row" data-default="true"><span className="aic-model-id">Unavailable configuration</span><AiChoiceRadio choice={configurationDefault} checked disabled unavailable label={configurationDefault.configurationId} onSelect={onSelectDefault} /></div></div>}
      {error ? <div className="aic-error" role="alert">Custom configurations could not be loaded. Refresh the page to try again.</div> : loading ? <div className="aic-empty">Loading custom configurations…</div> : configurations.length === 0 ? <div className="aic-empty">No custom configurations yet. Create one when you want different models to handle different roles.</div> : (
        <div className="aic-grid">{configurations.map(configuration => {
          const availability = configurationAvailability(configuration, state, clis, cliStatus)
          const usable = availability === 'usable'
          const choice = { kind: 'custom_configuration' as const, configurationId: configuration.id }
          const checked = choicesEqual(state?.defaultChoice ?? null, choice)
          const requiresCliState = AI_ROLES.some(role => configuration.roles[role].kind === 'local_cli')
          return <article className="aic-card" key={configuration.id}>
            <div className="aic-card-head">
              <div className="aic-card-title-row"><div><span className="aic-provider-name">Configuration · v{configuration.version}</span><h3>{configuration.name}</h3></div>{availability === 'unusable' && <span className="aic-status"><AlertCircle aria-hidden="true" />Needs repair</span>}{availability === 'unknown' && <span className="aic-status"><AlertCircle aria-hidden="true" />CLI availability unavailable</span>}</div>
              <div className="aic-role-grid">{AI_ROLES.map(role => <div className="aic-role-row" key={role}><span className="aic-role-label">{ROLE_LABELS[role]}</span><span className="aic-model-id">{targetLabel(configuration.roles[role])}</span></div>)}</div>
              {!configuration.deletedAt && <div className="aic-actions">{configuration.configurationKind !== 'legacy_mixed' ? <><button className="aic-button" type="button" disabled={requiresCliState && cliStatus !== 'ready'} onClick={() => openEdit(configuration)}>Edit</button><button className="aic-button" type="button" onClick={() => { setDuplicateTarget(configuration); setDuplicateName(`${configuration.name} copy`); setDuplicateError('') }}><Copy aria-hidden="true" className="inline size-3" /> Duplicate</button></> : <span className="aic-meta">Earlier mixed configuration · recreate within API or CLI</span>}<button className="aic-button" data-danger="true" type="button" onClick={() => previewDelete(configuration)}>Delete</button></div>}
            </div>
            <div className="aic-model-list"><div className="aic-model-row" data-default={checked}><div><span className="aic-model-name">Use this configuration</span><span className="aic-model-id">{usable ? 'All four roles are currently available' : availability === 'unknown' ? 'Local CLI availability could not be verified' : 'One or more exact role choices are unavailable'}</span></div><AiChoiceRadio choice={choice} checked={checked} disabled={!usable || mutationPending} unavailable={checked && availability === 'unusable'} unverified={availability === 'unknown'} label={configuration.name} onSelect={onSelectDefault} /></div></div>
          </article>
        })}</div>
      )}

      <Dialog open={editorOpen} onOpenChange={open => { setEditorOpen(open); if (!open) onSeedDismiss?.() }}><DialogContent className="pp-root aic-dialog aic-role-dialog">
        <DialogHeader><DialogTitle>{seed ? editing ? 'Edit role setup' : 'Set up four roles' : editing ? 'Edit custom configuration' : 'New custom configuration'}</DialogTitle><DialogDescription>{seed ? `Only ${mode === 'api' ? seedConnection?.name ?? 'this API provider' : seedCli?.productName ?? 'this local CLI'} models can be used in this setup. ` : ''}Available choices are suggested where possible; review each role before saving. API models have passed a small generation test, not a full role execution test. Discovered CLI models may still fail at execution.</DialogDescription></DialogHeader>
        <div className="aic-form">
          <div className="aic-field"><label htmlFor="aic-config-name">Configuration name</label><input id="aic-config-name" value={name} onChange={event => { setName(event.target.value); if (fieldError?.target === 'name') setFieldError(null) }} aria-invalid={fieldError?.target === 'name' || undefined} aria-describedby={fieldError?.target === 'name' ? 'aic-config-error' : undefined} /></div>
          {AI_ROLES.map(role => {
            const unavailableSource = sourceUnavailable(role)
            const options = modelOptions(drafts[role].source, role)
            const unavailableModel = modelUnavailable(role)
            const retainedStaleModel = Boolean(drafts[role].model) && !options.some(option => option.value === drafts[role].model)
            const missingRoleSource = fieldError?.target === 'roles' && !drafts[role].source
            const missingRoleModel = fieldError?.target === 'roles' && !drafts[role].model
            const sourceDescription = [unavailableSource ? 'aic-source-repair' : null, missingRoleSource ? 'aic-config-error' : null].filter(Boolean).join(' ') || undefined
            const modelDescription = [unavailableModel ? 'aic-model-repair' : null, missingRoleModel ? 'aic-config-error' : null].filter(Boolean).join(' ') || undefined
            return <div className="aic-editor-role" role="group" aria-labelledby={`aic-${role}-label`} key={role}><span id={`aic-${role}-label`}>{ROLE_LABELS[role]}</span><div className="aic-field"><label htmlFor={`aic-${role}-source`}>Source <span className="sr-only">for {ROLE_LABELS[role]}</span></label><select id={`aic-${role}-source`} value={drafts[role].source} aria-invalid={unavailableSource || missingRoleSource || undefined} aria-describedby={sourceDescription} onChange={event => { updateDraft(role, 'source', event.target.value); if (fieldError?.target === 'roles') setFieldError(null) }}><option value="">Choose source</option>{sources.map(source => <option key={source.value} value={source.value}>{source.label}</option>)}</select></div><div className="aic-field"><label htmlFor={`aic-${role}-model`}>Model <span className="sr-only">for {ROLE_LABELS[role]}</span></label><select id={`aic-${role}-model`} value={drafts[role].model} disabled={!drafts[role].source || unavailableSource} aria-invalid={unavailableModel || missingRoleModel || undefined} aria-describedby={modelDescription} onChange={event => { updateDraft(role, 'model', event.target.value); if (fieldError?.target === 'roles') setFieldError(null) }}><option value="">Choose model</option>{retainedStaleModel && <option value={drafts[role].model} disabled>Saved model {drafts[role].model === '__builtin__' ? 'Built-in default' : drafts[role].model} · no longer available or compatible</option>}{options.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></div></div>
          })}
          {hasUnavailableSource && <p id="aic-source-repair" className="aic-field-error" role="status">One or more saved sources are no longer selectable. Choose an available source and model for every affected role.</p>}
          {hasUnavailableModel && <p id="aic-model-repair" className="aic-field-error" role="status">One or more saved model choices are no longer available or compatible. Choose a current compatible model for every affected role.</p>}
          <button className="aic-button" type="button" disabled={!canFillAll} onClick={fillAllRoles}>Use this model for every role</button>
          {fieldError && <p id="aic-config-error" className="aic-field-error" role="alert">{fieldError.message}</p>}
        </div>
          <DialogFooter><button className="aic-button" type="button" onClick={() => { setEditorOpen(false); onSeedDismiss?.() }}>Cancel</button><button className="aic-button" data-primary="true" type="button" disabled={!complete || mutationPending} onClick={saveConfiguration}>{mutationPending ? 'Working…' : 'Save configuration'}</button></DialogFooter>
      </DialogContent></Dialog>

      <Dialog open={duplicateTarget !== null} onOpenChange={open => { if (!open) { setDuplicateTarget(null); setDuplicateError('') } }}><DialogContent className="pp-root aic-dialog"><DialogHeader><DialogTitle>Duplicate configuration</DialogTitle><DialogDescription>Create an independent copy with a new name.</DialogDescription></DialogHeader><div className="aic-field"><label htmlFor="aic-duplicate-name">Configuration name</label><input id="aic-duplicate-name" value={duplicateName} onChange={event => { setDuplicateName(event.target.value); setDuplicateError('') }} aria-invalid={Boolean(duplicateError) || undefined} aria-describedby={duplicateError ? 'aic-duplicate-error' : undefined} /></div>{duplicateError && <p id="aic-duplicate-error" className="aic-field-error" role="alert">{duplicateError}</p>}<DialogFooter><button className="aic-button" type="button" onClick={() => setDuplicateTarget(null)}>Cancel</button><button className="aic-button" data-primary="true" type="button" disabled={!duplicateName.trim() || mutationPending} onClick={duplicateConfiguration}>Duplicate</button></DialogFooter></DialogContent></Dialog>

      <AlertDialog open={deleteTarget !== null} onOpenChange={open => { if (!open) setDeleteTarget(null) }}><AlertDialogContent className="pp-root aic-dialog"><AlertDialogHeader><AlertDialogTitle>Delete {deleteTarget?.name}?</AlertDialogTitle><AlertDialogDescription>{deleteSummary} No other configuration will be substituted.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel><AlertDialogAction disabled={mutationPending} onClick={confirmDelete}>Delete configuration</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
    </section>
  )
}
