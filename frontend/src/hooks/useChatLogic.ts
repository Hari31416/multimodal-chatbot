import { useState } from "react";
import { postJSON, postForm, getJSON } from "../api/client";
import { ChatMessage } from "../types/chat";

interface BackendMessage {
  role: string;
  content: any; // may be string or multimodal array
}

export const useChatLogic = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string>("");
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [columns, setColumns] = useState<string[]>([]);
  const [head, setHead] = useState<any[][]>([]);

  function pushMessage(partial: Omit<ChatMessage, "id">) {
    setMessages((m) => [
      ...m,
      {
        id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        ...partial,
      },
    ]);
  }

  function loadSessionMessages(
    sessionId: string,
    backendMessages: BackendMessage[]
  ) {
    const converted: ChatMessage[] = backendMessages.map((msg, index) => {
      let modality: ChatMessage["modality"] = "text";
      let content: string = "";
      let imageUrl: string | undefined;
      let code: string | undefined;
      let artifact: ChatMessage["artifact"]; // possibly undefined

      if (Array.isArray(msg.content)) {
        // Vision style content: list of parts
        const textPart = msg.content.find((p: any) => p?.type === "text");
        const imagePart = msg.content.find((p: any) => p?.type === "image_url");
        content = textPart?.text || "";
        if (imagePart?.image_url?.url) {
          modality = "vision";
          imageUrl = imagePart.image_url.url; // data URL
        }
      } else if (typeof msg.content === "string") {
        // Try to detect serialized analysis object
        const rawStr = msg.content.trim();
        let parsed: any = null;
        if (rawStr.startsWith("{") && rawStr.endsWith("}")) {
          try {
            parsed = JSON.parse(rawStr);
          } catch {
            // not valid JSON, treat as plain string
          }
        }
        if (
          parsed &&
          typeof parsed.explanation === "string" &&
          (typeof parsed.code === "string" || typeof parsed.plot === "string")
        ) {
          modality = "data";
          content = parsed.explanation;
          if (typeof parsed.code === "string" && parsed.code.trim()) {
            code = parsed.code;
          }
          // Ignore plot/image for history per requirement
        } else {
          content = msg.content;
        }
      } else if (msg.content && typeof msg.content === "object") {
        // Data analysis history object pattern: { explanation, code?, plot? }
        const c: any = msg.content;
        const hasAnalysisShape =
          typeof c.explanation === "string" &&
          (typeof c.code === "string" || typeof c.plot === "string");
        if (hasAnalysisShape) {
          modality = "data";
          content = c.explanation;
          if (typeof c.code === "string" && c.code.trim()) {
            code = c.code;
          }
          // Ignore plot artifact in history objects per requirement
        } else {
          // Fallback: stringifiable object
          try {
            content = JSON.stringify(msg.content);
          } catch {
            content = String(msg.content);
          }
        }
      }

      return {
        id: `${sessionId}-${index}`,
        role: (msg.role as "user" | "assistant") || "assistant",
        content,
        modality,
        imageUrl,
        code,
        artifact,
      } as ChatMessage;
    });

    setMessages(converted);
    setSessionId(sessionId);
    setInput("");
    setError("");
    setImageFile(null);
    setCsvFile(null);
    setPending(false);
  }

  async function handleNewChat() {
    setMessages([]);
    setInput("");
    setError("");
    setImageFile(null);
    setCsvFile(null);
    setColumns([]);
    setHead([]);
    setPending(false);
    try {
      const res = await getJSON<{ sessionId: string }>("/start-new-chat");
      setSessionId(res.sessionId);
    } catch (e: any) {
      // If we can't start a new chat, leave session null but surface error
      setError("Failed to start new chat: " + e.message);
      setSessionId(null);
    }
  }

  async function handleSend() {
    if (!input.trim()) return;
    setError("");

    // Ensure we have a sessionId for continuity; create lazily if absent
    let activeSession = sessionId;
    if (!activeSession) {
      try {
        const res = await getJSON<{ sessionId: string }>("/start-new-chat");
        activeSession = res.sessionId;
        setSessionId(res.sessionId);
      } catch (e: any) {
        // Non-fatal for plain text / vision chat, we can proceed without session
        console.warn("Could not obtain sessionId", e);
      }
    }

    const userModality: ChatMessage["modality"] = imageFile
      ? "vision"
      : activeSession && (columns.length > 0 || head.length > 0)
      ? "data"
      : "text";

    // If there's an image, create an object URL for thumbnail preview
    let imageUrl: string | undefined;
    if (imageFile) {
      try {
        imageUrl = URL.createObjectURL(imageFile);
      } catch (e) {
        console.warn("Failed to create object URL for image", e);
      }
    }

    pushMessage({
      role: "user",
      content: input,
      modality: userModality,
      imageUrl,
    });

    setPending(true);
    const currentInput = input;
    const currentImage = imageFile;
    setInput("");
    setImageFile(null);

    try {
      if (currentImage) {
        const form = new FormData();
        // Backend /vision-chat now expects 'message' instead of 'prompt'
        form.append("message", currentInput);
        if (activeSession) form.append("sessionId", activeSession);
        form.append("image", currentImage);
        const res = await postForm<{ reply: string }>("/vision-chat", form);
        pushMessage({
          role: "assistant",
          content: res.reply,
          modality: "vision",
        });
      } else if (userModality === "data" && activeSession) {
        // Backend expects: { sessionId, message }
        const res = await postJSON<{
          reply: string;
          code: string | null;
          artifact: string | null;
          artifact_is_mime_type: boolean;
        }>("/analyze", {
          sessionId: activeSession,
          message: currentInput,
        });

        // Normalize artifact: if mime type -> treat as chart; else textual
        const isImage =
          !!res.artifact_is_mime_type && typeof res.artifact === "string";
        const normalizedArtifacts = isImage
          ? { chart: res.artifact, raw: res.artifact, isMime: true }
          : res.artifact
          ? {
              text: String(res.artifact),
              raw: String(res.artifact),
              isMime: false,
            }
          : null;

        pushMessage({
          role: "assistant",
          content: res.reply,
          modality: "data",
          artifact: normalizedArtifacts,
          code: res.code || undefined,
        });
      } else {
        const res = await postJSON<{ reply: string }>("/chat", {
          message: currentInput,
          sessionId: activeSession,
        });
        pushMessage({
          role: "assistant",
          content: res.reply,
          modality: "text",
        });
      }
    } catch (err: any) {
      pushMessage({
        role: "assistant",
        content: "Error: " + err.message,
        modality: "text",
      });
    } finally {
      setPending(false);
    }
  }

  async function handleCsvUpload(file?: File) {
    const f = file || csvFile;
    if (!f) return;
    setError("");

    try {
      const form = new FormData();
      form.append("file", f);
      const res = await postForm<{
        sessionId: string;
        columns: string[];
        headPreview: any[][];
      }>("/upload-csv", form);

      setSessionId(res.sessionId);
      setColumns(res.columns);
      setHead(res.headPreview);

      pushMessage({
        role: "assistant",
        content: `CSV uploaded. Session ${res.sessionId.slice(
          0,
          8
        )}… Data analysis mode enabled.`,
        modality: "data",
      });

      setCsvFile(null);
    } catch (err: any) {
      setError(err.message);
    }
  }

  return {
    messages,
    input,
    setInput,
    pending,
    error,
    imageFile,
    setImageFile,
    csvFile,
    setCsvFile,
    sessionId,
    columns,
    head,
    handleNewChat,
    handleSend,
    handleCsvUpload,
    loadSessionMessages,
  };
};
