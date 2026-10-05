import type { CSSProperties, ReactNode } from "react";
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
const GRAHAS = [
  "Moon",
  "Mars",
  "Mercury",
  "Jupiter",
  "Venus",
  "Saturn",
  "Rahu",
  "Ketu",
];
export function EntryShell({
  name,
  children,
}: {
  name: PageName;
  children: ReactNode;
}) {
  return (
    <main className="j1 j1-entry">
      <div className="j1-cosmos" aria-hidden="true">
        {Array.from({ length: 26 }, (_, i) => (
          <i
            key={i}
            className="j1-star"
            style={{
              left: `${((i * 9301 + 49297) % 233280) / 2332.8}%`,
              top: `${(((i + 3) * 7919 + 104729) % 233280) / 2332.8}%`,
              animationDelay: `-${i % 6}s`,
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
          {GRAHAS.map((g, i) => (
            <div
              key={g}
              data-graha={g}
              className={`j1-orbit j1-orbit-${i}`}
              style={
                {
                  "--orbit-size": `${340 + i * 125}px`,
                  "--orbit-time": `${85 + i * 43}s`,
                  "--orbit-delay": `-${i * 18}s`,
                } as CSSProperties
              }
            >
              <i />
            </div>
          ))}
          {/* Supplied master medallion serves as Sūrya; never recoloured or rotated. */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            className="j1-sun"
            src="/brand/marsys-logo-256.png"
            alt=""
            width="128"
            height="128"
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
