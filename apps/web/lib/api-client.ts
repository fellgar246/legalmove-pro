const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080';

export class ApiClientError extends Error {
  status: number;
  body: any;

  constructor(message: string, status: number, body?: any) {
    super(message);
    this.name = 'ApiClientError';
    this.status = status;
    this.body = body;
  }
}

async function request<T>(endpoint: string, options: RequestInit): Promise<T> {
  const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  try {
    const response = await fetch(url, options);

    // If HTTP status is not ok (2xx), parse body errors and throw ApiClientError
    if (!response.ok) {
      let errorMessage = `API request failed with status ${response.status}`;
      let errorBody: any = null;

      try {
        errorBody = await response.json();
        if (errorBody && errorBody.error) {
          errorMessage = errorBody.error;
        }
      } catch {
        // Fall back if response isn't JSON
        try {
          const text = await response.text();
          if (text) {
            errorMessage = text;
          }
        } catch {
          // Fall back to default message
        }
      }

      throw new ApiClientError(errorMessage, response.status, errorBody);
    }

    // Handle No Content (244 / 204 status codes)
    if (response.status === 204) {
      return {} as T;
    }

    // Try parsing JSON response
    return await response.json();
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error;
    }
    const message = error instanceof Error ? error.message : 'Network connection error';
    throw new ApiClientError(message, 0);
  }
}

export const apiClient = {
  get: <T>(endpoint: string, options?: Omit<RequestInit, 'method'>) => {
    return request<T>(endpoint, {
      ...options,
      method: 'GET',
    });
  },

  postJson: <T>(endpoint: string, body: any, options?: Omit<RequestInit, 'method' | 'body'>) => {
    const headers = new Headers(options?.headers);
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json');
    }

    return request<T>(endpoint, {
      ...options,
      headers,
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  postFormData: <T>(endpoint: string, formData: FormData, options?: Omit<RequestInit, 'method' | 'body'>) => {
    // Note: Do NOT set Content-Type header here manually. Let the browser handle boundary insertion automatically.
    return request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: formData,
    });
  },
};
