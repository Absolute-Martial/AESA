import type { Metadata } from 'next';
import './globals.css';
import { ThemeProvider, ApolloProvider } from '@/lib/contexts';

export const metadata: Metadata = {
  title: 'AESA - AI Engineering Study Assistant',
  description: 'Local-first scheduling and personal learning assistant for KU Engineering students',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* Material Symbols Outlined font */}
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
          rel="stylesheet"
        />
        {/* Prevent flash of wrong theme */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('aesa-theme');
                  var resolved = theme;
                  if (!theme || theme === 'system') {
                    resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                  }
                  document.documentElement.classList.add(resolved);
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body className="min-h-screen bg-sand-100 dark:bg-gray-900 text-text-main dark:text-gray-100 transition-colors">
        <ApolloProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </ApolloProvider>
      </body>
    </html>
  );
}
