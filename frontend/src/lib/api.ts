const BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${method} ${path} 失败: ${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string) => req<T>("GET", path),
  post: <T>(path: string, body?: unknown) => req<T>("POST", path, body),
  patch: <T>(path: string, body?: unknown) => req<T>("PATCH", path, body),
  del: <T>(path: string) => req<T>("DELETE", path),
};

// ---------- 类型 ----------
export interface Card {
  id: number;
  relationship_id: number;
  name: string;
  age: number | null;
  city: string | null;
  occupation: string | null;
  score: number;
  state: string;
  stage: string;
  radar: number[];
  tags: string[];
  memories: string[];
  last_chat: string | null;
  suggestion: string;
  completeness: number;
}

export interface GanttSegment {
  start: string;
  end: string;
  state: string;
  summary: string;
  engine: string;
}

export interface GanttRow {
  person_id: number;
  name: string;
  state: string;
  state_color: string;
  score: number;
  stage_label: string;
  first_message: string | null;
  last_message: string | null;
  message_count: number;
  segments: GanttSegment[];
  events: { time: string; type: string; summary: string; is_turning_point: boolean }[];
}

export interface Dashboard {
  cards: Card[];
  gantt: GanttRow[];
  total: number;
}

export interface ProfileQuestion {
  field: string;
  label: string;
  question: string;
  method: string;
  information_value: number;
  timing: string;
  importance: number;
  options: string[];
}

export interface ProfileLoop {
  stage: string;
  stage_label: string;
  questions: ProfileQuestion[];
  completeness: number;
  should_converge: boolean;
}

export interface ProfileSummary {
  confirmed: { field: string; label: string; value: unknown }[];
  inferred: { field: string; label: string; value: unknown; confidence: number }[];
  unknown: { field: string; label: string; importance: number; timing: string; information_value: number; method: string }[];
  worth_now: unknown[];
  defer: unknown[];
  completeness: number;
}

export interface PersonDetail {
  id: number;
  name: string;
  relationship_id: number;
  stage: string;
  stage_label: string;
  state: string;
  state_label: string;
  state_color: string;
  score: number;
  facts: Record<string, { value: unknown; source: string; confidence: number; status: string; evidence: string[] }>;
  profile_summary: ProfileSummary;
  metric: { dimensions: Record<string, number>; overall: number; delta: number; trend: string; plus: string[]; minus: string[]; confidence: number } | null;
  memories: { content: string; category: string; time: string }[];
  timeline: { time: string; type: string; summary: string; stage: string; is_turning_point: boolean }[];
  advice: { current_state: string; finding: string; suggestion: string; timing: string; method: string; risk: string } | null;
  skill_versions: { version: number; created_at: string; confidence: number; content: Record<string, unknown> }[];
}

export interface MatchResult {
  overall: number;
  dimensions: Record<string, number>;
  confirmed: string[];
  unknown: string[];
  conflicts: string[];
  inferred: string[];
  confidence: number;
  note: string;
}

export interface TimelineData {
  events: { time: string; type: string; summary: string; stage: string; score_delta: number; is_turning_point: boolean }[];
  turning_points: { title: string; what: string; why: string; before: string; after: string; possible_causes: string[]; suggestion: string; confidence: number }[];
}

export interface WechatStatus {
  configured: boolean;
  reachable: boolean;
}

export interface WechatTarget {
  username: string;
  name: string;
  display_name: string;
  is_group: boolean;
}

export interface WechatTargets {
  account: string;
  source: string;
  targets: WechatTarget[];
  total: number;
}

export const STATE_COLORS: Record<string, string> = {
  warming: "#16a34a", stable: "#2563eb", cooling: "#d97706",
  coldwar: "#dc2626", ended: "#4b5563",
};
export const STATE_LABELS: Record<string, string> = {
  warming: "关系升温", stable: "稳定发展", cooling: "感情降温",
  coldwar: "冷战/踩雷", ended: "已结束",
};
