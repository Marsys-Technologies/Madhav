'use client'

import { useMemo, useState } from 'react'
import { AlertCircle, Copy, Plus } from 'lucide-react'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { AiChoiceRadio } from './AiChoiceRadio'
import {
  AI_ROLES, PROVIDER_LABELS, ROLE_LABELS, choicesEqual,
  type AiChoice, type AiConsoleStateDto, type AiRole, type CliCardDto, type ConfigurationDto,
  type ConsoleMutation, type RoleTarget,
} from './types'

interface Props {
  state?: AiConsoleStateDto
  clis: CliCardDto[]
  loading: boolean
  mutationPending: boolean
  mutate: ConsoleMutation
  onSelectDefault: (choice: AiChoice) => Promise<unknown>
}

interface RoleDraft { source: string; model: string }
type Drafts = Record<AiRole, RoleDraft>
const EMPTY_DRAFTS = (): Drafts => Object.fromEntries(AI_ROLES.map(role => [role, { source: '', model: '' }])) as Drafts
const encodeModel = (value: string | null) => value === null ? '__builtin__' : value

function sourceFor(target: RoleTarget) {
  return target.kind === 'provider_model' ? `provider:${target.connectionId}` : `cli:${target.cliId}`
}

function configurationUsable(configuration: ConfigurationDto, state: AiConsoleStateDto | undefined, clis: CliCardDto[]) {
  if (configuration.deletedAt) return false
  return AI_ROLES.every(role => {
    const target = configuration.roles[role]
    if (target.kind === 'provider_model') {
      const connection = state?.connections.find(item => item.id === target.connectionId)
      const model = state?.models.find(item => item.connectionId === target.connectionId && item.modelId === target.modelId)
      return connection?.validationState === 'validated' && !connection.deletedAt && model?.available === true && model.compatibleRoles.includes(role)
    }
    const cli = clis.find(item => item.cliId === target.cliId)
    return cli?.state === 'reachable' && cli.models.some(model => model.modelId === target.modelId && model.compatibleRoles.includes(role))
  })
}

export function CustomConfigurationsSection({ state, clis, loading, mutationPending, mutate, onSelectDefault }: Props) {
  const [editorOpen, setEditorOpen] = useState(false)
  const [editing, setEditing] = useState<ConfigurationDto | null>(null)
  const [name, setName] = useState('')
  const [drafts, setDrafts] = useState<Drafts>(EMPTY_DRAFTS)
  const [fieldError, setFieldError] = useState('')
  const [duplicateTarget, setDuplicateTarget] = useState<ConfigurationDto | null>(null)
  const [duplicateName, setDuplicateName] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<ConfigurationDto | null>(null)
  const [deleteSummary, setDeleteSummary] = useState('')
  const configurationDefault = state?.defaultChoice?.kind === 'custom_configuration' ? state.defaultChoice : null

  const configurations = useMemo(() => (state?.configurations ?? []).filter(configuration =>
    !configuration.deletedAt || configurationDefault?.configurationId === configuration.id), [state, configurationDefault])

  const sources = useMemo(() => {
    const providerSources = (state?.connections ?? []).filter(connection => !connection.deletedAt && connection.validationState === 'validated')
      .map(connection => ({ value: `provider:${connection.id}`, label: `${connection.name} · ${PROVIDER_LABELS[connection.providerId]}` }))
    const cliSources = clis.filter(cli => cli.state === 'reachable')
      .map(cli => ({ value: `cli:${cli.cliId}`, label: cli.productName }))
    return [...providerSources, ...cliSources]
  }, [state, clis])

  function modelOptions(source: string, role: AiRole) {
    const [kind, id] = source.split(':', 2)
    if (kind === 'provider') return (state?.models ?? []).filter(model => model.connectionId === id && model.available && model.compatibleRoles.includes(role))
      .map(model => ({ value: encodeModel(model.modelId), label: model.displayName, target: { kind: 'provider_model' as const, connectionId: id, modelId: model.modelId } }))
    if (kind === 'cli') {
      const cli = clis.find(item => item.cliId === id)
      if (cli?.state !== 'reachable') return []
      return cli.models.filter(model => model.compatibleRoles.includes(role)).map(model => ({ value: encodeModel(model.modelId), label: model.displayName,
        target: { kind: 'local_cli' as const, cliId: cli.cliId, modelId: model.modelId } }))
    }
    return []
  }

  function openNew() {
    setEditing(null); setName(''); setDrafts(EMPTY_DRAFTS()); setFieldError(''); setEditorOpen(true)
  }

  function openEdit(configuration: ConfigurationDto) {
    const next = EMPTY_DRAFTS()
    for (const role of AI_ROLES) next[role] = { source: sourceFor(configuration.roles[role]), model: encodeModel(configuration.roles[role].modelId) }
    setEditing(configuration); setName(configuration.name); setDrafts(next); setFieldError(''); setEditorOpen(true)
  }

  function updateDraft(role: AiRole, field: keyof RoleDraft, value: string) {
    setDrafts(current => ({ ...current, [role]: field === 'source' ? { source: value, model: '' } : { ...current[role], model: value } }))
  }

  function targetFor(role: AiRole): RoleTarget | null {
    const draft = drafts[role]
    return modelOptions(draft.source, role).find(option => option.value === draft.model)?.target ?? null
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
  const fillAllTarget = targetFor('synthesizer')
  const canFillAll = fillAllTarget !== null && AI_ROLES.every(role => modelOptions(drafts.synthesizer.source, role).some(option => option.value === drafts.synthesizer.model))

  function fillAllRoles() {
    if (!canFillAll) return
    setDrafts(Object.fromEntries(AI_ROLES.map(role => [role, { ...drafts.synthesizer }])) as Drafts)
  }

  async function saveConfiguration() {
    if (!complete) { setFieldError('Name the configuration and choose a compatible source and model for all four roles.'); return }
    const roles = Object.fromEntries(AI_ROLES.map(role => [role, targetFor(role)])) as Record<AiRole, RoleTarget>
    try {
      await mutate(editing ? `/api/ai-console/configurations/${editing.id}` : '/api/ai-console/configurations', {
        method: editing ? 'PATCH' : 'POST',
        body: JSON.stringify(editing ? { name: name.trim(), expectedVersion: editing.version, roles } : { name: name.trim(), roles }),
      }, editing ? 'Configuration updated.' : 'Configuration created.')
      setEditorOpen(false)
    } catch (error) { setFieldError(error instanceof Error ? error.message : 'The request could not be completed safely.') }
  }

  async function duplicateConfiguration() {
    if (!duplicateTarget || !duplicateName.trim()) return
    try {
      await mutate('/api/ai-console/configurations', { method: 'POST', body: JSON.stringify({ name: duplicateName.trim(), duplicateFrom: duplicateTarget.id }) }, 'Configuration duplicated.')
      setDuplicateTarget(null)
    } catch (error) { setFieldError(error instanceof Error ? error.message : 'The request could not be completed safely.') }
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

  const defaultMissing = configurationDefault !== null
    && !configurations.some(configuration => configuration.id === configurationDefault.configurationId)

  return (
    <section className="aic-section" aria-labelledby="aic-config-heading">
      <div className="aic-section-head"><div><h2 id="aic-config-heading">Custom configurations</h2><p className="aic-section-copy">Name a complete routing configuration and choose an exact validated model for each of Madhav’s four roles.</p></div><button className="aic-button" data-primary="true" type="button" onClick={openNew}><Plus aria-hidden="true" className="inline size-4" /> New configuration</button></div>
      {defaultMissing && configurationDefault && <div className="aic-broken"><strong>Broken default.</strong> Configuration {configurationDefault.configurationId} is no longer available. Choose another default.<div className="aic-model-row" data-default="true"><span className="aic-model-id">Unavailable configuration</span><AiChoiceRadio choice={configurationDefault} checked disabled unavailable label={configurationDefault.configurationId} onSelect={onSelectDefault} /></div></div>}
      {loading ? <div className="aic-empty">Loading custom configurations…</div> : configurations.length === 0 ? <div className="aic-empty">No custom configurations yet. Create one when you want different models to handle different roles.</div> : (
        <div className="aic-grid">{configurations.map(configuration => {
          const usable = configurationUsable(configuration, state, clis)
          const choice = { kind: 'custom_configuration' as const, configurationId: configuration.id }
          const checked = choicesEqual(state?.defaultChoice ?? null, choice)
          return <article className="aic-card" key={configuration.id}>
            <div className="aic-card-head">
              <div className="aic-card-title-row"><div><span className="aic-provider-name">Configuration · v{configuration.version}</span><h3>{configuration.name}</h3></div>{!usable && <span className="aic-status"><AlertCircle aria-hidden="true" />Needs repair</span>}</div>
              <div className="aic-role-grid">{AI_ROLES.map(role => <div className="aic-role-row" key={role}><span className="aic-role-label">{ROLE_LABELS[role]}</span><span className="aic-model-id">{targetLabel(configuration.roles[role])}</span></div>)}</div>
              {!configuration.deletedAt && <div className="aic-actions"><button className="aic-button" type="button" onClick={() => openEdit(configuration)}>Edit</button><button className="aic-button" type="button" onClick={() => { setDuplicateTarget(configuration); setDuplicateName(`${configuration.name} copy`); setFieldError('') }}><Copy aria-hidden="true" className="inline size-3" /> Duplicate</button><button className="aic-button" data-danger="true" type="button" onClick={() => previewDelete(configuration)}>Delete</button></div>}
            </div>
            <div className="aic-model-list"><div className="aic-model-row" data-default={checked}><div><span className="aic-model-name">Use this configuration</span><span className="aic-model-id">{usable ? 'All four roles are currently available' : 'One or more exact role choices are unavailable'}</span></div><AiChoiceRadio choice={choice} checked={checked} disabled={!usable || mutationPending} unavailable={checked && !usable} label={configuration.name} onSelect={onSelectDefault} /></div></div>
          </article>
        })}</div>
      )}

      <Dialog open={editorOpen} onOpenChange={setEditorOpen}><DialogContent className="aic-dialog">
        <DialogHeader><DialogTitle>{editing ? 'Edit custom configuration' : 'New custom configuration'}</DialogTitle><DialogDescription>Choose a source first, then one compatible model for each role. Configurations save only when all four roles are complete.</DialogDescription></DialogHeader>
        <div className="aic-form">
          <div className="aic-field"><label htmlFor="aic-config-name">Configuration name</label><input id="aic-config-name" value={name} onChange={event => setName(event.target.value)} aria-invalid={Boolean(fieldError) || undefined} aria-describedby={fieldError ? 'aic-config-error' : undefined} /></div>
          {AI_ROLES.map(role => <div className="aic-editor-role" role="group" aria-labelledby={`aic-${role}-label`} key={role}><span id={`aic-${role}-label`}>{ROLE_LABELS[role]}</span><div className="aic-field"><label htmlFor={`aic-${role}-source`}>Source <span className="sr-only">for {ROLE_LABELS[role]}</span></label><select id={`aic-${role}-source`} value={drafts[role].source} aria-invalid={Boolean(fieldError) && !drafts[role].source || undefined} aria-describedby={fieldError ? 'aic-config-error' : undefined} onChange={event => updateDraft(role, 'source', event.target.value)}><option value="">Choose source</option>{sources.map(source => <option key={source.value} value={source.value}>{source.label}</option>)}</select></div><div className="aic-field"><label htmlFor={`aic-${role}-model`}>Model <span className="sr-only">for {ROLE_LABELS[role]}</span></label><select id={`aic-${role}-model`} value={drafts[role].model} disabled={!drafts[role].source} aria-invalid={Boolean(fieldError) && !drafts[role].model || undefined} aria-describedby={fieldError ? 'aic-config-error' : undefined} onChange={event => updateDraft(role, 'model', event.target.value)}><option value="">Choose model</option>{modelOptions(drafts[role].source, role).map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></div></div>)}
          <button className="aic-button" type="button" disabled={!canFillAll} onClick={fillAllRoles}>Use this model for every role</button>
          {fieldError && <p id="aic-config-error" className="aic-field-error" role="alert">{fieldError}</p>}
        </div>
        <DialogFooter><button className="aic-button" type="button" onClick={() => setEditorOpen(false)}>Cancel</button><button className="aic-button" data-primary="true" type="button" disabled={!complete || mutationPending} onClick={saveConfiguration}>{mutationPending ? 'Working…' : 'Save configuration'}</button></DialogFooter>
      </DialogContent></Dialog>

      <Dialog open={duplicateTarget !== null} onOpenChange={open => { if (!open) setDuplicateTarget(null) }}><DialogContent className="aic-dialog"><DialogHeader><DialogTitle>Duplicate configuration</DialogTitle><DialogDescription>Create an independent copy with a new name.</DialogDescription></DialogHeader><div className="aic-field"><label htmlFor="aic-duplicate-name">Configuration name</label><input id="aic-duplicate-name" value={duplicateName} onChange={event => setDuplicateName(event.target.value)} /></div>{fieldError && <p className="aic-field-error" role="alert">{fieldError}</p>}<DialogFooter><button className="aic-button" type="button" onClick={() => setDuplicateTarget(null)}>Cancel</button><button className="aic-button" data-primary="true" type="button" disabled={!duplicateName.trim() || mutationPending} onClick={duplicateConfiguration}>Duplicate</button></DialogFooter></DialogContent></Dialog>

      <AlertDialog open={deleteTarget !== null} onOpenChange={open => { if (!open) setDeleteTarget(null) }}><AlertDialogContent className="aic-dialog"><AlertDialogHeader><AlertDialogTitle>Delete {deleteTarget?.name}?</AlertDialogTitle><AlertDialogDescription>{deleteSummary} No other configuration will be substituted.</AlertDialogDescription></AlertDialogHeader><AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel><AlertDialogAction disabled={mutationPending} onClick={confirmDelete}>Delete configuration</AlertDialogAction></AlertDialogFooter></AlertDialogContent></AlertDialog>
    </section>
  )
}
