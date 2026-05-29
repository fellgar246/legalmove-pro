'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FileSearch, PlusCircle, LayoutDashboard, ShieldAlert } from 'lucide-react';
import { LegalDisclaimer } from './legal-disclaimer';
import { cn } from '@/lib/cn';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const pathname = usePathname();

  const navigation = [
    {
      name: 'Dashboard',
      href: '/analyses',
      icon: LayoutDashboard,
      active: pathname === '/analyses' || pathname === '/',
    },
    {
      name: 'New Analysis',
      href: '/analyses/new',
      icon: PlusCircle,
      active: pathname === '/analyses/new',
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Top Header Navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-slate-800 bg-slate-950/85 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/analyses" className="flex items-center gap-2 hover:opacity-90 transition-opacity">
            <div className="w-9 h-9 rounded-xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shadow-inner">
              <FileSearch className="w-5 h-5" />
            </div>
            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-slate-100 via-slate-200 to-slate-400 bg-clip-text text-transparent">
              LegalMove Pro
            </span>
          </Link>

          <nav className="flex items-center gap-1 sm:gap-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all duration-200",
                    item.active
                      ? "bg-slate-900 text-slate-100 border border-slate-800"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/50 border border-transparent"
                  )}
                >
                  <Icon className={cn("w-4 h-4", item.active ? "text-indigo-400" : "text-slate-500")} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12 flex flex-col">
        {children}
      </main>

      {/* Footer with Persistent Legal Disclaimer */}
      <footer className="w-full border-t border-slate-900 bg-slate-950 py-8 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          <div className="max-w-3xl mx-auto">
            <LegalDisclaimer />
          </div>
          <div className="border-t border-slate-900 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-slate-600">
            <p>&copy; {new Date().getFullYear()} LegalMove Pro. Professional AI-assisted legal contract review system.</p>
            <div className="flex gap-4">
              <span className="hover:text-slate-400 transition-colors">v0.2.2 MVP</span>
              <span>•</span>
              <span className="hover:text-slate-400 transition-colors">Local Sandbox</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
