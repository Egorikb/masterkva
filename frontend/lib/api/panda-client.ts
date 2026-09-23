import type { PandaChatRequest, PandaChatResponse } from "@/contracts/panda";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";
const PANDA_CHAT_PATH = "/api/v1/plugins/panda/chat";

export class PandaApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message);
    this.name = "PandaApiError";
  }
}

export async function postPandaChat(payload: PandaChatRequest): Promise<PandaChatResponse> {
  const response = await fetch(`${API_BASE_URL}${PANDA_CHAT_PATH}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: { code?: string } } | null;
    throw new PandaApiError(
      `Panda chat request failed with status ${response.status}`,
      response.status,
      body?.detail?.code,
    );
  }

  return (await response.json()) as PandaChatResponse;
}
