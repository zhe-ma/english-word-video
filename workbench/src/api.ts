const j = async <T>(r: Response): Promise<T> => {
  const data = await r.json();
  if (!r.ok) throw new Error((data as { error?: string }).error || r.statusText);
  return data as T;
};

export const api = {
  get: <T>(url: string) => fetch(url).then((r) => j<T>(r)),
  send: <T>(url: string, method: string, body?: unknown) =>
    fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    }).then((r) => j<T>(r)),
};

export const media = (url?: string | null) => (url ? `/${url}` : "");
