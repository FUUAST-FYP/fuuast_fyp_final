export type ChatApiSource =
  | { label: string; url?: string; sourceDocument?: string; pageNumber?: number };

export type ChatHistoryTurn = { role: "user" | "assistant"; text: string };

export async function sendChat(
  message: string,
  session_id = "guest_session",
  history: ChatHistoryTurn[] = []
) {
  const isHeavyQuery = /(fee|structure|merit|result|admission|convocation|schedule|timetable|availability|teacher|bscs|bs\s*computer)/i.test(message);
  const top_k = isHeavyQuery ? 6 : 4;

  const res = await fetch(`/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id, top_k, history }),
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Chat API failed: ${res.status} ${txt}`);
  }

  return (await res.json()) as {
    status: string;
    timestamp: string;
    answer: string;
    sources: { label: string; url?: string; sourceDocument?: string; pageNumber?: number }[];
  };
}
