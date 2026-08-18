"use client";

import { useCallback, useEffect, useState } from "react";
import { api, Dashboard } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import Topbar from "@/components/Topbar";
import Gantt from "@/components/Gantt";
import PersonCard from "@/components/PersonCard";
import DetailDrawer from "@/components/DetailDrawer";
import NewPersonModal from "@/components/NewPersonModal";

export default function Home() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<number | null>(null);
  const [showNew, setShowNew] = useState(false);

  const load = useCallback(() => {
    api.get<Dashboard>("/dashboard").then(setData).catch((e) => setError(e.message));
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <div className="flex flex-col gap-5 px-6 py-5 pb-10">
          {error && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-[13px] text-amber-800">
              ⚠️ 无法连接后端（{error}）。请先启动：<code className="rounded bg-amber-100 px-1">uvicorn app.main:app --port 8000</code>
            </div>
          )}

          {/* 第一部分：甘特图 */}
          <section id="timeline" className="rounded-2xl border border-line bg-white shadow-card">
            <div className="flex items-center gap-3 border-b border-line-2 px-5 py-4">
              <div className="flex-1">
                <h2 className="text-[15.5px] font-bold">相亲对象关系时间轴</h2>
                <div className="mt-0.5 text-xs text-ink-400">AI 自动识别每段关系的阶段变化，横轴为时间，纵轴为对象</div>
              </div>
            </div>
            <div className="px-5 pb-4 pt-3">
              {data && data.gantt.length > 0 ? (
                <Gantt rows={data.gantt} onSelect={(id) => setSelected(id)} />
              ) : (
                <EmptyState text="暂无关系数据，点击下方「新增相亲对象」开始" />
              )}
            </div>
          </section>

          {/* 第二部分：对象卡片 */}
          <section id="persons" className="rounded-2xl border border-line bg-white shadow-card">
            <div className="flex items-center gap-3 border-b border-line-2 px-5 py-4">
              <div className="flex-1">
                <h2 className="text-[15.5px] font-bold">相亲对象</h2>
                <div className="mt-0.5 text-xs text-ink-400">按照 AI 综合关系评分排序</div>
              </div>
              <button onClick={() => setShowNew(true)}
                className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-[13px] font-semibold text-white shadow-card-md hover:bg-blue-700">
                ＋ 新增相亲对象
              </button>
            </div>
            <div className="grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-4 p-5">
              {data && data.cards.length > 0 ? (
                data.cards.map((c, i) => (
                  <PersonCard key={c.id} card={c} rank={i + 1} onOpen={() => setSelected(c.id)} />
                ))
              ) : (
                <div className="col-span-full">
                  <EmptyState text="还没有相亲对象，点击右上角「新增相亲对象」，用一句话描述她即可开始" />
                </div>
              )}
            </div>
          </section>
        </div>
      </main>

      {selected !== null && <DetailDrawer personId={selected} onClose={() => { setSelected(null); load(); }} />}
      {showNew && <NewPersonModal onClose={() => setShowNew(false)} onCreated={load} />}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="grid place-items-center rounded-xl border border-dashed border-line py-16 text-center">
      <div>
        <div className="mb-2 text-3xl">🌱</div>
        <div className="text-[13px] text-ink-400">{text}</div>
      </div>
    </div>
  );
}
