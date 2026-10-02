import type { CliRunLimits, StartedCliProcess } from '../../src/lib/ai-console/cli/runner'
export function startCatalogProcess(options: {
  cliId: 'codex' | 'claude_code'; executable: string; args: readonly string[]; cwd: string;
  env: NodeJS.ProcessEnv; limits: CliRunLimits; signal?: AbortSignal;
  error?: (code: string) => Error; cleanup?: () => Promise<void>;
}): StartedCliProcess
