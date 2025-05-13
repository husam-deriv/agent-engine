import '@/app/globals.css'
import { Inter } from 'next/font/google'
import { Metadata } from 'next'
import { Toaster } from '@/components/ui/sonner'
import Navbar from '@/components/layout/navbar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'AI Agent Engine',
  description: 'Create and chat with AI agent teams',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          <Navbar />
          <main className="flex-1 container py-8">
            {children}
          </main>
          <footer className="border-t py-4 text-center text-sm text-muted-foreground">
            © {new Date().getFullYear()} Agent Engine. All rights reserved.
          </footer>
        </div>
        <Toaster />
      </body>
    </html>
  )
}
