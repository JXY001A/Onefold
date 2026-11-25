import { apiRequest } from "./http";

export type Skill = {
  id: string;
  name: string;
  version: string;
  enabled: boolean;
};

const JSON_HEADERS = { "Content-Type": "application/json" };

export function fetchSkills(): Promise<Skill[]> {
  return apiRequest<Skill[]>("/api/skills");
}

export function setSkillEnabled(id: string, enabled: boolean): Promise<unknown> {
  return apiRequest(`/api/skills/${id}/enable`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ enabled }),
  });
}
