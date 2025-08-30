export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  modality: "text" | "vision" | "data";
  /**
   * For data / analysis responses we normalize artifact into a simple shape.
   * chart: data URI for image based plot
   * text: textual artifact (stringified result) when not a plot
   * raw: original raw backend artifact string (for debugging / future use)
   * isMime: whether backend indicated artifact was a mime/image
   */
  artifact?: {
    chart?: string;
    text?: string;
    raw?: string;
    isMime?: boolean;
  } | null;
  /** Optional python code returned from /analyze */
  code?: string;
  // For vision/user messages we can carry a local preview URL (object URL or remote URL)
  imageUrl?: string;
  // For multiple images in user messages
  imageUrls?: string[];
}
