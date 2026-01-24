import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Відео з Фотографій | Професійні Відео на Замовлення',
  description: 'Створюємо унікальні AI-відео з ваших фотографій для будь-якої події: весілля, дні народження, ювілеї та інші особливі моменти.',
  icons: {
    icon: '/favicon.ico',
    apple: '/apple-touch-icon.png',
  },
  openGraph: {
    title: 'AI Відео з Фотографій | Професійні Відео на Замовлення',
    description: 'Створюємо унікальні AI-відео з ваших фотографій для будь-якої події',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="uk">
      <head>
        <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
        <link rel="icon" type="image/png" href="/favicon.ico" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#6366f1" />
      </head>
      <body>{children}</body>
    </html>
  )
}
