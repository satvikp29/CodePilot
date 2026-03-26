import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'CodePilot — AI Code Review',
  description: 'Paste your code. Get honest, structured feedback in seconds.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-paper text-ink">{children}</body>
    </html>
  )
}
