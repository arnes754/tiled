import type { NextConfig } from "next";

const config: NextConfig = {
  // Renders come from the API in dev; proxy so the browser sees one origin.
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://localhost:8000/:path*" }];
  },
};

export default config;
