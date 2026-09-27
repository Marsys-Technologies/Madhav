/**
 * AI choice replay discovery.
 *
 * The standalone replay server does not mount the production React surface.
 * Keep the intended browser checks discoverable, but skip them truthfully
 * until the authenticated production surface is available to this harness.
 */
import { test } from '@playwright/test'

test.describe('AI choice — composer geometry and choreography', () => {
  test('keeps AI → Depth → Length and the exact three-row internal-scroll composer', async () => {
    test.skip(true, 'Production Paripraśna composer is not mounted by the standalone replay harness.')
  })

  test('retains the grouped desktop/mobile picker and keyboard dismissal contract', async () => {
    test.skip(true, 'Production AI picker is not mounted by the standalone replay harness.')
  })
})
