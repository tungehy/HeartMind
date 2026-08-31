"use client";

import { useMemo, useState } from "react";
import type { GanttRow } from "@/lib/api";
import { STATE_LABELS } from "@/lib/api";

const MONTHS = ["一月","二月","三月","四月","五月","六月","七月","八月","九月","十月","十一月","十二月"];
const LEGEND = [
  { key: "warming", label: "关系升温", color: "#16a34a" },
  { key: "stable", label: "稳定发展", color: "#2563eb" },
  { key: "cooling", label: "感情降温", color: "#d97706" },
  { key: "coldwar", label: "冷战/踩雷", color: "#dc2626" },
  { key: "ended", label: "已结束", color: "#4b5563" },
];
// 以今天为基准动态计算范围，结束点留 7 天余量
function buildRanges() {
  const now = new Date();
  const end = new Date(now);
  end.setDate(end.getDate() + 7);
  const back = (months: number) => {
    const d = new Date(now);
    d.setMonth(d.getMonth() - months);
    return d;
  };
  return {
    "3m": { start: back(3), end, label: "3个月" },
    "6m": { start: back(6), end, label: "6个月" },
    ytd: { start: new Date(now.getFullYear(), 0, 1), end, label: "全部" },
  } as const;
}
// 事件类型 → 甘特状态色
const EVENT_STATE: Record<string, string> = {
  met: "stable", chat_import: "stable", date: "warming", warming: "warming",
  cooling: "cooling", conflict: "coldwar", turning_point: "coldwar",
  reconnect: "warming", end: "ended", stable: "stable",
};
const TODAY = new Date();

function pct(date: Date, start: Date, end: Date) {
  return ((date.getTime() - start.getTime()) / (end.getTime() - start.getTime())) * 100;
}
const clamp = (p: number) => Math.max(0, Math.min(100, p));

interface Bar { left: number; width: number; color: string; label: string; tip: string }

export default function Gantt({ rows, onSelect }: { rows: GanttRow[]; onSelect: (id: number) => void }) {
  const RANGES = useMemo(buildRanges, []);
  const [range, setRange] = useState<keyof typeof RANGES>("6m");
  const [tip, setTip] = useState<{ x: number; y: number; text: string } | null>(null);
  const { start, end } = RANGES[range];

  const months = useMemo(() => {
    const out: { label: string; left: number }[] = [];
    const m = new Date(start);
    while (m < end) {
      out.push({ label: MONTHS[m.getMonth()], left: pct(m, start, end) });
      m.setMonth(m.getMonth() + 1);
    }
    return out;
  }, [start, end]);

  const todayPct = pct(TODAY, start, end);

  function barsFor(row: GanttRow): Bar[] {
    const evs = [...row.events].sort((a, b) => a.time.localeCompare(b.time));
    const fmt = (d: Date) => `${d.getMonth() + 1}月${d.getDate()}日`;
    // 聊天真实时间跨度：以消息内容时间为准，而非导入/记录时刻
    const firstMsg = row.first_message ? new Date(row.first_message) : null;
    const lastMsg = row.last_message ? new Date(row.last_message) : null;

    // AI 时期分段（PeriodAgent：LLM 按聊天内容在趋势突变点切分）优先于单条主状态
    if (row.segments && row.segments.length > 0) {
      const bars: Bar[] = [];
      for (const s of row.segments) {
        const segStart = new Date(s.start + "T00:00:00");
        const segEnd = new Date(s.end + "T23:59:59");
        if (segEnd < start || segStart > end) continue;
        const l = clamp(pct(segStart < start ? start : segStart, start, end));
        const r = clamp(pct(segEnd > end ? end : segEnd, start, end));
        if (r - l <= 0.3) continue;
        bars.push({
          left: l, width: Math.max(r - l, 0.8), color: colorOf(s.state),
          label: STATE_LABELS[s.state] || s.state,
          tip: `${row.name} · ${fmt(segStart)}~${fmt(segEnd)} ${STATE_LABELS[s.state] || s.state}${s.summary ? "：" + s.summary : ""}`,
        });
      }
      if (bars.length) return bars;
    }

    if (firstMsg && lastMsg) {
      const l = clamp(pct(firstMsg < start ? start : firstMsg, start, end));
      const r = clamp(pct(lastMsg > end ? end : lastMsg, start, end));
      const bars: Bar[] = [{
        left: l, width: Math.max(r - l, 0.8), color: row.state_color,
        label: STATE_LABELS[row.state],
        tip: `${row.name} · ${fmt(firstMsg)} ~ ${fmt(lastMsg)} · ${row.message_count}条消息（${STATE_LABELS[row.state]}）`,
      }];
      // 主条之后的业务事件（约会/转折点/结束等）画为小标记段；met/chat_import 是系统记录时刻，不作分段依据
      for (const e of evs) {
        if (e.type === "met" || e.type === "chat_import") continue;
        const t = new Date(e.time);
        if (t <= lastMsg || t > end) continue;
        const state = EVENT_STATE[e.type] || row.state;
        bars.push({
          left: clamp(pct(t, start, end)), width: 0.9, color: colorOf(state),
          label: STATE_LABELS[state] || state,
          tip: `${row.name} · ${e.summary}（${fmt(t)}）`,
        });
      }
      return bars;
    }

    if (evs.length === 0) {
      // 无事件：用认识至今的一段当前状态
      return [{ left: 0, width: clamp(todayPct), color: row.state_color, label: STATE_LABELS[row.state], tip: `${row.name} · ${STATE_LABELS[row.state]}` }];
    }
    const bars: Bar[] = [];
    for (let i = 0; i < evs.length; i++) {
      const segStart = new Date(evs[i].time);
      const segEnd = i + 1 < evs.length ? new Date(evs[i + 1].time) : end;
      const state = EVENT_STATE[evs[i].type] || row.state;
      const left = clamp(pct(segStart, start, end));
      const right = clamp(pct(segEnd > end ? end : segEnd, start, end));
      const width = right - left;
      if (width <= 0.3) continue;
      bars.push({
        left, width, color: colorOf(state), label: STATE_LABELS[state] || state,
        tip: `${row.name} · ${evs[i].summary}（${STATE_LABELS[state] || state}）`,
      });
    }
    return bars;
  }

  function colorOf(state: string) {
    return LEGEND.find((l) => l.key === state)?.color || "#2563eb";
  }

  return (
    <div>
      <div className="flex items-center gap-2">
        <div className="mr-1 flex flex-wrap items-center gap-3.5">
          {LEGEND.map((l) => (
            <div key={l.key} className="flex items-center gap-1.5 text-[11.5px] text-ink-500">
              <span className="h-[11px] w-[11px] rounded" style={{ background: l.color }} />
              {l.label}
            </div>
          ))}
        </div>
        <div className="flex rounded-lg border border-line bg-bg p-0.5">
          {(Object.keys(RANGES) as (keyof typeof RANGES)[]).map((k) => (
            <button key={k} onClick={() => setRange(k)}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold ${range === k ? "bg-white text-blue-700 shadow-card" : "text-ink-500"}`}>
              {RANGES[k].label}
            </button>
          ))}
        </div>
      </div>

      <div className="relative mt-2 min-w-[640px] overflow-x-auto px-0 pb-2 pt-1">
        {/* 月份表头 */}
        <div className="relative ml-24 h-7 border-b border-line">
          {months.map((m, i) => (
            <div key={i} className="absolute top-0 text-[11.5px] font-semibold text-ink-400" style={{ left: `${m.left}%` }}>
              {m.label}
              <span className="absolute left-0 top-[22px] h-[9999px] w-px bg-line-2" />
            </div>
          ))}
        </div>
        {/* 行 */}
        {rows.map((row) => (
          <div key={row.person_id} className="relative flex h-[38px] items-center hover:bg-[#fafcff]">
            <div className="z-[3] flex w-24 shrink-0 items-center gap-2 text-[13px] font-semibold text-ink-700">
              <span className="grid h-[22px] w-[22px] shrink-0 place-items-center rounded-md text-[11px] font-bold text-white"
                style={{ background: row.state_color }}>
                {row.name[0]}
              </span>
              {row.name}
            </div>
            <div className="relative h-full flex-1">
              {barsFor(row).map((b, i) => (
                <div key={i}
                  className="absolute top-2 flex h-[22px] cursor-pointer items-center overflow-hidden rounded-md transition-all hover:brightness-95"
                  style={{ left: `${b.left}%`, width: `${b.width}%`, background: b.color, boxShadow: "inset 0 0 0 1px rgba(255,255,255,.35)" }}
                  onMouseMove={(e) => setTip({ x: e.clientX, y: e.clientY, text: b.tip })}
                  onMouseLeave={() => setTip(null)}
                  onClick={() => onSelect(row.person_id)}>
                  {b.width > 12 && <span className="whitespace-nowrap px-2 text-[10.5px] font-semibold text-white/95">{b.label}</span>}
                </div>
              ))}
            </div>
          </div>
        ))}
        {/* 今日线 */}
        {todayPct >= 0 && todayPct <= 100 && (
          <div className="pointer-events-none absolute bottom-1.5 top-[30px] w-0.5 bg-coldwar z-[4]"
            style={{ left: `calc(96px + (100% - 96px) * ${todayPct / 100})` }}>
            <span className="absolute -top-5 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-coldwar px-1.5 py-0.5 text-[10px] font-bold text-white">
              今天
            </span>
          </div>
        )}
      </div>

      {tip && (
        <div className="pointer-events-none fixed z-[100] max-w-[240px] rounded-lg bg-ink-900 px-3 py-2 text-xs leading-relaxed text-white shadow-card-lg"
          style={{ left: tip.x + 14, top: tip.y + 14 }}>
          {tip.text}
        </div>
      )}
    </div>
  );
}
