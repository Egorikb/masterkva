import type { Metadata, Viewport } from 'next'
import { Nunito, Source_Code_Pro } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import './globals.css'

const nunito = Nunito({ 
  subsets: ["latin", "cyrillic"],
  variable: "--font-nunito"
});
const sourceCodePro = Source_Code_Pro({ 
  subsets: ["latin"],
  variable: "--font-source-code-pro"
});

export const metadata: Metadata = {
  title: 'Мастер Кват | Образовательная платформа',
  description: 'Интерактивная образовательная платформа для детей 7-12 лет с геймификацией и методикой Кунг-фу',
  generator: 'v0.app',
  icons: {
    icon: [
      {
        url: '/icon-light-32x32.png',
        media: '(prefers-color-scheme: light)',
      },
      {
        url: '/icon-dark-32x32.png',
        media: '(prefers-color-scheme: dark)',
      },
      {
        url: '/icon.svg',
        type: 'image/svg+xml',
      },
    ],
    apple: '/apple-icon.png',
  },
}

export const viewport: Viewport = {
  themeColor: '#3d9970',
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ru" className="bg-background">
      <body className={`${nunito.variable} ${sourceCodePro.variable} font-sans antialiased`}>
        {children}
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
