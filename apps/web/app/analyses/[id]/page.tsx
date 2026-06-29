import { AnalysisDetailClient } from '@/features/analyses/analysis-detail-client';

export function generateStaticParams() {
  return [{ id: '_' }];
}

export default function AnalysisDetailPage() {
  return <AnalysisDetailClient />;
}
