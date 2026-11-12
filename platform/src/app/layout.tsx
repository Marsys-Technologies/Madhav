import type { Metadata, Viewport } from 'next'
import { preload } from 'react-dom'
import './root-fonts.css'
import './globals.css'
import './journey1.css'
import '@/styles/theme_tokens.css'
import '@/lib/styles/marsys-theme.css'
import { Toaster } from '@/components/ui/sonner'
import { Providers } from './providers'
import BuildCompleteToast from '@/components/dashboard/BuildCompleteToast'

export const metadata: Metadata = {
  title: 'MARSYS-JIS',
  description: 'Jyotish Intelligence System',
}

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#f7f6f4' },
    { media: '(prefers-color-scheme: dark)', color: '#1c1c1a' },
  ],
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  interactiveWidget: 'resizes-content',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  preload('/brand/fonts/root/e4af272ccee01ff0-s.p.woff2', {
    as: 'font',
    type: 'font/woff2',
    crossOrigin: 'anonymous',
  })
  return (
    <html lang="en" suppressHydrationWarning className="root-fonts">
      <body className="bg-background font-sans text-foreground antialiased">
        <Providers>{children}</Providers>
        <BuildCompleteToast />
        <Toaster />
      </body>
    </html>
  )
}
