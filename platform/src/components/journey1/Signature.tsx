import { useId } from "react";

// Signature 12: the exact selected Marck Script lettering, emboss and feather geometry.
// Ported from the reviewed Claude shared wordmark, separate from the unaltered Marsys mark.
export function Signature({ height = 44 }: { height?: number }) {
  const id = useId().replace(/:/g, "");
  const gl = `gold-${id}`;
  const emb = `emboss-${id}`;
  const P = [244, 146, 272, 149, 304, 149, 334, 144];
  const b = (t: number) => {
    const u = 1 - t;
    return [
      u * u * u * P[0] +
        3 * u * u * t * P[2] +
        3 * u * t * t * P[4] +
        t * t * t * P[6],
      u * u * u * P[1] +
        3 * u * u * t * P[3] +
        3 * u * t * t * P[5] +
        t * t * t * P[7],
    ];
  };
  const derivative = (t: number) => {
    const u = 1 - t;
    return [
      3 * u * u * (P[2] - P[0]) +
        6 * u * t * (P[4] - P[2]) +
        3 * t * t * (P[6] - P[4]),
      3 * u * u * (P[3] - P[1]) +
        6 * u * t * (P[5] - P[3]) +
        3 * t * t * (P[7] - P[5]),
    ];
  };
  const barbs = Array.from({ length: 22 }, (_, i) => {
    const t = 0.08 + (0.76 * i) / 21;
    const [x, y] = b(t);
    const [tx, ty] = derivative(t);
    const L = Math.hypot(tx, ty);
    const ux = tx / L,
      uy = ty / L;
    const profile = Math.sin(Math.PI * Math.pow((t - 0.08) / 0.76, 0.8));
    const len = 12 * (0.35 + 0.65 * profile);
    const wob = (((i * 7919) % 13) - 6) / 40;
    return [1, -1].map((s) => {
      const bx = -uy * s + ux * 0.6,
        by = ux * s + uy * 0.6,
        B = Math.hypot(bx, by);
      return (
        <path
          key={`${i}-${s}`}
          d={`M${x.toFixed(1)} ${y.toFixed(1)} Q${(x + (bx / B) * len * 0.5 + ux * len * 0.12).toFixed(1)} ${(y + (by / B) * len * 0.5 + uy * len * 0.12).toFixed(1)} ${(x + (bx / B) * len * (1 + wob)).toFixed(1)} ${(y + (by / B) * len * (1 + wob)).toFixed(1)}`}
          stroke={t > 0.62 ? "#5FA37A" : "#D2A23C"}
          strokeWidth=".85"
          opacity={(0.55 + 0.45 * profile).toFixed(3)}
        />
      );
    });
  });
  const [ex, ey] = b(0.91);
  const [tx, ty] = derivative(0.91);
  return (
    <svg
      viewBox="186 56 248 108"
      role="img"
      aria-label="Madhav"
      focusable="false"
      style={{ height, width: "auto", display: "block", overflow: "visible" }}
    >
      <defs>
        <linearGradient id={gl} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#F6DC8C" />
          <stop offset=".45" stopColor="#D2A23C" />
          <stop offset=".72" stopColor="#A87C2A" />
          <stop offset="1" stopColor="#E7C062" />
        </linearGradient>
        <filter id={emb} x="-10%" y="-20%" width="120%" height="140%">
          <feGaussianBlur in="SourceAlpha" stdDeviation=".6" result="b" />
          <feOffset in="b" dy="1.2" result="o" />
          <feFlood floodColor="#000" floodOpacity=".7" />
          <feComposite in2="o" operator="in" result="sh" />
          <feSpecularLighting
            in="b"
            surfaceScale="2.2"
            specularConstant=".9"
            specularExponent="18"
            lightingColor="#FFF4D0"
            result="sp"
          >
            <fePointLight x="180" y="-40" z="160" />
          </feSpecularLighting>
          <feComposite in="sp" in2="SourceAlpha" operator="in" result="sp2" />
          <feMerge>
            <feMergeNode in="sh" />
            <feMergeNode in="SourceGraphic" />
            <feMergeNode in="sp2" />
          </feMerge>
        </filter>
      </defs>
      <g filter={`url(#${emb})`}>
        <text
          x="190"
          y="128"
          fontFamily="'Marck Script', cursive"
          fontSize="84"
          letterSpacing="2"
          textLength="240"
          lengthAdjust="spacingAndGlyphs"
          fill={`url(#${gl})`}
          stroke="#8A5E12"
          strokeWidth=".35"
        >
          Madhav
        </text>
      </g>
      <g fill="none" strokeLinecap="round" filter={`url(#${emb})`}>
        <path
          d="M244 146 C272 149 304 149 334 144"
          stroke="#E7C062"
          strokeWidth="1.3"
        />
        {barbs}
        <g
          transform={`translate(${ex.toFixed(1)} ${ey.toFixed(1)}) rotate(${((Math.atan2(ty, tx) * 180) / Math.PI - 90).toFixed(1)})`}
          stroke="none"
        >
          <ellipse rx="8" ry="11" fill="#E7C062" opacity=".9" />
          <ellipse cy=".88" rx="5.76" ry="7.92" fill="#4E9A98" />
          <ellipse cy="1.76" rx="3.36" ry="5.06" fill="#5B7FB5" />
          <ellipse cy="2.42" rx="1.44" ry="2.42" fill="#1A1206" />
        </g>
      </g>
    </svg>
  );
}
