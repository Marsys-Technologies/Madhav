/**
 * roster.ts — D-4b permission-bridge lane (wave/D-4b/permission-bridge).
 *
 * The B-1 Grand Bakeoff's ACTIVE/narrowed contender roster: the 13
 * genuinely evaluable models today — `pratyantar_lord` (DR-10's classical
 * default, already real per model_interface.ts) + the 12 D-5 PERMISSION
 * standalone system-generators (permission_model.ts, this lane).
 *
 * `midpoint_triangle` and `transit_kernel` are DELIBERATELY excluded —
 * both remain `NotImplementedModelError` stubs (model_interface.ts) and
 * are registered as NOT-EVALUABLE coverage-gap rows in
 * MARSYS_DEFECT_GAP_REGISTER_v2_0.md (CR-… — see this lane's own PR), not
 * silently dropped and not deleted/deprecated from the doctrine's own
 * contender list.
 *
 * `hierarchical_ensemble` (ensemble_model.ts) is NOT in `ACTIVE_ROSTER` —
 * it is built FROM the roster (a 14th, derived contender), not a peer
 * member of it; see `activeRosterWithEnsemble` below for the combined
 * 14-model list a future B-1 scoring driver may want.
 */
import type { EventClass, TemporalCurveModel } from './model_interface'
import { pratyantarLordModel } from './model_interface'
import { allPermissionSystemModels, type PermissionModelOptions } from './permission_model'
import { hierarchicalEnsembleModel } from './ensemble_model'

/**
 * The 13 evaluable contenders. `eventClassSignificators` is
 * `pratyantar_lord`'s own required significator map (model_interface.ts's
 * existing signature — this function does not invent a new one, it is the
 * SAME parameter every prior caller of `pratyantarLordModel` already
 * supplies).
 */
export function buildActiveRoster(
  eventClassSignificators: Record<EventClass, Record<string, number>>,
  permissionOpts?: PermissionModelOptions
): TemporalCurveModel[] {
  return [pratyantarLordModel(eventClassSignificators), ...allPermissionSystemModels(permissionOpts)]
}

/** The 13-model roster plus the hierarchical ensemble built from it (14 total). */
export function buildActiveRosterWithEnsemble(
  eventClassSignificators: Record<EventClass, Record<string, number>>,
  permissionOpts?: PermissionModelOptions
): TemporalCurveModel[] {
  const roster = buildActiveRoster(eventClassSignificators, permissionOpts)
  return [...roster, hierarchicalEnsembleModel(roster)]
}

export const NOT_EVALUABLE_MODEL_IDS = ['midpoint_triangle', 'transit_kernel'] as const
