"use client";

import { useEffect, useState } from "react";
import { api, PersonDetail, MatchResult, TimelineData, ProfileLoop, ProfileQuestion } from "@/lib/api";
import { STATE_COLORS } from "@/lib/api";
import Radar from "./Radar";

const TABS = ["概览", "人物画像", "关系时间轴", "匹配分析", "约会复盘", "数字人格", "模拟对话"];

const TIMING_LABEL: Record<string, string> = {
  now: "现在适合了解", soon: "近期适合了解", later: "暂缓了解",
  not_relevant: "暂不相关", unknown: "未知", known: "已知",
};
const STATUS_LABEL: Record<string, { label: string; cls: string }> = {
  confirmed: { label: "已确认", cls: "bg-green-100 text-green-700" },
  inferred: { label: "AI 推测", cls: "bg-amber-100 text-amber-700" },
  unknown: { label: "未知", cls: "bg-gray-100 text-gray-500" },
  conflicting: { label: "信息冲突", cls: "bg-red-100 text-red-600" },
  outdated: { label: "可能过期", cls: "bg-gray-100 text-gray-500" },
};

export default function DetailDrawer({ personId, onClose }: { personId: number; onClose: () => void }) {
  const [tab, setTab] = useState("概览");
  const [detail, setDetail] = useState<PersonDetail | null>(null);
  const [match, setMatch] = useState<MatchResult | null>(null);
  const [timeline, setTimeline] = useState<TimelineData | null>(null);
  const [loop, setLoop] = useState<ProfileLoop | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingName, setEditingName] = useState(false);
  const [nameInput, setNameInput] = useState("");
  const [nameError, setNameError] = useState("");

  async function saveName() {
    const name = nameInput.trim();
    if (!name || !detail) return;
    if (name === detail.name) { setEditingName(false); return; }
    try {
      await api.patch(`/persons/${personId}`, { name });
      setEditingName(false);
      setNameError("");
      api.get<PersonDetail>(`/persons/${personId}`).then(setDetail);
    } catch (e) {
      setNameError(e instanceof Error ? e.message : "修改失败");
    }
  }

  useEffect(() => {
    setLoading(true);
    setTab("概览");
    api.get<PersonDetail>(`/persons/${personId}`).then(setDetail).finally(() => setLoading(false));
  }, [personId]);

  useEffect(() => {
    if (tab === "匹配分析" && !match) api.get<MatchResult>(`/persons/${personId}/match`).then(setMatch).catch(() => {});
    if (tab === "关系时间轴" && !timeline) api.get<TimelineData>(`/persons/${personId}/timeline`).then(setTimeline).catch(() => {});
    if (tab === "人物画像" && !loop) api.get<ProfileLoop>(`/persons/${personId}/profile-loop`).then(setLoop).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  async function answer(field: string, ans: string) {
    const res = await api.post<{ profile_loop: ProfileLoop }>(`/persons/${personId}/profile-loop/answer`, { field, answer: ans });
    setLoop(res.profile_loop);
    api.get<PersonDetail>(`/persons/${personId}`).then(setDetail);
  }

  const sc = detail ? STATE_COLORS[detail.state] : "#2563eb";

  return (
    <>
      <div className="fixed inset-0 z-50 bg-ink-900/35 backdrop-blur-sm" onClick={onClose} />
      <aside className="fixed right-0 top-0 z-[60] flex h-screen w-[520px] max-w-[94vw] flex-col bg-white shadow-card-lg">
        {loading || !detail ? (
          <div className="grid flex-1 place-items-center text-ink-400">加载中…</div>
        ) : (
          <>
            <div className="flex items-center gap-3.5 border-b border-line px-5 py-4">
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded-xl text-lg font-bold text-white"
                style={{ background: `linear-gradient(135deg, ${sc}, ${sc}cc)` }}>
                {detail.name[0]}
              </div>
              <div className="min-w-0 flex-1">
                {editingName ? (
                  <div>
                    <div className="flex items-center gap-1.5">
                      <input autoFocus value={nameInput}
                        onChange={(e) => setNameInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter") saveName(); if (e.key === "Escape") setEditingName(false); }}
                        className="w-36 rounded-md border border-blue-300 px-2 py-1 text-[15px] font-bold outline-none focus:border-blue-500" />
                      <button onClick={saveName} className="rounded-md bg-blue-600 px-2 py-1 text-xs font-semibold text-white hover:bg-blue-700">保存</button>
                      <button onClick={() => { setEditingName(false); setNameError(""); }} className="rounded-md px-2 py-1 text-xs text-ink-500 hover:bg-line-2">取消</button>
                    </div>
                    {nameError && <div className="mt-1 text-[11px] text-red-500">{nameError}</div>}
                  </div>
                ) : (
                  <div className="group flex items-center gap-1.5">
                    <span className="text-[17px] font-bold">{detail.name}</span>
                    <button onClick={() => { setNameInput(detail.name); setEditingName(true); }}
                      title="修改姓名"
                      className="grid h-5 w-5 place-items-center rounded text-ink-300 opacity-0 transition-all hover:bg-line-2 hover:text-ink-600 group-hover:opacity-100">
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M17 3a2.83 2.83 0 114 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
                      </svg>
                    </button>
                  </div>
                )}
                <div className="mt-0.5 text-xs text-ink-400">
                  {detail.stage_label} · {detail.state_label} · {Math.round(detail.score)}分
                </div>
              </div>
              <button onClick={onClose} className="grid h-[34px] w-[34px] place-items-center rounded-lg text-lg text-ink-500 hover:bg-line-2">✕</button>
            </div>

            <div className="flex gap-1 overflow-x-auto border-b border-line px-3">
              {TABS.map((t) => (
                <button key={t} onClick={() => setTab(t)}
                  className={`whitespace-nowrap border-b-2 px-3 py-2.5 text-[13px] font-medium ${
                    tab === t ? "border-blue-600 text-blue-700" : "border-transparent text-ink-500 hover:text-ink-700"
                  }`}>
                  {t}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto px-5 py-5">
              {tab === "概览" && <Overview detail={detail} />}
              {tab === "人物画像" && <ProfileTab detail={detail} loop={loop} onAnswer={answer} />}
              {tab === "关系时间轴" && <TimelineTab data={timeline} />}
              {tab === "匹配分析" && <MatchTab match={match} />}
              {tab === "约会复盘" && <DateTab personId={personId} />}
              {tab === "数字人格" && <SkillTab personId={personId} detail={detail} />}
              {tab === "模拟对话" && <SimulateTab personId={personId} name={detail.name} />}
            </div>
          </>
        )}
      </aside>
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-6">
      <div className="mb-3 flex items-center gap-2 text-[13.5px] font-bold">
        <span className="h-3.5 w-[3px] rounded bg-blue-600" />
        {title}
      </div>
      {children}
    </div>
  );
}

function Overview({ detail }: { detail: PersonDetail }) {
  const m = detail.metric;
  return (
    <>
      <Section title="关系评分">
        {m ? (
          <>
            <div className="mb-3 grid grid-cols-3 gap-2.5">
              <Stat v={Math.round(m.overall)} k="综合评分" color="#2563eb" />
              <Stat v={m.delta >= 0 ? `+${m.delta}` : `${m.delta}`} k="评分变化" color={m.delta >= 0 ? "#16a34a" : "#dc2626"} />
              <Stat v={{ up: "上升", down: "下降", stable: "平稳" }[m.trend] || m.trend} k="趋势" />
            </div>
            <div className="mb-2 text-[11px] font-bold text-ink-400">加分因素</div>
            <Chips items={m.plus} cls="bg-green-50 text-green-700" empty="暂无" />
            <div className="mb-2 mt-3 text-[11px] font-bold text-ink-400">扣分因素</div>
            <Chips items={m.minus} cls="bg-amber-50 text-amber-700" empty="暂无" />
            <div className="mt-3 text-xs text-ink-400">数据完整度 {Math.round(m.confidence * 100)}% · 判断可信度 {Math.round(m.confidence * 100)}%</div>
          </>
        ) : <Empty text="暂无评分数据" />}
      </Section>

      <Section title="关系雷达">
        <div className="flex justify-center">
          <Radar values={m ? [m.dimensions["沟通质量"] ?? 50, m.dimensions["兴趣匹配"] ?? 50, m.dimensions["价值观匹配"] ?? 50, m.dimensions["情绪连接"] ?? 50, m.dimensions["未来规划匹配"] ?? 50, m.dimensions["主动程度"] ?? 50] : [50, 50, 50, 50, 50, 50]} />
        </div>
      </Section>

      {detail.advice && (
        <Section title="AI 建议">
          <div className="rounded-xl border border-[#e6ecfb] bg-gradient-to-br from-blue-50 to-[#f5f3ff] p-3.5 text-[13px] leading-relaxed text-ink-700">
            <div className="mb-1.5 font-semibold text-blue-700">{detail.advice.current_state}</div>
            <div>{detail.advice.finding}</div>
            <div className="mt-2">💡 {detail.advice.suggestion}</div>
            <div className="mt-1.5 text-xs text-ink-500">方式：{detail.advice.method} · 时机：{detail.advice.timing}</div>
            {detail.advice.risk && detail.advice.risk !== "—" && (
              <div className="mt-1.5 text-xs text-amber-700">⚠️ {detail.advice.risk}</div>
            )}
          </div>
        </Section>
      )}

      <Section title="长期记忆">
        {detail.memories.length ? (
          <div className="relative pl-4">
            <span className="absolute bottom-1 left-1 top-1 w-0.5 bg-line" />
            {detail.memories.map((mm, i) => (
              <div key={i} className="relative pb-3.5 last:pb-0">
                <span className="absolute -left-4 top-1 h-2.5 w-2.5 rounded-full border-2 border-white bg-blue-500" style={{ boxShadow: "0 0 0 2px #dbeafe" }} />
                <div className="text-[11px] text-ink-400">{new Date(mm.time).toLocaleDateString("zh-CN")} · {mm.category}</div>
                <div className="mt-0.5 text-[13px]">{mm.content}</div>
              </div>
            ))}
          </div>
        ) : <Empty text="暂无记忆，导入聊天后自动生成" />}
      </Section>
    </>
  );
}

function ProfileTab({ detail, loop, onAnswer }: { detail: PersonDetail; loop: ProfileLoop | null; onAnswer: (f: string, a: string) => void }) {
  const s = detail.profile_summary;
  const [editing, setEditing] = useState<string | null>(null);
  return (
    <>
      <Section title={`画像完整度 ${Math.round(s.completeness * 100)}%`}>
        <div className="h-2 overflow-hidden rounded-full bg-line-2">
          <div className="h-full rounded-full bg-gradient-to-r from-blue-500 to-blue-600" style={{ width: `${s.completeness * 100}%` }} />
        </div>
      </Section>

      <Section title="已了解（点击可修改）">
        {s.confirmed.length ? (
          <div className="flex flex-wrap gap-1.5">
            {s.confirmed.map((c) => (
              <button key={c.field} onClick={() => setEditing(c.field)}
                className="group rounded-lg border border-green-200 bg-green-50 px-2.5 py-1.5 text-left transition-colors hover:border-green-400 hover:bg-green-100">
                <span className="text-[11px] text-green-600">{c.label}</span>
                <span className="ml-1.5 text-[12.5px] font-medium text-green-800">{String(c.value)}</span>
                <span className="ml-1.5 text-[10px] text-green-400 opacity-0 transition-opacity group-hover:opacity-100">✎</span>
              </button>
            ))}
          </div>
        ) : <Empty text="暂无已了解信息" />}
        {/* 内联编辑：点击上面字段后展开 */}
        {editing && (() => {
          const cur = s.confirmed.find((c) => c.field === editing);
          if (!cur) return null;
          return (
            <div className="mt-3 rounded-xl border border-blue-200 bg-blue-50 p-3.5">
              <div className="mb-2 text-[12.5px] font-semibold text-blue-800">修改「{cur.label}」</div>
              <InlineAnswer onSubmit={(v) => { onAnswer(editing, v); setEditing(null); }} onCancel={() => setEditing(null)} />
            </div>
          );
        })()}
      </Section>

      {s.inferred.length > 0 && (
        <Section title="AI 初步推断（点击可纠正）">
          <div className="flex flex-wrap gap-1.5">
            {s.inferred.map((c) => (
              <button key={c.field} onClick={() => setEditing(c.field)}
                className="rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-left hover:border-amber-400 hover:bg-amber-100">
                <span className="text-[11px] text-amber-600">{c.label} · 推测</span>
                <span className="ml-1.5 text-[12.5px] font-medium text-amber-800">{String(c.value)}</span>
              </button>
            ))}
          </div>
        </Section>
      )}

      <Section title="未知信息（未知也是数据）">
        <div className="flex flex-col gap-2">
          {s.unknown.map((u) => (
            <div key={u.field} className="flex items-center justify-between rounded-lg border border-line px-3 py-2">
              <span className="text-[13px] font-medium">{u.label}</span>
              <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                u.timing === "now" ? "bg-green-100 text-green-700" : u.timing === "soon" ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-500"
              }`}>
                {TIMING_LABEL[u.timing] || u.timing}
              </span>
            </div>
          ))}
        </div>
      </Section>

      {loop && loop.questions.length > 0 && (
        <Section title={`画像构建 Loop · ${loop.stage_label}`}>
          <div className="flex flex-col gap-3">
            {loop.questions.map((q) => (
              <QuestionCard key={q.field} q={q} onAnswer={onAnswer} />
            ))}
          </div>
        </Section>
      )}
    </>
  );
}

// 单个画像问题卡片：AI 候选 + 自定义输入框 + 一个「跳过」
function QuestionCard({ q, onAnswer }: { q: ProfileQuestion; onAnswer: (f: string, a: string) => void }) {
  const [text, setText] = useState("");
  const submit = (v: string) => { if (v.trim()) { onAnswer(q.field, v.trim()); setText(""); } };
  return (
    <div className="rounded-xl border border-line p-3.5">
      <div className="text-[13px] font-medium">{q.question}</div>
      <div className="mt-1 text-[11px] text-ink-400">方式：{q.method} · 信息价值 {Math.round(q.information_value * 100)}%</div>
      {/* AI 提供的候选回答 */}
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
      {/* 自定义输入 + 跳过 */}
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

// 内联修改已确认字段（候选按钮 + 自定义输入）
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

function TimelineTab({ data }: { data: TimelineData | null }) {
  if (!data) return <Empty text="加载中…" />;
  return (
    <>
      {data.turning_points.length > 0 && (
        <Section title="⚠ 关系转折点">
          {data.turning_points.map((t, i) => (
            <div key={i} className="mb-3 rounded-xl border border-amber-200 bg-amber-50 p-3.5">
              <div className="font-semibold text-amber-800">{t.title}</div>
              <div className="mt-1.5 text-[12.5px] text-ink-700"><b>发生了什么：</b>{t.what}</div>
              <div className="mt-1 text-[12.5px] text-ink-700"><b>判断依据：</b>{t.why}</div>
              <div className="mt-1 text-[12.5px] text-ink-700"><b>建议：</b>{t.suggestion}</div>
              <div className="mt-1.5 text-[11px] text-amber-600">基于聊天行为的推断 · 可信度 {Math.round(t.confidence * 100)}%</div>
            </div>
          ))}
        </Section>
      )}
      <Section title="关系回放（Timeline）">
        <div className="relative pl-4">
          <span className="absolute bottom-1 left-1 top-1 w-0.5 bg-line" />
          {data.events.map((e, i) => (
            <div key={i} className="relative pb-4 last:pb-0">
              <span className={`absolute -left-4 top-1 h-2.5 w-2.5 rounded-full border-2 border-white ${e.is_turning_point ? "bg-red-500" : "bg-blue-500"}`} />
              <div className="text-[11px] text-ink-400">{new Date(e.time).toLocaleString("zh-CN")}</div>
              <div className="mt-0.5 text-[13px]">
                {e.is_turning_point && <span className="mr-1 text-red-500">⚠</span>}
                {e.summary}
              </div>
            </div>
          ))}
        </div>
      </Section>
    </>
  );
}

function MatchTab({ match }: { match: MatchResult | null }) {
  if (!match) return <Empty text="加载中…" />;
  return (
    <>
      <Section title={`总体匹配程度 ${Math.round(match.overall)}`}>
        <div className="mb-2 text-xs text-ink-400">判断可信度：{Math.round(match.confidence * 100)}%（{match.note}）</div>
        <div className="flex flex-col gap-2">
          {Object.entries(match.dimensions).map(([k, v]) => (
            <div key={k} className="flex items-center gap-3">
              <span className="w-16 text-[12.5px] text-ink-700">{k}</span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-line-2">
                <div className="h-full rounded-full bg-blue-600" style={{ width: `${v}%` }} />
              </div>
              <span className="w-8 text-right text-xs text-ink-500">{v > 0 ? Math.round(v) : "未知"}</span>
            </div>
          ))}
        </div>
      </Section>
      <Section title="匹配优点"><Chips items={match.confirmed} cls="bg-green-50 text-green-700" empty="暂无可确认项" /></Section>
      <Section title="潜在冲突"><Chips items={match.conflicts} cls="bg-red-50 text-red-600" empty="暂无冲突" /></Section>
      <Section title="未知区域（建议优先了解）"><Chips items={match.unknown} cls="bg-gray-100 text-gray-600" empty="暂无" /></Section>
    </>
  );
}

function DateTab({ personId }: { personId: number }) {
  const [text, setText] = useState("");
  const [result, setResult] = useState<{ followup_questions: string[] } | null>(null);
  const [busy, setBusy] = useState(false);
  async function submit() {
    if (!text.trim()) return;
    setBusy(true);
    try {
      const res = await api.post<{ date_id: number; followup_questions: string[] }>(`/persons/${personId}/dates`, { description: text });
      setResult(res);
    } finally { setBusy(false); }
  }
  return (
    <Section title="约会复盘 · 自然描述即可">
      <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4}
        placeholder={"今天怎么样？直接告诉我发生了什么。\n例如：今天和她吃了火锅，聊了工作和旅游，整体很轻松。"}
        className="w-full rounded-xl border border-line bg-bg p-3 text-[13px] outline-none focus:border-blue-400" />
      <button onClick={submit} disabled={busy || !text.trim()}
        className="mt-2.5 rounded-lg bg-blue-600 px-4 py-2 text-[13px] font-semibold text-white disabled:opacity-50">
        {busy ? "AI 分析中…" : "提交复盘"}
      </button>
      {result && (
        <div className="mt-4 rounded-xl border border-line p-3.5">
          <div className="mb-2 text-[13px] font-semibold">已记录。还有几个问题值得补充：</div>
          {result.followup_questions.map((q, i) => (
            <div key={i} className="mb-1.5 text-[13px] text-ink-700">① {q}</div>
          ))}
          <div className="mt-2 text-xs text-ink-400">可回答，也可以选择「不知道 / 记不清 / 暂时跳过」。</div>
        </div>
      )}
    </Section>
  );
}

function SkillTab({ personId, detail }: { personId: number; detail: PersonDetail }) {
  const [skill, setSkill] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  async function distill() {
    setBusy(true);
    try {
      const res = await api.post<{ skill: Record<string, unknown> }>(`/persons/${personId}/skill/distill`);
      setSkill(res.skill);
    } finally { setBusy(false); }
  }
  useEffect(() => {
    api.get<{ skill: Record<string, unknown> }>(`/persons/${personId}/skill`).then((r) => setSkill(r.skill)).catch(() => {});
  }, [personId]);
  return (
    <>
      <div className="mb-4 flex items-center justify-between">
        <div className="text-xs text-ink-400">数字人格 · Skill 版本 {detail.skill_versions.length}（持续演化）</div>
        <button onClick={distill} disabled={busy}
          className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50">
          {busy ? "蒸馏中…" : "重新蒸馏"}
        </button>
      </div>
      {skill ? (
        <pre className="overflow-x-auto rounded-xl border border-line bg-bg p-4 text-[12px] leading-relaxed text-ink-700">
          {JSON.stringify(skill, null, 2)}
        </pre>
      ) : <Empty text="尚未蒸馏，点击右上角生成数字人格" />}
    </>
  );
}

function SimulateTab({ personId, name }: { personId: number; name: string }) {
  const [msg, setMsg] = useState("");
  const [mode, setMode] = useState("real");
  const [log, setLog] = useState<{ role: string; text: string; coach?: string[] }[]>([]);
  const [busy, setBusy] = useState(false);
  async function send() {
    if (!msg.trim()) return;
    const mine = msg;
    setLog((l) => [...l, { role: "user", text: mine }]);
    setMsg("");
    setBusy(true);
    try {
      const res = await api.post<{ reply: string; coach?: { tips: string[] } }>(`/persons/${personId}/simulate`, { message: mine, mode });
      setLog((l) => [...l, { role: "person", text: res.reply, coach: res.coach?.tips }]);
    } finally { setBusy(false); }
  }
  return (
    <>
      <div className="mb-3 flex gap-1.5">
        {[["real", "真实聊天"], ["training", "训练模式"], ["stress", "压力测试"], ["rehearsal", "约会前演练"]].map(([k, l]) => (
          <button key={k} onClick={() => setMode(k)}
            className={`rounded-lg px-3 py-1.5 text-xs font-semibold ${mode === k ? "bg-blue-600 text-white" : "border border-line bg-white text-ink-600"}`}>
            {l}
          </button>
        ))}
      </div>
      <div className="mb-3 flex max-h-[46vh] flex-col gap-2.5 overflow-y-auto rounded-xl border border-line bg-bg p-3">
        {log.length === 0 && <div className="py-8 text-center text-xs text-ink-400">与「{name}」的数字人格开始模拟对话</div>}
        {log.map((m, i) => (
          <div key={i} className={`max-w-[80%] rounded-xl px-3 py-2 text-[13px] leading-relaxed ${
            m.role === "user" ? "self-end bg-blue-600 text-white" : "self-start border border-line bg-white text-ink-800"
          }`}>
            {m.text}
            {m.coach && (
              <div className="mt-1.5 border-t border-line pt-1.5 text-[11px] text-amber-600">
                🎓 {m.coach.join(" ")}
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input value={msg} onChange={(e) => setMsg(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="输入想说的话…" className="flex-1 rounded-lg border border-line bg-white px-3 py-2 text-[13px] outline-none focus:border-blue-400" />
        <button onClick={send} disabled={busy || !msg.trim()}
          className="rounded-lg bg-blue-600 px-4 py-2 text-[13px] font-semibold text-white disabled:opacity-50">
          发送
        </button>
      </div>
    </>
  );
}

function Stat({ v, k, color }: { v: React.ReactNode; k: string; color?: string }) {
  return (
    <div className="rounded-xl border border-line bg-bg p-3 text-center">
      <div className="text-lg font-extrabold" style={{ color: color || "#0f172a" }}>{v}</div>
      <div className="mt-0.5 text-[11px] text-ink-400">{k}</div>
    </div>
  );
}
function Chips({ items, cls, empty }: { items: string[]; cls: string; empty: string }) {
  if (!items || items.length === 0) return <div className="text-xs text-ink-400">{empty}</div>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((t, i) => <span key={i} className={`rounded-lg px-2.5 py-1 text-xs ${cls}`}>{t}</span>)}
    </div>
  );
}
function Empty({ text }: { text: string }) {
  return <div className="rounded-lg border border-dashed border-line py-6 text-center text-xs text-ink-400">{text}</div>;
}
