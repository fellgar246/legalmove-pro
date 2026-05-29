import { AnalysisDetailClient } from '@/features/analyses/analysis-detail-client';

interface AnalysisDetailPageProps {
  params: {
    id: string;
  };
}

export default function AnalysisDetailPage({ params }: AnalysisDetailPageProps) {
  return <AnalysisDetailClient analysisId={params.id} />;
}
