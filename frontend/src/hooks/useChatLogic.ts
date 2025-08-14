import { useState } from "react";
import { postJSON, postForm, getJSON } from "../api/client";
import { ChatMessage } from "../types/chat";

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
        const res = await postJSON<{ answer: string; artifacts?: any }>(
          "/analyze",
          {
            sessionId: activeSession,
            question: currentInput,
          }
        );
        pushMessage({
          role: "assistant",
          content: res.answer,
          modality: "data",
          artifacts: res.artifacts || null,
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
  };
};
