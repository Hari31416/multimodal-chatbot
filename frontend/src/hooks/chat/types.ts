import { ChatMessage } from "../../types/chat";

export interface BackendMessage {
  role: string;
  content: any; // may be string or multimodal array
}

export interface UploadedImageArtifact {
  artifactId: string;
  data: string;
  fileName: string;
  description: string;
}

export interface UploadedCsvArtifact {
  artifactId: string;
  fileName: string;
  description: string;
  columns: string[];
  rowCount: number;
}

export interface UploadProgress {
  [fileName: string]: number;
}

export interface ChatState {
  messages: ChatMessage[];
  input: string;
  pending: boolean;
  error: string;
  csvFile: File | null;
  sessionId: string | null;
  columns: string[];
  head: any[][];
  uploadedArtifactIds: string[];
  hasUploadedImages: boolean;
  uploadedImageArtifacts: UploadedImageArtifact[];
  uploadedCsvArtifact: UploadedCsvArtifact | null;
  uploadProgress: UploadProgress;
}

export interface ChatActions {
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  setInput: React.Dispatch<React.SetStateAction<string>>;
  setPending: React.Dispatch<React.SetStateAction<boolean>>;
  setError: React.Dispatch<React.SetStateAction<string>>;
  setCsvFile: React.Dispatch<React.SetStateAction<File | null>>;
  setSessionId: React.Dispatch<React.SetStateAction<string | null>>;
  setColumns: React.Dispatch<React.SetStateAction<string[]>>;
  setHead: React.Dispatch<React.SetStateAction<any[][]>>;
  setUploadedArtifactIds: React.Dispatch<React.SetStateAction<string[]>>;
  setHasUploadedImages: React.Dispatch<React.SetStateAction<boolean>>;
  setUploadedImageArtifacts: React.Dispatch<
    React.SetStateAction<UploadedImageArtifact[]>
  >;
  setUploadedCsvArtifact: React.Dispatch<
    React.SetStateAction<UploadedCsvArtifact | null>
  >;
  setUploadProgress: React.Dispatch<React.SetStateAction<UploadProgress>>;
  csvFile: File | null;
  uploadedImageArtifacts: UploadedImageArtifact[];
  uploadedCsvArtifact: UploadedCsvArtifact | null;
}
