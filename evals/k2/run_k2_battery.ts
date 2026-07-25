#!/usr/bin/env tsx
/**
 * evals/k2/run_k2_battery.ts — Lane K2 orchestrator (Elevation Campaign v2.1, Stream γ).
 *
 * Ties every K2 sub-item together into ONE runnable pass over a captured sealed-harness
 * transcript, producing the consolidated grading envelope a standing-battery run would attach
 * to a scored answer:
 *
 *   1. consumption_grader.ts   — consumption_ratio, accounting_completeness, volunteered_findings
 *   2. auditor.ts              — the LAW-mandated two-pass audit (TWO_PASS_GRADING_LAW_v1_0.md)
 *   3. instrumentation_tracks.ts — experience + I1-I5/V1-V5/RE1-RE5 capture
 *   5. varga_depth_probe.ts    — domain-appropriate divisional-chart depth check
 *   6. classical_attribution_checker.ts — the 20-entry misattribution scan
 *
 * (Item 4, benchmark pairs, is a cross-transcript comparison — run separately via
 * benchmark_pairs_runner.ts once both members of a pair are captured. Item 7, EL-60a, is a
 * standing structural check on the tool itself, not a per-transcript grading dimension — run
 * separately via reading_notes_accretion_check.ts.)
 *
 * Usage:
 *   npx tsx evals/k2/run_k2_battery.ts <transcript.json> <domain> <chart_id> [--no-write]
 *   npx tsx evals/k2/run_k2_battery.ts --smoke   # runs the bundled fixture, no args needed
 */
import { existsSync, mkdirSync, writeFileSync } from 'fs'
import { join } from 'path'
import { REPO_ROOT, loadTranscript } from './transcript_utils.js'
import { gradeConsumption } from './consumption_grader.js'
import { runTwoPass } from './auditor.js'
import { captureInstrumentation } from './instrumentation_tracks.js'
import { probeVargaDepth } from './varga_depth_probe.js'
import { gradeClassicalAttributions } from './classical_attribution_checker.js'

export interface K2BatteryReport {
  artifact: 'K2_BATTERY_REPORT'
  version: '1.0'
  generated_at: string
  domain: string
  chart_id: string
  consumption: ReturnType<typeof gradeConsumption>
  two_pass_audit: Awaited<ReturnType<typeof runTwoPass>>
  instrumentation: ReturnType<typeof captureInstrumentation>
  varga_depth: ReturnType<typeof probeVargaDepth>
  classical_attributions: ReturnType<typeof gradeClassicalAttributions>
  headline: {
    consumption_ratio: number
    accounting_completeness_verdict: string
    volunteered_findings_count: number
    audit_overturn_rate: number
    varga_depth_score: number
    varga_d1_only: boolean
    classical_attribution_flags: number
    classical_attribution_trust_breaking: number
  }
}

export async function runK2Battery(
  transcriptPath: string,
  domain: string,
  chartId: string,
): Promise<K2BatteryReport> {
  const transcript = loadTranscript(transcriptPath)
  const finalAnswer = transcript.final_answer

  const consumption = gradeConsumption(domain, chartId, transcript, finalAnswer)
  const two_pass_audit = await runTwoPass(domain, chartId, transcript)
  const instrumentation = captureInstrumentation(transcript)
  const varga_depth = probeVargaDepth(finalAnswer, domain)
  const classical_attributions = gradeClassicalAttributions(finalAnswer)

  return {
    artifact: 'K2_BATTERY_REPORT',
    version: '1.0',
    generated_at: new Date().toISOString(),
    domain,
    chart_id: chartId,
    consumption,
    two_pass_audit,
    instrumentation,
    varga_depth,
    classical_attributions,
    headline: {
      consumption_ratio: consumption.consumption.consumption_ratio,
      accounting_completeness_verdict: consumption.accounting_completeness.verdict,
      volunteered_findings_count: consumption.volunteered_findings.volunteered_findings_count,
      audit_overturn_rate: two_pass_audit.audit_overturn_rate,
      varga_depth_score: varga_depth.depth_score,
      varga_d1_only: varga_depth.d1_only,
      classical_attribution_flags: classical_attributions.flag_count,
      classical_attribution_trust_breaking: classical_attributions.trust_breaking_count,
    },
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────────────────────

function isMain(): boolean {
  return process.argv[1] != null && import.meta.url === `file://${process.argv[1]}`
}

if (isMain()) {
  void (async () => {
    const args = process.argv.slice(2)
    let transcriptPath: string
    let domain: string
    let chartId: string

    if (args[0] === '--smoke') {
      transcriptPath = join(REPO_ROOT, 'evals/k2/__fixtures__/wealth_expert_smoke.transcript.json')
      domain = 'wealth'
      chartId = '482012f1-710e-4a25-994a-93821f5871aa'
      console.log('SMOKE MODE — running the bundled wealth_expert_smoke fixture.\n')
    } else {
      ;[transcriptPath, domain, chartId] = args
      if (!transcriptPath || !domain || !chartId) {
        console.error(
          'Usage: npx tsx evals/k2/run_k2_battery.ts <transcript.json> <domain> <chart_id> [--no-write]\n' +
            '       npx tsx evals/k2/run_k2_battery.ts --smoke',
        )
        process.exit(1)
      }
    }

    const report = await runK2Battery(transcriptPath, domain, chartId)

    console.log(JSON.stringify(report.headline, null, 2))
    console.log(`\n(full report has ${report.consumption.consumption.misses.length} consumption misses, ` +
      `${report.two_pass_audit.disagreement_ledger.length} audit disagreements, ` +
      `${report.instrumentation.investigation.ledger.leads_offered.length} leads offered — ` +
      `pass --full to print everything)`)

    if (args.includes('--full')) {
      console.log('\nFull report:')
      console.log(JSON.stringify(report, null, 2))
    }

    if (!args.includes('--no-write')) {
      const outDir = join(REPO_ROOT, 'evals/k2/battery_runs')
      if (!existsSync(outDir)) mkdirSync(outDir, { recursive: true })
      const chart8 = chartId.slice(0, 8)
      const ts = report.generated_at.replace(/[:.]/g, '-')
      const outPath = join(outDir, `${domain}_${chart8}_${ts}.json`)
      writeFileSync(outPath, JSON.stringify(report, null, 2))
      console.log(`\nK2 battery report written: ${outPath}`)
    }
  })()
}
