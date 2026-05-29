import Link from 'next/link';
import { PageHeader } from '@/components/page-header';
import { UploadAnalysisForm } from '@/features/analyses/upload-analysis-form';
import { ArrowLeft, HelpCircle } from 'lucide-react';

export default function NewAnalysisPage() {
  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
      {/* Back to dashboard */}
      <div>
        <Link
          href="/analyses"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors group"
        >
          <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
          Back to Dashboard
        </Link>
      </div>

      {/* Visual Page Header */}
      <PageHeader
        title="New AI-assisted analysis"
        description="Upload an original contract and its amendment. Outputs support human review — they are not legal advice."
      />

      {/* Upload Form */}
      <UploadAnalysisForm />

      {/* Auxiliary Help block */}
      <div className="flex items-start gap-3 bg-slate-900/10 border border-slate-900 p-4 rounded-xl text-xs text-slate-500 leading-relaxed">
        <HelpCircle className="w-4 h-4 text-slate-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-1 text-left">
          <p className="font-semibold text-slate-300">What happens after upload?</p>
          <p className="text-[11px]">
            Documents are stored and an AI-assisted analysis job is queued. When processing
            finishes, you can review extracted changes on the detail page. Always verify findings
            with a qualified human before acting on them.
          </p>
        </div>
      </div>
    </div>
  );
}
