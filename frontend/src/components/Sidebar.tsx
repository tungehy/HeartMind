"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/", icon: "🏠", label: "总览" },
  { href: "/#persons", icon: "👥", label: "相亲对象" },
  { href: "/#timeline", icon: "💬", label: "聊天分析" },
  { href: "/profile", icon: "🧠", label: "数字人格" },
  { href: "/#timeline", icon: "📅", label: "关系时间轴" },
  { href: "/#persons", icon: "📊", label: "数据分析" },
  { href: "/profile", icon: "🤖", label: "AI 助手" },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sticky top-0 flex h-screen w-[260px] shrink-0 flex-col border-r border-line bg-white">
      <div className="flex items-center gap-3 px-5 pb-4 pt-5">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 text-xl shadow-card-md">
          ❤️
        </div>
        <div>
          <div className="text-base font-bold tracking-wide">HeartMind</div>
          <div className="mt-0.5 text-[11px] text-ink-400">AI 关系智能平台</div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-2">
        <div className="px-3 pb-1.5 pt-3 text-[11px] tracking-wider text-ink-400">工作台</div>
        {NAV.map((n, i) => {
          const active = (n.href === "/" && pathname === "/") || (n.href !== "/" && pathname.startsWith(n.href.split("#")[0]) && n.href !== "/");
          return (
            <Link key={i} href={n.href}
              className={`mb-0.5 flex items-center gap-3 rounded-lg px-3 py-2.5 text-[13.5px] font-medium transition-colors ${
                active ? "bg-blue-50 font-semibold text-blue-700" : "text-ink-700 hover:bg-line-2"
              }`}>
              <span className="w-[18px] text-center text-[15px]">{n.icon}</span>
              {n.label}
            </Link>
          );
        })}
      </nav>

      <div className="m-3 rounded-2xl border border-[#e2e8ff] bg-gradient-to-br from-blue-50 to-[#f5f3ff] p-3.5">
        <div className="flex items-center gap-1.5 text-[11.5px] font-bold text-blue-700">✨ AI 今日建议</div>
        <div className="mt-2.5 text-xs text-ink-500">今天适合主动联系：</div>
        <div className="mb-2 mt-0.5 text-base font-extrabold">林小雨</div>
        <div className="text-xs leading-relaxed text-ink-700">
          最近她频繁提到旅游，可以分享一篇旅行攻略，避免继续讨论工作压力。
        </div>
        <button className="mt-2.5 w-full rounded-lg bg-blue-600 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-blue-700">
          一键生成开场白
        </button>
      </div>
    </aside>
  );
}
