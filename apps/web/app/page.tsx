import Link from 'next/link';
import { ArrowRight, Sparkles, FileSearch, ShieldAlert } from 'lucide-react';

export default function Home() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center max-w-4xl mx-auto py-12 px-4 text-center space-y-8 animate-fade-in">
      {/* Brand logo splash */}
      <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-2xl bg-indigo-500/5 border border-indigo-500/15 shadow-inner text-indigo-400">
        <Sparkles className="w-4 h-4 animate-pulse" />
        <span className="text-xs font-bold uppercase tracking-widest">Local-First Sandbox MVP v0.2.2</span>
      </div>

      {/* Main headings */}
      <div className="space-y-4">
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-black tracking-tight leading-none text-slate-100">
          AI-Assisted Contract <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-indigo-400 via-indigo-200 to-indigo-600 bg-clip-text text-transparent">
            Review and Comparison
          </span>
        </h1>
        <p className="text-xs sm:text-base text-slate-400 max-w-xl mx-auto leading-relaxed">
          Compare original agreements and amendments side-by-side. Automatically extract clauses, check soft validations, categorize legal topics, and grade risks with localized visual OCR agents.
        </p>
      </div>

      {/* Primary Actions */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-4 w-full">
        <Link
          href="/analyses"
          className="w-full sm:w-auto flex items-center justify-center gap-2 font-bold bg-indigo-600 hover:bg-indigo-500 text-white px-8 py-3.5 rounded-xl shadow-lg shadow-indigo-600/15 transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          Access Dashboard
          <ArrowRight className="w-4 h-4" />
        </Link>
        <Link
          href="/analyses/new"
          className="w-full sm:w-auto flex items-center justify-center gap-2 font-bold border border-slate-800 text-slate-300 hover:text-slate-100 hover:bg-slate-900 px-8 py-3.5 rounded-xl transition-all"
        >
          <Sparkles className="w-4 h-4" />
          Analyze New Contract
        </Link>
      </div>

      {/* Key highlights checklist grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-12 text-left w-full border-t border-slate-900/60">
        <div className="bg-slate-900/10 border border-slate-900 p-5 rounded-2xl space-y-2">
          <div className="w-8 h-8 rounded-xl bg-indigo-500/5 flex items-center justify-center text-indigo-400 border border-indigo-500/15">
            <FileSearch className="w-4 h-4" />
          </div>
          <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Side-by-side Diffs</h4>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            See exactly what modified, added, or deleted clauses look like compared to original contract sections.
          </p>
        </div>

        <div className="bg-slate-900/10 border border-slate-900 p-5 rounded-2xl space-y-2">
          <div className="w-8 h-8 rounded-xl bg-indigo-500/5 flex items-center justify-center text-indigo-400 border border-indigo-500/15">
            <Sparkles className="w-4 h-4" />
          </div>
          <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Operational Risks</h4>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Instantly catch Critical and High threat alterations (such as unilateral IP transfer or net payment stretches).
          </p>
        </div>

        <div className="bg-slate-900/10 border border-slate-900 p-5 rounded-2xl space-y-2">
          <div className="w-8 h-8 rounded-xl bg-indigo-500/5 flex items-center justify-center text-indigo-400 border border-indigo-500/15">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider">Grounded Evidence</h4>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            AI-extracted quotes are paired with specific contract page indicators for high-confidence manual audit.
          </p>
        </div>
      </div>
    </div>
  );
}
