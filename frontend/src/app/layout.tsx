'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutGrid, MessageSquare, Search, Box, Sparkles, FolderOpen } from 'lucide-react';
import './globals.css';

const queryClient = new QueryClient();

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased selection:bg-cyan-500/30">
        <QueryClientProvider client={queryClient}>
          {/* Ambient Backgrounds */}
          <div className="bg-aurora" />
          <div className="bg-grain" />

          <div className="min-h-screen flex text-slate-200 font-sans">
            <Sidebar />

            <main className="flex-1 flex flex-col relative z-10 overflow-hidden">
              <AnimatePresence mode="wait">
                <motion.div
                  key="content"
                  initial={{ opacity: 0, filter: 'blur(10px)' }}
                  animate={{ opacity: 1, filter: 'blur(0px)' }}
                  exit={{ opacity: 0, filter: 'blur(10px)' }}
                  transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                  className="flex-1 flex flex-col"
                >
                  {children}
                </motion.div>
              </AnimatePresence>
            </main>
          </div>
        </QueryClientProvider>
      </body>
    </html>
  );
}

function Sidebar() {
  const pathname = usePathname();

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      className="w-[280px] glass h-screen sticky top-0 flex flex-col border-r border-white/5 z-20"
    >
      {/* Brand */}
      <div className="p-8">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <span className="text-xl">🦅</span>
            </div>
            <div className="absolute inset-0 bg-cyan-400 blur-lg opacity-40 animate-pulse" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-white tracking-tight font-display">
              CodeCritic AI
            </h1>
            <p className="text-[10px] uppercase tracking-widest text-cyan-400 font-semibold">
              Agent V2.0
            </p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-4 space-y-2">
        <NavItem href="/" icon={<LayoutGrid size={20} />} label="Overview" active={pathname === '/'} />
        <NavItem href="/chat" icon={<MessageSquare size={20} />} label="Agent Chat" active={pathname === '/chat'} />
        <NavItem href="/search" icon={<Search size={20} />} label="Deep Search" active={pathname === '/search'} />
        <nav className="mt-8 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Tools
        </nav>
        <NavItem href="/refactor" icon={<Box size={20} />} label="Refactor" active={pathname === '/refactor'} />
        <NavItem href="/generate" icon={<Sparkles size={20} />} label="Generate" active={pathname === '/generate'} />
      </nav>

      {/* Footer */}
      <div className="p-6 border-t border-white/5">
        <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/5">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-slate-700 to-slate-600 flex items-center justify-center text-xs">
            JD
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">Connected</p>
            <p className="text-xs text-emerald-400">● Online</p>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}

function NavItem({ href, icon, label, active }: { href: string; icon: React.ReactNode; label: string; active: boolean }) {
  return (
    <Link href={href}>
      <div className="relative group">
        {active && (
          <motion.div
            layoutId="activeNav"
            className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-violet-500/10 rounded-xl border border-cyan-500/20"
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          />
        )}
        <div className={`
          relative flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300
          ${active ? 'text-cyan-400' : 'text-slate-400 group-hover:text-slate-200 group-hover:bg-white/5'}
        `}>
          {icon}
          <span className="font-medium">{label}</span>
          {active && (
            <div className="ml-auto w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
          )}
        </div>
      </div>
    </Link>
  );
}
