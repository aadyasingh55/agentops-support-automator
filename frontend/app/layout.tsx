import "./globals.css";

export const metadata = {
  title: "AgentOps Support Automator",
  description: "Human-reviewed multi-agent support workflow console.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
