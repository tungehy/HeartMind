"use client";

import type { Card } from "@/lib/api";
import { STATE_COLORS, STATE_LABELS } from "@/lib/api";
import Radar from "./Radar";

const TAG_PALETTE = [
  ["#dbeafe", "#1d4ed8"], ["#dcfce7", "#15803d"], ["#fef3c7", "#b45309"],
  ["#fce7f3", "#be185d"], ["#ede9fe", "#6d28d9"], ["#cffafe", "#0e7490"],
];

function scoreColor(s: number) {
  return s >= 90 ? "#16a34a" : s >= 80 ? "#2563eb" : s >= 70 ? "#d97706" : "#dc2626";
}
const RANK_CLS = [
  "bg-gradient-to-br from-amber-200 to-amber-500 text-amber-900",
  "bg-gradient-to-br from-gray-200 to-gray-400 text-gray-800",
  "bg-gradient-to-br from-orange-200 to-orange-400 text-orange-900",
];

export default function PersonCard({ card, rank, onOpen, onDelete }: { card: Card; rank: number; onOpen: () => void; onDelete?: () => void }) {
  const sc = STATE_COLORS[card.state] || "#2563eb";
  const rankCls = rank <= 3 ? RANK_CLS[rank - 1] : "bg-line-2 text-ink-500";
  const radar = card.radar && card.radar.length === 6 ? card.radar : [50, 50, 50, 50, 50, 50];
  return (
    <div onClick={onOpen}
      className="group relative flex cursor-pointer flex-col gap-3.5 rounded-2xl border border-line bg-white p-[18px] shadow-card transition-all hover:-translate-y-0.5 hover:border-[#dce6f5] hover:shadow-card-lg">
      <span className={`absolute right-3.5 top-3.5 rounded-full px-2.5 py-0.5 text-[11px] font-extrabold tracking-wide ${rankCls}`}>
        NO.{rank}
      </span>
      {onDelete && (
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          title="删除该对象及其数据"
          className="absolute left-3.5 top-3.5 z-[5] grid h-6 w-6 place-items-center rounded-md text-ink-300 opacity-0 transition-all hover:bg-red-50 hover:text-red-500 group-hover:opacity-100">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
            <path d="M3 6h18M8 6V4a1 1 0 011-1h6a1 1 0 011 1v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14zM10 11v6M14 11v6" />
          </svg>
        </button>
      )}

      <div className="flex items-center gap-3">
        <div className="grid h-[52px] w-[52px] shrink-0 place-items-center rounded-xl text-xl font-bold text-white"
          style={{ background: `linear-gradient(135deg, ${sc}, ${sc}cc)` }}>
          {card.name[0]}
        </div>
        <div>
          <div className="text-base font-bold">{card.name}</div>
          <div className="mt-0.5 text-xs text-ink-400">
            {card.age ? `${card.age}岁` : "年龄未知"} · {card.city || "城市未知"}
          </div>
        </div>
      </div>

      <div className="flex items-end justify-between gap-3">
        <div>
          <div className="text-[40px] font-extrabold leading-none tracking-tight" style={{ color: scoreColor(card.score) }}>
            {Math.round(card.score)}<span className="ml-0.5 text-[15px] font-semibold text-ink-400">分</span>
          </div>
          <div className="mt-1 text-[11px] text-ink-400">AI 综合关系评分</div>
        </div>
        <div className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold"
          style={{ background: `${sc}1a`, color: sc }}>
          <span className="h-2 w-2 rounded-full" style={{ background: sc }} />
          {STATE_LABELS[card.state] || card.state}
        </div>
      </div>

      <div className="flex justify-center">
        <Radar values={radar} size={210} />
      </div>

      {card.tags.length > 0 && (
        <div>
          <div className="mb-2 text-[11px] font-bold tracking-wide text-ink-400">兴趣标签</div>
          <div className="flex flex-wrap gap-1.5">
            {card.tags.map((t, i) => {
              const [bg, fg] = TAG_PALETTE[i % TAG_PALETTE.length];
              return (
                <span key={t} className="rounded-full px-2.5 py-1 text-[11.5px] font-medium" style={{ background: bg, color: fg }}>
                  {t}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {card.memories.length > 0 && (
        <div>
          <div className="mb-2 text-[11px] font-bold tracking-wide text-ink-400">AI 记忆摘要</div>
          <div className="flex flex-col gap-1.5">
            {card.memories.slice(0, 3).map((m, i) => (
              <div key={i} className="flex gap-2 text-[12.5px] text-ink-700">
                <span className="mt-[7px] h-[5px] w-[5px] shrink-0 rounded-full bg-blue-500" />
                {m}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2 rounded-xl border border-[#e6ecfb] bg-gradient-to-br from-blue-50 to-[#f5f3ff] px-3 py-2.5 text-[12.5px] leading-relaxed text-ink-700">
        <span>🤖</span>
        <span>{card.suggestion}</span>
      </div>

      <div className="flex items-center justify-between border-t border-line-2 pt-3">
        <span className="flex items-center gap-1.5 text-xs text-ink-400">
          💬 最近聊天 · {card.last_chat ? new Date(card.last_chat).toLocaleDateString("zh-CN") : "暂无"}
        </span>
        <span className="text-xs font-semibold text-blue-600">查看详情 ›</span>
      </div>
    </div>
  );
}
