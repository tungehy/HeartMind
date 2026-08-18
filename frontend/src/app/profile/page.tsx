"use client";

import { useEffect, useState } from "react";
import { api, ProfileLoop, ProfileQuestion } from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import Link from "next/link";

interface UserProfile {
  user_id: number;
  facts: Record<string, { value: unknown; status: string }>;
  summary: { completeness: number; confirmed: { field: string; label: string; value: unknown }[] };
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loop, setLoop] = useState<ProfileLoop | null>(null);
  const [skill, setSkill] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);

  function load() {
    api.get<UserProfile>("/user/profile").then(setProfile).catch(() => {});
    api.get<ProfileLoop>("/user/profile-loop").then(setLoop).catch(() => {});
  }
  useEffect(load, []);

  async function answer(field: string, ans: string) {
    await api.post("/user/profile/answer", { field, answer: ans });
    load();
  }
  async function distill() {
    setBusy(true);
    try {
      const res = await api.post<{ skill: Record<string, unknown> }>("/user/skill/distill");
      setSkill(res.skill);
    } finally { setBusy(false); }
  }

  const completeness = profile?.summary.completeness ?? 0;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 border-b border-line bg-white/85 px-6 py-4 backdrop-blur">
          <h1 className="text-lg font-bold">我的画像 · User Digital Twin</h1>
          <div className="mt-0.5 text-xs text-ink-400">
            真正有价值的匹配 = 对象画像 × 用户画像。
            <Link href="/" className="ml-2 text-blue-600 hover:underline">← 返回总览</Link>
          </div>
        </header>

        <div className="grid flex-1 grid-cols-1 gap-5 px-6 py-5 lg:grid-cols-2">
          {/* 左：画像构建 */}
          <section className="rounded-2xl border border-line bg-white p-5 shadow-card">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-[15px] font-bold">自我画像构建</h2>
              <span className="text-xs text-ink-400">完整度 {Math.round(completeness * 100)}%</span>
            </div>
            <div className="mb-5 h-2 overflow-hidden rounded-full bg-line-2">
              <div className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500" style={{ width: `${completeness * 100}%` }} />
            </div>

            <div className="mb-5">
              <div className="mb-2 text-[11px] font-bold text-ink-400">已了解（点击可修改）</div>
              {profile && profile.summary.confirmed.length ? (
                <div className="flex flex-wrap gap-1.5">
                  {profile.summary.confirmed.map((c) => (
                    <button key={c.field} onClick={() => setEditing(c.field)}
                      className="group rounded-lg border border-green-200 bg-green-50 px-2.5 py-1.5 text-left hover:border-green-400 hover:bg-green-100">
                      <span className="text-[11px] text-green-600">{c.label}</span>
                      <span className="ml-1.5 text-[12.5px] font-medium text-green-800">{String(c.value)}</span>
                      <span className="ml-1 text-[10px] text-green-400 opacity-0 group-hover:opacity-100">✎</span>
                    </button>
                  ))}
                </div>
              ) : <div className="text-xs text-ink-400">还没有，回答下面的问题开始构建</div>}
              {editing && (() => {
                const cur = profile?.summary.confirmed.find((c) => c.field === editing);
                if (!cur) return null;
                return (
                  <div className="mt-3 rounded-xl border border-blue-200 bg-blue-50 p-3.5">
                    <div className="mb-2 text-[12.5px] font-semibold text-blue-800">修改「{cur.label}」</div>
                    <InlineAnswer onSubmit={(v) => { answer(editing, v); setEditing(null); }} onCancel={() => setEditing(null)} />
                  </div>
                );
              })()}
            </div>

            <div className="mb-2 text-[11px] font-bold text-ink-400">AI 想了解（选候选 / 自定义输入 / 跳过）</div>
            <div className="flex flex-col gap-3">
              {loop && loop.questions.length ? loop.questions.map((q) => (
                <SelfQuestionCard key={q.field} q={q} onAnswer={answer} />
              )) : <div className="text-xs text-ink-400">画像已较为完整</div>}
            </div>
          </section>

          {/* 右：数字人格 */}
          <section className="rounded-2xl border border-line bg-white p-5 shadow-card">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-[15px] font-bold">我的数字人格（Self Skill）</h2>
              <button onClick={distill} disabled={busy}
                className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50">
                {busy ? "蒸馏中…" : "生成 / 更新"}
              </button>
            </div>
            {skill ? (
              <pre className="max-h-[70vh] overflow-auto rounded-xl border border-line bg-bg p-4 text-[12px] leading-relaxed text-ink-700">
                {JSON.stringify(skill, null, 2)}
              </pre>
            ) : (
              <div className="grid place-items-center rounded-xl border border-dashed border-line py-16 text-center text-xs text-ink-400">
                先完善左侧画像，再点击「生成」蒸馏你的数字人格
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

// 自我画像问题卡片：AI 候选 + 自定义输入框 + 一个「跳过」
function SelfQuestionCard({ q, onAnswer }: { q: ProfileQuestion; onAnswer: (f: string, a: string) => void }) {
  const [text, setText] = useState("");
  const submit = (v: string) => { if (v.trim()) { onAnswer(q.field, v.trim()); setText(""); } };
  return (
    <div className="rounded-xl border border-line p-3.5">
      <div className="text-[13px] font-medium">{q.label}</div>
      {q.options.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {q.options.map((opt) => (
            <button key={opt} onClick={() => onAnswer(q.field, opt)}
              className="rounded-lg border border-blue-200 bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 hover:border-blue-400 hover:bg-blue-100">
              {opt}
            </button>
          ))}
        </div>
      )}
      <div className="mt-2.5 flex gap-1.5">
        <input value={text} onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit(text)}
          placeholder="其它回答…"
          className="flex-1 rounded-lg border border-line bg-white px-2.5 py-1.5 text-xs outline-none focus:border-blue-400" />
        <button onClick={() => submit(text)} disabled={!text.trim()}
          className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-40">
          确定
        </button>
        <button onClick={() => onAnswer(q.field, "跳过")} title="现在给不了，先跳过"
          className="rounded-lg border border-line bg-white px-3 py-1.5 text-xs text-ink-500 hover:bg-line-2">
          跳过
        </button>
      </div>
    </div>
  );
}

// 内联修改已了解字段
function InlineAnswer({ onSubmit, onCancel }: { onSubmit: (v: string) => void; onCancel: () => void }) {
  const [text, setText] = useState("");
  return (
    <div className="flex gap-1.5">
      <input autoFocus value={text} onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter" && text.trim()) onSubmit(text.trim()); if (e.key === "Escape") onCancel(); }}
        placeholder="输入新的值，回车确认"
        className="flex-1 rounded-lg border border-blue-300 bg-white px-2.5 py-1.5 text-xs outline-none" />
      <button onClick={() => text.trim() && onSubmit(text.trim())} disabled={!text.trim()}
        className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-40">
        保存
      </button>
      <button onClick={onCancel} className="rounded-lg border border-line bg-white px-3 py-1.5 text-xs text-ink-500 hover:bg-line-2">
        取消
      </button>
    </div>
  );
}
