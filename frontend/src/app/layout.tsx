import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HeartMind · AI 关系智能平台",
  description: "以项目管理思想管理相亲交往全生命周期的 AI Relationship Intelligence Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
