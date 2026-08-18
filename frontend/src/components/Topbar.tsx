"use client";

export default function Topbar() {
  return (
    <header className="sticky top-0 z-20 flex items-center gap-4 border-b border-line bg-white/85 px-6 py-4 backdrop-blur">
      <div className="min-w-0 flex-1">
        <h1 className="text-lg font-bold">关系总览</h1>
        <div className="mt-0.5 text-xs text-ink-400">AI 持续分析每段关系的发展趋势</div>
      </div>
      <div className="flex w-[220px] items-center gap-2 rounded-lg border border-line bg-bg px-3 py-2">
        <span>🔍</span>
        <input placeholder="搜索相亲对象、话题、记忆…"
          className="w-full bg-transparent text-[13px] text-ink-700 outline-none" />
        <span className="rounded border border-line px-1.5 py-0.5 text-[11px] text-ink-400">⌘K</span>
      </div>
      <button className="flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-line bg-white px-3 py-2 text-[13px] text-ink-700 hover:border-[#cfd8e3]">
        📅 近 6 个月 <span className="text-ink-400">▾</span>
      </button>
      <button className="flex items-center gap-1.5 whitespace-nowrap rounded-lg border border-line bg-white px-3 py-2 text-[13px] text-ink-700 hover:border-[#cfd8e3]">
        👥 全部对象 <span className="text-ink-400">▾</span>
      </button>
      <button className="flex items-center gap-1.5 whitespace-nowrap rounded-lg bg-blue-600 px-3.5 py-2 text-[13px] font-semibold text-white shadow-card-md transition-colors hover:bg-blue-700">
        📄 生成 AI 报告
      </button>
      <button className="relative grid h-[38px] w-[38px] place-items-center rounded-lg border border-line bg-white text-base hover:bg-line-2">
        🔔<span className="absolute right-[7px] top-[6px] h-[7px] w-[7px] rounded-full border-[1.5px] border-white bg-coldwar" />
      </button>
      <button className="grid h-[38px] w-[38px] place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-blue-600 text-sm font-bold text-white">
        我
      </button>
    </header>
  );
}
