import type { WaveProgressCount } from '@/lib/nirmana-elevation/projection'

export function WaveProgressBar({ waveProgress }: { waveProgress: WaveProgressCount[] }) {
  return <ol aria-label="Programme sub-wave progress" className="grid grid-cols-6 gap-1.5">
    {waveProgress.map((wave) => {
      const complete = wave.required > 0 && wave.earned === wave.required
      const empty = wave.required === 0
      return <li key={wave.wave_id} className={`rounded-md border px-1.5 py-1 text-center text-[10px] ${
        complete ? 'border-brand-ok/60 bg-brand-ok/10 text-brand-ok'
          : empty ? 'border-brand-border text-brand-text-3'
            : 'border-brand-gold-1/50 text-brand-gold-2'
      }`}>
        <span className="block font-semibold">{wave.wave_id}</span>
        <span className="block">{wave.label}</span>
        <span className="mt-0.5 block font-mono">{wave.earned}/{wave.required}</span>
      </li>
    })}
  </ol>
}
