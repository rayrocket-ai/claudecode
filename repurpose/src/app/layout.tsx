import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Repurpose — AI Content Repurposing Tool",
  description:
    "Transform your content into platform-optimized posts for Twitter, LinkedIn, Instagram, Email, and Video.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
