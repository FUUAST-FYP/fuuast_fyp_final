export interface KnowledgeEntry {
  id: string;
  category: string;
  content: string;
  sourceDocument?: string;
  pageNumber?: number;
}

export type SourceRef = {
  label: string;
  url?: string;
  sourceDocument?: string;
  pageNumber?: number;
};

export interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: Date;
  sources?: SourceRef[];
}
