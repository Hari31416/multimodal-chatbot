export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  modality: "text" | "vision" | "data";
  artifacts?: any | null;
  // For vision/user messages we can carry a local preview URL (object URL or remote URL)
  imageUrl?: string;
}
