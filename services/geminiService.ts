import { sendChat } from "./chatApi";

export async function generateAcademicResponse(message: string, sessionId?: string) {
  const res = await sendChat(message, sessionId ?? "guest_session");
  return { text: res.answer, sources: res.sources };
}
