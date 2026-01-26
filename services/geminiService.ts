import { sendChat } from "./chatApi";

export async function generateAcademicResponse(message: string, sessionId?: string) {
  const res = await sendChat(message, sessionId);
  return { text: res.answer, sources: res.sources };
}
