"use client";

import { useEffect, useMemo, useState } from "react";
import { api, WechatStatus, WechatTarget } from "@/lib/api";

export default function NewPersonModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [mode, setMode] = useState<"describe" | "import">("describe");
  const [importTab, setImportTab] = useState<"wechat" | "paste">("wechat");
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [chat, setChat] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // 微信自动导出
  const [wxStatus, setWxStatus] = useState<WechatStatus | null>(null);
  const [wxTargets, setWxTargets] = useState<WechatTarget[] | null>(null);
  const [wxQuery, setWxQuery] = useState("");
  const [wxSelected, setWxSelected] = useState<WechatTarget | null>(null);
  const [wxLoading, setWxLoading] = useState(false);

  useEffect(() => {
    if (mode !== "import") return;
    api.get<WechatStatus>("/wechat/status").then((s) => {
      setWxStatus(s);
      if (s.configured && s.reachable) {
        setWxLoading(true);
        api.get<{ targets: WechatTarget[] }>("/wechat/targets")
          .then((d) => setWxTargets(d.targets))
          .catch(() => setWxTargets([]))
          .finally(() => setWxLoading(false));
      } else {
        setImportTab("paste");
      }
    }).catch(() => { setWxStatus({ configured: false, reachable: false }); setImportTab("paste"); });
  }, [mode]);

  const filtered = useMemo(() => {
    if (!wxTargets) return [];
    const q = (wxQuery || name).trim().toLowerCase();
    const list = q
      ? wxTargets.filter((t) => (t.display_name || t.name || "").toLowerCase().includes(q))
      : wxTargets;
    return list.slice(0, 20);
  }, [wxTargets, wxQuery, name]);

  async function submit() {
    if (!name.trim() && !(mode === "import" && importTab === "wechat" && wxSelected)) {
      setError("请填写姓名"); return;
    }
    setBusy(true); setError("");
    try {
      const personName = (name.trim() || wxSelected?.display_name || "").trim();
      if (mode === "describe") {
        await api.post("/persons", { name: personName, description: desc });
      } else if (importTab === "wechat") {
        if (!wxSelected) { setError("请先选择微信联系人"); setBusy(false); return; }
        await api.post("/import/wechat", { person_name: personName, username: wxSelected.username });
      } else {
        if (!chat.trim()) { setError("请粘贴聊天记录"); setBusy(false); return; }
        await api.post("/persons", { name: personName, description: desc });
        await api.post("/import/text", { person_name: personName, text: chat, source: "text" });
      }
      onCreated();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "创建失败");
    } finally { setBusy(false); }
  }

  const wxReady = !!(wxStatus && wxStatus.configured && wxStatus.reachable);

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
            {wxReady && (
              <div className="mb-3 flex gap-1.5 rounded-lg bg-bg p-1">
                {[["wechat", "📲 微信自动导出"], ["paste", "📋 手动粘贴"]].map(([k, l]) => (
                  <button key={k} onClick={() => setImportTab(k as "wechat" | "paste")}
                    className={`flex-1 rounded-md py-1.5 text-[12.5px] font-semibold ${importTab === k ? "bg-white text-blue-700 shadow-card" : "text-ink-500"}`}>
                    {l}
                  </button>
                ))}
              </div>
            )}

            {importTab === "wechat" && wxReady ? (
              <div className="rounded-xl border border-line p-3">
                {wxLoading ? (
                  <div className="py-6 text-center text-xs text-ink-400">正在读取微信联系人…</div>
                ) : wxSelected ? (
                  <div className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-3 py-2.5">
                    <div>
                      <div className="text-[13px] font-semibold text-blue-800">{wxSelected.display_name || wxSelected.name}</div>
                      <div className="text-[10px] text-blue-400">{wxSelected.username}</div>
                    </div>
                    <button onClick={() => setWxSelected(null)} className="text-xs text-ink-400 hover:text-ink-600">重选</button>
                  </div>
                ) : (
                  <>
                    <input value={wxQuery} onChange={(e) => setWxQuery(e.target.value)}
                      placeholder="搜索微信备注 / 昵称（默认用上方称呼过滤）"
                      className="mb-2 w-full rounded-lg border border-line bg-white px-3 py-2 text-[12.5px] outline-none focus:border-blue-400" />
                    <div className="max-h-48 overflow-y-auto">
                      {filtered.length ? filtered.map((t) => (
                        <button key={t.username}
                          onClick={() => { setWxSelected(t); if (!name.trim()) setName(t.display_name || t.name); }}
                          className="flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left hover:bg-line-2">
                          <span className="text-[12.5px] font-medium">{t.display_name || t.name || t.username}</span>
                          <span className="text-[10px] text-ink-400">{t.username}</span>
                        </button>
                      )) : (
                        <div className="py-6 text-center text-xs text-ink-400">
                          {wxTargets === null ? "加载中…" : "没有匹配的联系人，换个关键词试试"}
                        </div>
                      )}
                    </div>
                  </>
                )}
                <div className="mt-2 text-[10px] leading-4 text-ink-400">
                  将从本机微信数据库自动导出你与她的全部聊天记录并分析，全程本地处理。
                </div>
              </div>
            ) : (
              <>
                {!wxReady && (
                  <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] leading-4 text-amber-700">
                    未检测到微信导出服务（WeChatDataAnalysis）。启动该服务并在 backend/.env 配置
                    <code className="mx-1 rounded bg-amber-100 px-1">WECHAT_EXPORT_URL</code>
                    后，即可免粘贴自动导出。当前可先手动粘贴。
                  </div>
                )}
                <label className="mb-1 block text-xs font-semibold text-ink-700">粘贴聊天记录</label>
                <textarea value={chat} onChange={(e) => setChat(e.target.value)} rows={6}
                  placeholder={"支持格式：\n2026-06-01 10:00 我: 周末有空吗\n2026-06-01 10:05 林小雨: 有呀"}
                  className="w-full rounded-lg border border-line bg-bg p-3 font-mono text-[12px] outline-none focus:border-blue-400" />
              </>
            )}
          </>
        )}

        {error && <div className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-600">{error}</div>}

        <div className="mt-5 flex justify-end gap-2">
          <button onClick={onClose} className="rounded-lg border border-line px-4 py-2 text-[13px] text-ink-600 hover:bg-line-2">取消</button>
          <button onClick={submit} disabled={busy}
            className="rounded-lg bg-blue-600 px-4 py-2 text-[13px] font-semibold text-white hover:bg-blue-700 disabled:opacity-50">
            {busy ? "AI 分析中…" : mode === "describe" ? "建立画像"
              : importTab === "wechat" && wxReady ? "导出并分析" : "导入并分析"}
          </button>
        </div>
      </div>
    </div>
  );
}
