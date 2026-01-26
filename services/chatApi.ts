export type ChatApiSource =
  | { label: string; url?: string; sourceDocument?: string; pageNumber?: number };

export async function sendChat(message: string, session_id = "guest_session") {
  const res = await fetch(`/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id, top_k: 3 }),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Chat API failed: ${res.status} ${txt}`);
  }

  return (await res.json()) as {
    status: string;
    timestamp: string;
    answer: string;
    sources: ChatApiSource[];
  };
}
