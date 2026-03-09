import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DASH.AI — AI BI Co-Pilot',
  description: 'Voice-first AI Business Intelligence dashboards',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}