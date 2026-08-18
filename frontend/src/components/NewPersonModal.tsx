"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function NewPersonModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [mode, setMode] = useState<"describe" | "import">("describe");
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [chat, setChat] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    if (!name.trim()) { setError("请填写姓名"); return; }
    setBusy(true); setError("");
    try {
      if (mode === "describe") {
        await api.post("/persons", { name: name.trim(), description: desc });
      } else {
        if (!chat.trim()) { setError("请粘贴聊天记录"); setBusy(false); return; }
        await api.post("/persons", { name: name.trim(), description: desc });
        await api.post("/import/text", { person_name: name.trim(), text: chat, source: "text" });
      }
      onCreated();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "创建失败");
    } finally { setBusy(false); }
  }

  return (
    <div className="fixed inset-0 z-[70] grid place-items-center bg-ink-900/40 p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="w-[560px] max-w-full rounded-2xl bg-white p-6 shadow-card-lg" onClick={(e) => e.stopPropagation()}>
        <div className="mb-1 text-lg font-bold">新增相亲对象</div>
        <div className="mb-5 text-xs text-ink-400">不需要填表单，直接描述她，或导入聊天记录，AI 会自动建立画像。</div>

        <div className="mb-4 flex gap-1.5 rounded-lg bg-bg p-1">
          {[["describe", "✍️ 描述她"], ["import", "💬 导入聊天记录"]].map(([k, l]) => (
            <button key={k} onClick={() => setMode(k as "describe" | "import")}
              className={`flex-1 rounded-md py-2 text-[13px] font-semibold ${mode === k ? "bg-white text-blue-700 shadow-card" : "text-ink-500"}`}>
              {l}
            </button>
          ))}
        </div>

        <label className="mb-1 block text-xs font-semibold text-ink-700">她的称呼</label>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="例如：林小雨"
          className="mb-4 w-full rounded-lg border border-line bg-white px-3 py-2.5 text-[13px] outline-none focus:border-blue-400" />

        {mode === "describe" ? (
          <>
            <label className="mb-1 block text-xs font-semibold text-ink-700">用一句话描述她（可选）</label>
            <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={4}
              placeholder="例如：27岁，在上海做产品经理，喜欢旅游和猫，性格比较慢热。"
              className="w-full rounded-lg border border-line bg-bg p-3 text-[13px] outline-none focus:border-blue-400" />
          </>
        ) : (
          <>
            <label className="mb-1 block text-xs font-semibold text-ink-700">粘贴聊天记录</label>
            <textarea value={chat} onChange={(e) => setChat(e.target.value)} rows={6}
              placeholder={"支持格式：\n2026-06-01 10:00 我: 周末有空吗\n2026-06-01 10:05 林小雨: 有呀"}
              className="w-full rounded-lg border border-line bg-bg p-3 font-mono text-[12px] outline-none focus:border-blue-400" />
          </>
        )}

        {error && <div className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{error}</div>}

        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-lg border border-line px-4 py-2 text-[13px] text-ink-600 hover:bg-line-2">取消</button>
          <button onClick={submit} disabled={busy}
            className="rounded-lg bg-blue-600 px-4 py-2 text-[13px] font-semibold text-white hover:bg-blue-700 disabled:opacity-50">
            {busy ? "AI 分析中…" : mode === "describe" ? "建立画像" : "导入并分析"}
          </button>
        </div>
      </div>
    </div>
  );
}
