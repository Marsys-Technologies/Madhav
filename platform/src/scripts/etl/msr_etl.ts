import { getStorageClient } from '../../lib/storage/index'
import { parseMsrSignals } from './msr_parser'
import { loadMsrSignals } from './msr_loader'

async function main(): Promise<void> {
  try {
    const client = getStorageClient()

    // Step 1: Read MSR file
    const content = await client.readFile('025_HOLISTIC_SYNTHESIS/MSR_v5_0.md')

    // Step 2: Parse signals
    const signals = parseMsrSignals(content)
    console.log(`Parsed ${signals.length} signals`)

    // Step 3: Load signals into DB
    const result = await loadMsrSignals(signals)
    console.log(`Inserted ${result.inserted} signals into msr_signals`)

    process.exit(0)
  } catch (err) {
    console.error('ETL failed:', err)
    process.exit(1)
  }
}

main()
