import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Qdrant CMS/DMS',
  description: 'Document Management System with Qdrant vector search',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
