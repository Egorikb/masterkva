import type { PandaChatRequest, PandaChatResponse } from "@/contracts/panda";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001";
const PANDA_CHAT_PATH = "/api/v1/plugins/panda/chat";

export async function postPandaChat(payload: PandaChatRequest): Promise<PandaChatResponse> {
  const response = await fetch(`${API_BASE_URL}${PANDA_CHAT_PATH}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Panda chat request failed with status ${response.status}`);
  }

  return (await response.json()) as PandaChatResponse;
}
