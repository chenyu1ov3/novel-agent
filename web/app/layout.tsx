import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "novel-agent Web UI",
  description: "Browser workspace for multi-agent long-form fiction writing.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN" className="dark">
      <body>{children}</body>
    </html>
  );
}
