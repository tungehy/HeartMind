"use client";

const DIMS = ["沟通舒适度", "共同兴趣", "价值观契合", "情感互动", "未来潜力", "聊天质量"];

export default function Radar({ values, size = 220 }: { values: number[]; size?: number }) {
  const cx = size / 2;
  const cy = size / 2 - 4;
  const r = size * 0.28;
  const n = DIMS.length;
  const pt = (i: number, frac: number): [number, number] => {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
    return [cx + Math.cos(a) * r * frac, cy + Math.sin(a) * r * frac];
  };
  const poly = (f: number) => DIMS.map((_, i) => pt(i, f).join(",")).join(" ");
  const dataPts = values
    .map((v, i) => pt(i, Math.max(0, Math.min(100, v)) / 100).join(","))
    .join(" ");

  return (
    <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} role="img" aria-label="关系雷达图">
      {[0.25, 0.5, 0.75, 1].map((f) => (
        <polygon key={f} points={poly(f)} fill="none" stroke="#e5eaf1" strokeWidth="1" />
      ))}
      {DIMS.map((_, i) => {
        const [x, y] = pt(i, 1);
        return <line key={i} x1={cx} y1={cy} x2={x} y2={y} stroke="#eef2f7" strokeWidth="1" />;
      })}
      <polygon points={dataPts} fill="rgba(37,99,235,.16)" stroke="#2563eb" strokeWidth="2" strokeLinejoin="round" />
      {values.map((v, i) => {
        const [x, y] = pt(i, Math.max(0, Math.min(100, v)) / 100);
        return <circle key={i} cx={x} cy={y} r="2.5" fill="#2563eb" />;
      })}
      {DIMS.map((d, i) => {
        const [x, y] = pt(i, 1.28);
        const anchor = x < cx - 6 ? "end" : x > cx + 6 ? "start" : "middle";
        const dy = y < cy - 6 ? -1 : y > cy + 6 ? 9 : 3;
        return (
          <text key={d} x={x} y={y + dy} textAnchor={anchor} fontSize="9.5" fill="#94a3b8">
            {d}
          </text>
        );
      })}
    </svg>
  );
}
