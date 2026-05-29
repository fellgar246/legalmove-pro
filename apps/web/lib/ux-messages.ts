/** Centralized UX copy for LegalMove Pro MVP. */

export const UX_MESSAGES = {
  loading: {
    analysesList: 'Loading your AI-assisted analyses…',
    analysisJob: 'Loading analysis details…',
    analysisResult: 'Loading AI-assisted analysis results…',
    upload: 'Uploading documents and starting AI-assisted analysis…',
    processing: 'Running AI-assisted analysis on your documents…',
  },
  error: {
    apiOffline:
      'Unable to reach the API. Make sure the backend is running at localhost:8080 and CORS allows this app.',
    uploadFailed: 'Upload failed. Check your files and try again.',
    createAnalysisFailed:
      'Could not start the AI-assisted analysis. Please try again.',
    analysisFailed: 'The AI-assisted analysis could not be completed.',
    resultNotAvailable:
      'Results are not available yet. The analysis may still be finishing — try refreshing in a moment.',
    generic: 'Something went wrong. Please try again.',
    notFound: 'This analysis was not found.',
  },
  empty: {
    noAnalyses: {
      title: 'No analyses yet',
      description:
        'Upload an original contract and its amendment to start your first AI-assisted analysis. All outputs should be reviewed by a qualified human.',
    },
    noChanges: {
      title: 'No changes detected',
      description:
        'The AI-assisted analysis did not identify any differences between the documents.',
    },
    noWarnings: {
      title: 'No validation warnings',
      description: 'The analysis output passed validation checks.',
    },
    noRecommendations: {
      title: 'No specific recommendations',
      description:
        'No additional human review steps were suggested. Review the findings yourself before acting on them.',
    },
    noFilteredChanges: {
      title: 'No matching changes',
      description: 'Try adjusting your search or filters.',
    },
  },
  disclaimer:
    'AI-generated review support. Not legal advice. All outputs should be reviewed by a qualified human.',
} as const;
