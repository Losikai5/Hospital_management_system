type ApiRequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  // Authentication is handled by the same-origin proxy's HTTP-only cookies.
  // Keep this option for call-site compatibility with the existing UI.
  authenticated?: boolean;
};

function errorMessage(payload: unknown, fallback: string) {
  if (typeof payload === "string" && payload) return payload;
  if (payload && typeof payload === "object") {
    const data = payload as Record<string, unknown>;
    if (typeof data.error === "string") return data.error;
    if (typeof data.detail === "string") return data.detail;
    const firstValue = Object.values(data)[0];
    if (Array.isArray(firstValue) && typeof firstValue[0] === "string") return firstValue[0];
  }
  return fallback;
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { body, headers, authenticated, ...requestOptions } = options;
  void authenticated;
  const hasBody = body !== undefined;
  const response = await fetch(`/api/backend${path}`, {
    ...requestOptions,
    headers: {
      Accept: "application/json",
      ...(hasBody ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: hasBody ? JSON.stringify(body) : undefined,
    credentials: "same-origin",
  });

  if (response.status === 204 || response.status === 205) return undefined as T;

  const text = await response.text();
  let payload: unknown = text;
  try {
    payload = text ? JSON.parse(text) : undefined;
  } catch {
    // Keep non-JSON responses as text so their message can be surfaced.
  }
  if (!response.ok) throw new Error(errorMessage(payload, `Request failed (${response.status})`));
  return payload as T;
}

export async function apiDownload(path: string, filename: string) {
  const response = await fetch(`/api/backend${path}`, { credentials: "same-origin" });
  if (!response.ok) throw new Error(`Download failed (${response.status})`);
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
