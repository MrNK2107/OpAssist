import type { Metadata } from 'next'
import { Inter, Bricolage_Grotesque, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-sans' })
const display = Bricolage_Grotesque({ subsets: ['latin'], variable: '--font-display', weight: ['500', '700', '800'] })
const mono = JetBrains_Mono({ subsets: ['latin'], variable: '--font-mono', weight: ['500', '700'] })

export const metadata: Metadata = {
  title: 'OpAssist: the opportunity radar for Indian students',
  description:
    'Hackathons, internships, scholarships and open source, ranked for your skills, year and city, with a deadline radar and an application board.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                var theme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                if (theme === 'dark') document.documentElement.classList.add('dark');
              })();
            `,
          }}
        />
      </head>
      <body className={`${inter.className} ${inter.variable} ${display.variable} ${mono.variable}`}>{children}</body>
    </html>
  )
}
