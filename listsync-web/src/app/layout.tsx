import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/components/layout/providers";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "ListSync Web UI",
  description: "Web interface for ListSync - Bridge Your Watchlist & Media Server",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <style>
          {`@import url('https://fonts.googleapis.com/css2?family=Titillium+Web:ital,wght@0,200;0,300;0,400;0,600;0,700;0,900;1,200;1,300;1,400;1,600;1,700&display=swap');`}
        </style>
      </head>
      <body className="titillium-web-regular" suppressHydrationWarning>
        <Providers>
        {children}
        </Providers>
        <Toaster 
          position="top-right"
          theme="dark"
          richColors
          closeButton
        />
      </body>
    </html>
  );
}
