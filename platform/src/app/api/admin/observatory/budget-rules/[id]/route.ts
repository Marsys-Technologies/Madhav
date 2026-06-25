// GET    /api/admin/observatory/budget-rules/[id] — fetch a single rule
// PATCH  /api/admin/observatory/budget-rules/[id] — partial update
// DELETE /api/admin/observatory/budget-rules/[id] — soft-delete (active=false)
//
// Phase O — O.3 Budgets — single-rule CRUD.
// Authored by USTAD_S3_1_BUDGET_RULES_FRAMEWORK.

import { NextResponse } from 'next/server'
import { res } from '@/lib/errors'
import { guardObservatoryRoute } from '../../_guard'
import {
  getBudgetRuleById,
  patchBudgetRule,
  softDeleteBudgetRule,
  validateBudgetRulePatch,
} from '@/lib/observatory/budget/persist'

interface RouteContext {
  params: Promise<{ id: string }>
}

async function resolveId(context: RouteContext): Promise<string> {
  const { id } = await context.params
  return id
}

export async function GET(_request: Request, context: RouteContext) {
  const auth = await guardObservatoryRoute()
  if (auth instanceof NextResponse) return auth

  const id = await resolveId(context)
  try {
    const rule = await getBudgetRuleById(id)
    if (!rule) return res.notFound(`No budget rule with id ${id}.`)
    return NextResponse.json(rule)
  } catch (err) {
    console.error('[admin/observatory/budget-rules/[id]] GET failed', err)
    return res.internal('Failed to fetch budget rule.')
  }
}

export async function PATCH(request: Request, context: RouteContext) {
  const auth = await guardObservatoryRoute()
  if (auth instanceof NextResponse) return auth

  const id = await resolveId(context)
  let raw: unknown
  try {
    raw = await request.json()
  } catch {
    return res.badRequest('Request body must be valid JSON.')
  }
  const parsed = validateBudgetRulePatch(raw)
  if (!parsed.ok || !parsed.value) {
    return res.badRequest(parsed.message ?? 'Invalid patch.')
  }

  try {
    const rule = await patchBudgetRule(id, parsed.value)
    if (!rule) return res.notFound(`No budget rule with id ${id}.`)
    return NextResponse.json(rule)
  } catch (err) {
    console.error('[admin/observatory/budget-rules/[id]] PATCH failed', err)
    return res.internal('Failed to update budget rule.')
  }
}

export async function DELETE(_request: Request, context: RouteContext) {
  const auth = await guardObservatoryRoute()
  if (auth instanceof NextResponse) return auth

  const id = await resolveId(context)
  try {
    const found = await softDeleteBudgetRule(id)
    if (!found) return res.notFound(`No budget rule with id ${id}.`)
    return new NextResponse(null, { status: 204 })
  } catch (err) {
    console.error('[admin/observatory/budget-rules/[id]] DELETE failed', err)
    return res.internal('Failed to delete budget rule.')
  }
}
