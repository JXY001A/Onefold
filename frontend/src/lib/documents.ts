import { apiRequest as request } from "./http";

export type Doc = {
  id: string;
  kb_id: string | null;
  scope: "public" | "personal" | "temp";
  filename: string;
  size: number;
  kind: string;
  status: string;
  error: string | null;
  page_count: number | null;
  chunk_count: number;
  expires_at: string | null;
};

export function fetchPersonalDocs(): Promise<Doc[]> {
  return request<Doc[]>("/api/documents");
}

export function fetchPublicDocs(): Promise<Doc[]> {
  return request<Doc[]>("/api/knowledge/public/documents");
}

export async function uploadDoc(file: File, scope: "personal" | "public"): Promise<Doc> {
  const body = new FormData();
  body.append("file", file);
  const url = scope === "public"
    ? "/api/knowledge/public/documents"
    : "/api/documents";
  return request<Doc>(url, { method: "POST", body });
}

export async function deleteDoc(doc: Doc): Promise<void> {
  const url = doc.scope === "public"
    ? `/api/knowledge/public/documents/${doc.id}`
    : `/api/documents/${doc.id}`;
  await request(url, { method: "DELETE" });
}

export async function collectDoc(id: string): Promise<void> {
  await request(`/api/documents/${id}/collect`, { method: "POST" });
}

export async function retryDoc(doc: Doc): Promise<void> {
  const url = doc.scope === "public"
    ? `/api/knowledge/public/documents/${doc.id}/retry`
    : `/api/documents/${doc.id}/retry`;
  await request(url, { method: "POST" });
}

export async function publishDoc(id: string): Promise<Doc> {
  return request<Doc>(`/api/knowledge/public/publish/${id}`, { method: "POST" });
}
