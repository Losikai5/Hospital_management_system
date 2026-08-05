import type { Metadata } from "next";
import { Toaster } from "sonner";
import { AuthProvider } from "@/lib/auth-context";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "Serenity Health — Hospital Management System",
    template: "%s | Serenity Health",
  },
  description:
    "A modern hospital management platform connecting patients with healthcare providers.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full" suppressHydrationWarning>
      <body className="min-h-full flex flex-col antialiased">
        <AuthProvider>
          {children}
          <Toaster
            richColors
            closeButton
            position="top-right"
            toastOptions={{
              duration: 4000,
            }}
          />
        </AuthProvider>
      </body>
    </html>
  );
}
