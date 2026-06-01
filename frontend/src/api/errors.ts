type FastApiValidationError = {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
};

function formatValidationError(error: FastApiValidationError): string {
  const field = error.loc?.filter((part) => part !== 'body').join('.');
  if (field && error.msg) {
    return `${field}: ${error.msg}`;
  }
  return error.msg || 'Некорректные данные';
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!error || typeof error !== 'object') {
    return fallback;
  }

  const response = (error as { response?: { data?: unknown } }).response;
  const data = response?.data;

  if (!data) {
    return fallback;
  }

  if (typeof data === 'string') {
    return data;
  }

  if (typeof data === 'object' && 'detail' in data) {
    const detail = (data as { detail?: unknown }).detail;

    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item) => {
          if (typeof item === 'string') return item;
          if (item && typeof item === 'object') return formatValidationError(item as FastApiValidationError);
          return 'Некорректные данные';
        })
        .join('; ');
    }
  }

  return fallback;
}
