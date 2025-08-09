import { useState } from "react";
import { postJSON, postForm } from "../api/client";
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

  function handleNewChat() {
    setMessages([]);
    setInput("");
    setError("");
    setImageFile(null);
    setCsvFile(null);
    setSessionId(null);
    setColumns([]);
    setHead([]);
    setPending(false);
  }

  async function handleSend() {
    if (!input.trim()) return;
    setError("");

    const userModality: ChatMessage["modality"] = imageFile
      ? "vision"
      : sessionId
      ? "data"
      : "text";

    pushMessage({
      role: "user",
      content: input + (imageFile ? " [image]" : ""),
      modality: userModality,
    });

    setPending(true);
    const currentInput = input;
    const currentImage = imageFile;
    setInput("");
    setImageFile(null);

    try {
      if (currentImage) {
        const form = new FormData();
        form.append("prompt", currentInput);
        form.append("image", currentImage);
        const res = await postForm<{ reply: string }>("/vision-chat", form);
        pushMessage({
          role: "assistant",
          content: res.reply,
          modality: "vision",
        });
      } else if (userModality === "data" && sessionId) {
        const res = await postJSON<{ answer: string; artifacts?: any }>(
          "/analyze",
          {
            sessionId,
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
