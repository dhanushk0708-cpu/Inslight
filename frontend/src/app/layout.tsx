import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'INSLIGHT — AI Business Intelligence Platform',
  description: 'Enterprise-grade AI-Powered Business Intelligence, Predictive Analytics & Automated Reporting',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
