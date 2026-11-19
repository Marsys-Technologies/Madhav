import type { CSSProperties, ReactNode } from "react";
import Image from "next/image";
import styles from "./EntryShell.module.css";
import { Signature } from "./Signature";
import { PageTitle, TitleToggle, type PageName } from "./Titles";
const NAKSHATRAS = [
  "Aśv",
  "Bha",
  "Kṛt",
  "Roh",
  "Mṛg",
  "Ārd",
  "Pun",
  "Puṣ",
  "Āśl",
  "Mag",
  "PPh",
  "UPh",
  "Has",
  "Cit",
  "Svā",
  "Viś",
  "Anu",
  "Jye",
  "Mūl",
  "PĀṣ",
  "UĀṣ",
  "Śra",
  "Dha",
  "Śat",
  "PBh",
  "UBh",
  "Rev",
];
const GRAHAS: ReadonlyArray<{
  name: string;
  diameter: number;
  duration: number;
  elapsed: number;
  size: number;
  reverse?: boolean;
}> = [
  { name: "Moon", diameter: 150, duration: 110, elapsed: 0, size: 11 },
  { name: "Mercury", diameter: 230, duration: 150, elapsed: 40, size: 7, reverse: true },
  { name: "Venus", diameter: 310, duration: 190, elapsed: 90, size: 10 },
  { name: "Mars", diameter: 390, duration: 240, elapsed: 20, size: 8, reverse: true },
  { name: "Jupiter", diameter: 480, duration: 300, elapsed: 150, size: 13 },
  { name: "Saturn", diameter: 580, duration: 380, elapsed: 260, size: 10 },
  { name: "Rahu", diameter: 680, duration: 460, elapsed: 0, size: 9, reverse: true },
  { name: "Ketu", diameter: 680, duration: 460, elapsed: 230, size: 9, reverse: true },
];
export function EntryShell({
  name,
  children,
}: {
  name: PageName;
  children: ReactNode;
}) {
  return (
    <main className={`j1 j1-entry ${styles.folio}`} data-entry-page={name}>
      <div className="j1-cosmos" aria-hidden="true">
        {Array.from({ length: 26 }, (_, i) => (
          <i
            key={i}
            className="j1-star"
            style={{
              left: `${((i * 9301 + 49297) % 233280) / 2332.8}%`,
              top: `${(((i + 3) * 7919 + 104729) % 233280) / 2332.8}%`,
              animationDuration: `${3 + (i % 5)}s`,
              animationDelay: `-${((i * 17) % 60) / 10}s`,
            }}
          />
        ))}
        <div className="j1-universe">
          <div className="j1-nakshatras">
            {NAKSHATRAS.map((n, i) => (
              <span
                key={n}
                style={{ transform: `rotate(${(i * 360) / 27}deg)` }}
              >
                <b>{n}</b>
              </span>
            ))}
          </div>
          <div className="j1-rashis">
            {Array.from({ length: 12 }, (_, i) => (
              <i key={i} style={{ transform: `rotate(${i * 30}deg)` }} />
            ))}
          </div>
          {GRAHAS.map(({ name, diameter, duration, elapsed, size, reverse }) => {
            const orbit = Math.round(diameter * 1.45);
            const turn = reverse ? -360 : 360;
            return (
              <div
                key={name}
                data-graha={name}
                className="j1-orbit"
                style={
                  {
                    "--orbit-size": `clamp(${Math.round(orbit * 0.42)}px, ${(orbit / 9).toFixed(2)}vmin, ${orbit}px)`,
                    "--orbit-time": `${duration}s`,
                    "--orbit-turn": `${turn}deg`,
                    "--orbit-start": `${((elapsed / duration) * turn).toFixed(2)}deg`,
                    "--graha-size": `${size}px`,
                  } as CSSProperties
                }
              >
                <i />
              </div>
            );
          })}
          <div className="j1-corona" />
          {/* The supplied master medallion serves as Sūrya. */}
          <Image
            className="j1-sun"
            src="/brand/logo.png"
            alt=""
            width={128}
            height={128}
            sizes="(max-width: 767px) 84px, 128px"
            loading="eager"
          />
        </div>
        <i className="j1-comet" />
      </div>
      <div className="j1-entry-column">
        <div className="j1-entry-brand">
          <Signature height={108} />
          <p className="j1-descriptor">Marsys Jyotish Intelligence System</p>
          <PageTitle name={name} />
        </div>
        <div className="j1-entry-card">{children}</div>
        <footer>
          <TitleToggle />
          <span>
            © {new Date().getFullYear()} Marsys Jyotish Intelligence System
          </span>
        </footer>
      </div>
    </main>
  );
}
