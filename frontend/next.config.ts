import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 允许本地开发通过 127.0.0.1 / localhost 访问 dev 静态资源
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
