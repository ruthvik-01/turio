import type { NextConfig } from "next";

const config: NextConfig = {
  distDir: process.env.TURIO_UI_VERIFY === "1" ? ".next/atmos" : ".next",
};

export default config;
