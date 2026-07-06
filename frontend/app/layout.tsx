import "./globals.css";

export const metadata = {
  title: "GitHub Automation Bot",
  description: "Event-driven GitHub bot dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
