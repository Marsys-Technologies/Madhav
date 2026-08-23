// FAIL fixture seed. `bg_seedonly` has no registry row (P-04). `bg_orphan` is
// deliberately ABSENT here as well as from the writer tree, so it is registry-only (P-03).
export const ASSETS = [
  {
    asset_id: 'bg_ok',
    layer: 'brahmagyan',
  },
  {
    asset_id: 'bg_dup',
    layer: 'brahmagyan',
  },
  {
    asset_id: 'zz_bad',
    layer: 'brahmagyan',
  },
  {
    asset_id: 'bg_seedonly',
    layer: 'brahmagyan',
  },
]
