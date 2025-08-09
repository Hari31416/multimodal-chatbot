export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  modality: "text" | "vision" | "data";
  artifacts?: any | null;
}
