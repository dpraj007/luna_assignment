import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Luna Social - Discover Your Next Dining Experience',
  description: 'AI-powered social dining platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="pb-20">{children}</body>
    </html>
  )
}

