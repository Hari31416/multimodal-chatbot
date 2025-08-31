import { useState } from "react";
import { ChatMessage } from "../../types/chat";
import {
  ChatState,
  ChatActions,
  UploadedImageArtifact,
  UploadedCsvArtifact,
  UploadProgress,
} from "./types";

export function useChatState(): ChatState & ChatActions {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string>("");
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [columns, setColumns] = useState<string[]>([]);
  const [head, setHead] = useState<any[][]>([]);
  const [uploadedArtifactIds, setUploadedArtifactIds] = useState<string[]>([]);
  const [hasUploadedImages, setHasUploadedImages] = useState(false);
  const [uploadedImageArtifacts, setUploadedImageArtifacts] = useState<
    UploadedImageArtifact[]
  >([]);
  const [uploadedCsvArtifact, setUploadedCsvArtifact] =
    useState<UploadedCsvArtifact | null>(null);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});

  return {
    messages,
    input,
    pending,
    error,
    csvFile,
    sessionId,
    columns,
    head,
    uploadedArtifactIds,
    hasUploadedImages,
    uploadedImageArtifacts,
    uploadedCsvArtifact,
    uploadProgress,
    setMessages,
    setInput,
    setPending,
    setError,
    setCsvFile,
    setSessionId,
    setColumns,
    setHead,
    setUploadedArtifactIds,
    setHasUploadedImages,
    setUploadedImageArtifacts,
    setUploadedCsvArtifact,
    setUploadProgress,
  };
}
