import { ApiClientError } from './api-client';
import { UX_MESSAGES } from './ux-messages';

function isNetworkOrCorsMessage(message: string): boolean {
  const lower = message.toLowerCase();
  return (
    lower === 'failed to fetch' ||
    lower.includes('networkerror') ||
    lower.includes('network connection error') ||
    lower.includes('load failed')
  );
}

/**
 * Converts API/network errors into user-friendly messages.
 * Detects likely CORS or connectivity issues generically.
 */
export function formatApiError(
  err: unknown,
  fallback: string = UX_MESSAGES.error.generic
): string {
  if (err instanceof ApiClientError) {
    if (err.status === 0 || isNetworkOrCorsMessage(err.message)) {
      return UX_MESSAGES.error.apiOffline;
    }
    return err.message || fallback;
  }

  if (err instanceof TypeError && isNetworkOrCorsMessage(err.message)) {
    return UX_MESSAGES.error.apiOffline;
  }

  if (err instanceof Error) {
    if (isNetworkOrCorsMessage(err.message)) {
      return UX_MESSAGES.error.apiOffline;
    }
    return err.message;
  }

  return fallback;
}
