import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Відео з Фотографій | Професійні Відео на Замовлення',
  description: 'Створюємо унікальні AI-відео з ваших фотографій для будь-якої події: весілля, дні народження, ювілеї та інші особливі моменти.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="uk">
      <body>{children}</body>
    </html>
  )
}
