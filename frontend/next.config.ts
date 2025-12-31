import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // rewrites removed for full-stack migration
  // async rewrites() {
  //   return [];
  // },
};

export default nextConfig;
