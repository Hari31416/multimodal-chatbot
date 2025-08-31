import { postForm, getJSON } from "../../api/client";
import { ChatMessage } from "../../types/chat";
import { ChatActions, BackendMessage } from "./types";
import {
  generateMessageId,
  convertBackendMessage,
  extractCsvDataFromSession,
  extractArtifactIdsFromSession,
  ensureSessionExists,
} from "./utils";

interface UseMessageHandlingProps {
  actions: ChatActions;
  sessionId: string | null;
  setSessionId: (sessionId: string) => void;
}

export function useMessageHandling({
  actions,
  sessionId,
  setSessionId,
}: UseMessageHandlingProps) {
  const {
    messages,
    setMessages,
    input,
    setInput,
    setPending,
    setError,
    uploadedArtifactIds,
    uploadedImageArtifacts,
    columns,
    setUploadedArtifactIds,
    setHasUploadedImages,
    setUploadedImageArtifacts,
    setUploadedCsvArtifact,
  } = actions;

  function pushMessage(partial: Omit<ChatMessage, "id">) {
    setMessages((m) => [
      ...m,
      {
        id: generateMessageId(),
        ...partial,
      },
    ]);
  }

  function loadSessionMessages(
    sessionId: string,
    backendMessages: BackendMessage[]
  ) {
    // Filter out system messages - only show user and assistant messages
    const filteredMessages = backendMessages.filter(
      (msg) => msg.role === "user" || msg.role === "assistant"
    );

    const converted: ChatMessage[] = filteredMessages.map((msg, index) =>
      convertBackendMessage(msg, index, sessionId)
    );

    // Extract CSV data from session
    extractCsvDataFromSession(
      backendMessages,
      actions.setColumns,
      actions.setHead,
      setUploadedCsvArtifact
    );

    // Extract all artifact IDs from the session
    const { allArtifactIds, sessionHasImages } =
      extractArtifactIdsFromSession(backendMessages);

    setUploadedArtifactIds(allArtifactIds);
    setHasUploadedImages(sessionHasImages);

    setMessages(converted);
    setSessionId(sessionId);
    setInput("");
    setError("");
    actions.setCsvFile(null);
    setUploadedArtifactIds([]);
    setUploadedImageArtifacts([]);
    setUploadedCsvArtifact(null);
    actions.setUploadProgress({});
    setPending(false);
  }

  async function handleNewChat() {
    setMessages([]);
    setInput("");
    setError("");
    actions.setCsvFile(null);
    actions.setColumns([]);
    actions.setHead([]);
    setUploadedArtifactIds([]);
    setHasUploadedImages(false);
    setUploadedImageArtifacts([]);
    setUploadedCsvArtifact(null);
    actions.setUploadProgress({});
    setPending(false);

    try {
      // Use fixed user_id for now - in production this would come from auth
      const res = await getJSON<{ sessionId: string }>(
        "/sessions/new?user_id=default_user"
      );
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

    // Ensure we have a sessionId for continuity; create if absent
    const activeSession = await ensureSessionExists(
      sessionId,
      setSessionId,
      setError,
      "sending message"
    );

    if (!activeSession) {
      return; // Abort the send operation if session creation failed
    }

    const userModality: ChatMessage["modality"] = uploadedArtifactIds.some(
      (id) =>
        // We'll check if any uploaded artifacts are images by making a simple assumption
        // In practice, we could track artifact types separately
        true // For now, assume mixed content
    )
      ? columns.length > 0
        ? "data"
        : "vision"
      : "text";

    // Create image preview URLs for the user message if images are uploaded
    let imageUrl: string | undefined;
    let imageUrls: string[] = [];
    if (uploadedImageArtifacts.length > 0) {
      // Use the first image as the main preview for backwards compatibility
      const firstImage = uploadedImageArtifacts[0];
      imageUrl = `data:image/png;base64,${firstImage.data}`;

      // Create URLs for all images
      imageUrls = uploadedImageArtifacts.map(
        (artifact) => `data:image/png;base64,${artifact.data}`
      );
    }

    // Store current uploaded artifacts before clearing
    const currentUploadedArtifacts = [...uploadedImageArtifacts];
    const currentArtifactIds = [...uploadedArtifactIds];

    pushMessage({
      role: "user",
      content: input,
      modality: userModality,
      imageUrl,
      imageUrls: imageUrls.length > 0 ? imageUrls : undefined,
    });

    setPending(true);
    const currentInput = input;
    setInput("");

    // Clear uploaded artifacts after adding to user message
    setUploadedImageArtifacts([]);
    setUploadedArtifactIds([]);
    setHasUploadedImages(false);
    setUploadedCsvArtifact(null);

    try {
      // Use the unified chat endpoint
      const form = new FormData();
      form.append("message", currentInput);
      form.append("user_id", "default_user");
      if (activeSession) form.append("session_id", activeSession);

      // Send uploaded artifact IDs that should be used for this message
      if (currentArtifactIds.length > 0) {
        // Backend expects comma-separated artifact IDs
        form.append("artifact_ids", currentArtifactIds.join(","));
      }

      const res = await postForm<{
        messageId: string;
        sessionId: string;
        role: string;
        timestamp: string;
        content: string;
        artifacts: any[];
      }>("/chat/", form);

      // Check if there are artifacts to display
      let normalizedArtifacts = null;
      let code: string | undefined;
      let responseModality: ChatMessage["modality"] = "text";

      if (res.artifacts && res.artifacts.length > 0) {
        // Process all artifacts, not just the first one
        for (const art of res.artifacts) {
          if (art.type === "code") {
            code = art.content || art.data;
            responseModality = "data";
          } else if (art.type === "chart") {
            normalizedArtifacts = normalizedArtifacts || {
              chart: art.data || art.content,
              raw: art.data || art.content,
              isMime: true,
            };
            responseModality = "data";
          } else if (art.type === "image") {
            // Handle image artifacts with proper data URL formatting
            let imageData = art.data || art.content;
            if (imageData && !imageData.startsWith("data:")) {
              // Determine the image format from the artifact or default to png
              const format = art.format ? art.format.toLowerCase() : "png";
              const mimeType =
                format === "png"
                  ? "image/png"
                  : format === "gif"
                  ? "image/gif"
                  : format === "webp"
                  ? "image/webp"
                  : format === "jpeg" || format === "jpg"
                  ? "image/jpeg"
                  : "image/png"; // Default to PNG as specified
              imageData = `data:${mimeType};base64,${imageData}`;
            }
            normalizedArtifacts = normalizedArtifacts || {
              chart: imageData,
              raw: imageData,
              isMime: true,
            };
            responseModality = "data";
          } else if (art.type === "text") {
            normalizedArtifacts = normalizedArtifacts || {
              text: art.data || art.content,
              raw: art.data || art.content,
              isMime: false,
            };
            responseModality = "data";
          }
        }
      }

      // If we had uploaded images, it might be a vision response
      if (currentArtifactIds.length > 0 && userModality === "vision") {
        responseModality = "vision";
      }

      pushMessage({
        role: "assistant",
        content: res.content,
        modality: responseModality,
        artifact: normalizedArtifacts,
        code: code,
      });
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

  return {
    pushMessage,
    loadSessionMessages,
    handleNewChat,
    handleSend,
  };
}
