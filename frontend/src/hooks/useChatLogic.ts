import { useState } from "react";
import { postJSON, postForm, getJSON, API_BASE_URL } from "../api/client";
import { ChatMessage } from "../types/chat";

interface BackendMessage {
  role: string;
  content: any; // may be string or multimodal array
}

// Helper function to convert image file to base64
async function convertImageToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Remove the data:image/...;base64, prefix
      const base64 = result.split(",")[1];
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export const useChatLogic = () => {
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
    Array<{
      artifactId: string;
      data: string;
      fileName: string;
      description: string;
    }>
  >([]);
  const [uploadedCsvArtifact, setUploadedCsvArtifact] = useState<{
    artifactId: string;
    fileName: string;
    description: string;
    columns: string[];
    rowCount: number;
  } | null>(null);
  const [uploadProgress, setUploadProgress] = useState<{
    [fileName: string]: number;
  }>({});

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
    // Filter out system messages - only show user and assistant messages
    const filteredMessages = backendMessages.filter(
      (msg) => msg.role === "user" || msg.role === "assistant"
    );

    const converted: ChatMessage[] = filteredMessages.map((msg, index) => {
      let modality: ChatMessage["modality"] = "text";
      let content: string = "";
      let imageUrl: string | undefined;
      let imageUrls: string[] = [];
      let code: string | undefined;
      let artifact: ChatMessage["artifact"]; // possibly undefined

      // Check if message has artifacts and extract image/code from them
      if ((msg as any).artifacts && Array.isArray((msg as any).artifacts)) {
        const artifacts = (msg as any).artifacts;
        console.log(
          "Processing message artifacts:",
          artifacts.map((a: any) => ({ type: a.type, hasData: !!a.data }))
        );

        // Look for all image artifacts
        const imageArtifacts = artifacts.filter((a: any) => a.type === "image");

        if (imageArtifacts.length > 0) {
          console.log("Found image artifacts:", {
            count: imageArtifacts.length,
            formats: imageArtifacts.map((a: any) => a.format),
            dataLengths: imageArtifacts.map((a: any) => a.data?.length),
          });
          modality = "vision";

          // Convert all image artifacts to data URLs
          imageUrls = imageArtifacts
            .map((imageArtifact: any) => {
              if (imageArtifact.data) {
                // Check if the data already includes the data URL prefix
                if (imageArtifact.data.startsWith("data:")) {
                  return imageArtifact.data;
                } else {
                  // Determine the image format from the artifact or default to png
                  const format = imageArtifact.format
                    ? imageArtifact.format.toLowerCase()
                    : "png";
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
                  return `data:${mimeType};base64,${imageArtifact.data}`;
                }
              }
              return null;
            })
            .filter((url): url is string => url !== null);

          // Set imageUrl for backward compatibility (first image)
          if (imageUrls.length > 0) {
            imageUrl = imageUrls[0];
          }

          console.log(
            "Generated imageUrls:",
            imageUrls.map((url) => url.substring(0, 100) + "...")
          );
        }

        // Look for code artifacts
        const codeArtifact = artifacts.find((a: any) => a.type === "code");
        if (codeArtifact) {
          code = codeArtifact.data;
          if (modality === "text") modality = "data"; // Only change if not already vision
        }

        // Look for chart artifacts
        const chartArtifact = artifacts.find((a: any) => a.type === "chart");
        if (chartArtifact) {
          modality = "data";
          artifact = {
            chart: chartArtifact.data,
            raw: chartArtifact.data,
            isMime: true,
          };
        }

        // Look for text artifacts
        const textArtifact = artifacts.find((a: any) => a.type === "text");
        if (textArtifact) {
          modality = "data";
          if (artifact) {
            // If we already have a chart artifact, add text to it
            artifact.text = textArtifact.data;
          } else {
            // Create a new artifact with text
            artifact = {
              text: textArtifact.data,
              raw: textArtifact.data,
              isMime: false,
            };
          }
        }
      }

      // Handle the backend message content
      if (typeof msg.content === "string") {
        content = msg.content;

        // Try to detect if this is an analysis response with artifacts
        // Look for patterns that indicate data analysis responses
        if (
          content.includes("analysis") ||
          content.includes("chart") ||
          content.includes("plot")
        ) {
          if (modality === "text") modality = "data"; // Only change if not already vision
        }
      } else if (Array.isArray(msg.content)) {
        // Vision style content: list of parts (for new messages)
        const textPart = msg.content.find((p: any) => p?.type === "text");
        const imageParts = msg.content.filter(
          (p: any) => p?.type === "image_url"
        );
        content = textPart?.text || "";

        if (imageParts.length > 0) {
          modality = "vision";
          imageUrls = imageParts
            .map((part: any) => part.image_url?.url)
            .filter((url): url is string => url != null);

          // Set imageUrl for backward compatibility (first image)
          if (imageUrls.length > 0) {
            imageUrl = imageUrls[0];
          }
        }
      } else if (msg.content && typeof msg.content === "object") {
        // Handle object content - could be analysis results
        const c: any = msg.content;
        if (typeof c.explanation === "string") {
          if (modality === "text") modality = "data"; // Only change if not already vision
          content = c.explanation;
          if (typeof c.code === "string" && c.code.trim()) {
            code = c.code;
          }
          // Handle chart/plot artifacts
          if (c.plot || c.chart) {
            artifact = {
              chart: c.plot || c.chart,
              raw: c.plot || c.chart,
              isMime: true,
            };
          }
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
        imageUrls: imageUrls.length > 0 ? imageUrls : undefined,
        code,
        artifact,
      } as ChatMessage;
    });

    // Check if any message has CSV artifacts and extract column/preview data
    // This will enable the data analysis features when loading sessions with CSV data
    const sessionHasCsvData = filteredMessages.some((msg: any) => {
      return (
        msg.artifacts &&
        msg.artifacts.some((artifact: any) => artifact.type === "csv")
      );
    });

    if (sessionHasCsvData) {
      // Extract CSV data from the first CSV artifact found
      for (const msg of filteredMessages as any[]) {
        if (msg.artifacts) {
          for (const artifact of msg.artifacts) {
            if (artifact.type === "csv" && artifact.data) {
              try {
                // Decode base64 CSV data and extract columns/preview
                const csvContent = atob(artifact.data);
                const lines = csvContent.split("\n");
                const headers = lines[0]
                  .split(",")
                  .map((h: string) => h.trim().replace(/"/g, ""));
                const previewRows = lines
                  .slice(1, 6)
                  .map((line: string) =>
                    line
                      .split(",")
                      .map((cell: string) => cell.trim().replace(/"/g, ""))
                  )
                  .filter((row: string[]) =>
                    row.some((cell: string) => cell.length > 0)
                  );

                setColumns(headers);
                setHead(previewRows);

                // Set uploaded CSV artifact for display
                setUploadedCsvArtifact({
                  artifactId: artifact.artifactId,
                  fileName: artifact.description || "Loaded CSV",
                  description: artifact.description || "CSV data from session",
                  columns: headers,
                  rowCount: lines.length - 1, // Exclude header row
                });

                break;
              } catch (e) {
                console.warn("Could not parse CSV data from artifact:", e);
              }
            }
          }
          if (columns.length > 0) break; // Found CSV data, stop searching
        }
      }
    } else {
      // Clear CSV data if no CSV artifacts found
      setColumns([]);
      setHead([]);
    }

    // Extract all artifact IDs from the session for tracking
    const allArtifactIds: string[] = [];
    let sessionHasImages = false;
    for (const msg of filteredMessages as any[]) {
      if (msg.artifacts) {
        for (const artifact of msg.artifacts) {
          if (artifact.artifactId) {
            allArtifactIds.push(artifact.artifactId);
          }
          if (artifact.type === "image") {
            sessionHasImages = true;
          }
        }
      }
    }
    setUploadedArtifactIds(allArtifactIds);
    setHasUploadedImages(sessionHasImages);

    setMessages(converted);
    setSessionId(sessionId);
    setInput("");
    setError("");
    setCsvFile(null);
    setUploadedArtifactIds([]);
    setUploadedImageArtifacts([]);
    setUploadedCsvArtifact(null);
    setUploadProgress({});
    setPending(false);
  }

  async function handleNewChat() {
    setMessages([]);
    setInput("");
    setError("");
    setCsvFile(null);
    setColumns([]);
    setHead([]);
    setUploadedArtifactIds([]);
    setHasUploadedImages(false);
    setUploadedImageArtifacts([]);
    setUploadedCsvArtifact(null);
    setUploadProgress({});
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

    // Ensure we have a sessionId for continuity; create lazily if absent
    let activeSession = sessionId;
    if (!activeSession) {
      try {
        // Use fixed user_id for now - in production this would come from auth
        const res = await getJSON<{ sessionId: string }>(
          "/sessions/new?user_id=default_user"
        );
        activeSession = res.sessionId;
        setSessionId(res.sessionId);
      } catch (e: any) {
        // Non-fatal for plain text / vision chat, we can proceed without session
        console.warn("Could not obtain sessionId", e);
      }
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

  async function handleCsvUpload(file?: File) {
    const f = file || csvFile;
    if (!f) return;
    setError("");

    try {
      // Initialize progress for this file
      setUploadProgress((prev) => ({ ...prev, [f.name]: 0 }));

      const form = new FormData();
      form.append("file", f);
      form.append("userId", "default_user"); // Use fixed user_id for now

      // Create a new session if we don't have one
      let activeSession = sessionId;
      if (!activeSession) {
        const sessionRes = await getJSON<{ sessionId: string }>(
          "/sessions/new?user_id=default_user"
        );
        activeSession = sessionRes.sessionId;
        setSessionId(activeSession);
      }

      form.append("sessionId", activeSession);

      // Use XMLHttpRequest for progress tracking
      const res = await new Promise<{
        artifactId: string;
        sessionId: string;
        userId: string;
        data: string;
        type: string;
        description: string;
        columns?: string[];
        headPreview?: any[][];
      }>((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener("progress", (event) => {
          if (event.lengthComputable) {
            const percentComplete = Math.round(
              (event.loaded / event.total) * 100
            );
            setUploadProgress((prev) => ({
              ...prev,
              [f.name]: percentComplete,
            }));
          }
        });

        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText);
              resolve(response);
            } catch (e) {
              reject(new Error("Invalid JSON response"));
            }
          } else {
            reject(new Error(`Upload failed: ${xhr.statusText}`));
          }
        });

        xhr.addEventListener("error", () => {
          reject(new Error("Upload failed"));
        });

        xhr.open("POST", API_BASE_URL + "/upload/csv");
        xhr.send(form);
      });

      // Clear progress for this file
      setUploadProgress((prev) => {
        const newProgress = { ...prev };
        delete newProgress[f.name];
        return newProgress;
      });

      // Add the artifact ID to our uploaded artifacts list
      setUploadedArtifactIds((prev) => [...prev, res.artifactId]);

      // Decode the CSV data to extract columns and preview
      let rowCount = 0;
      let parsedHeaders: string[] = [];
      try {
        const csvContent = atob(res.data);
        const lines = csvContent.split("\n");
        parsedHeaders = lines[0]
          .split(",")
          .map((h) => h.trim().replace(/"/g, ""));
        const previewRows = lines
          .slice(1, 6)
          .map((line) =>
            line.split(",").map((cell) => cell.trim().replace(/"/g, ""))
          )
          .filter((row) => row.some((cell) => cell.length > 0));

        // Calculate total row count (excluding header)
        rowCount = lines.length - 1;

        setColumns(parsedHeaders);
        setHead(previewRows);
      } catch (e) {
        console.warn("Could not parse CSV preview:", e);
        setColumns([]);
        setHead([]);
      }

      // Store the uploaded CSV information
      setUploadedCsvArtifact({
        artifactId: res.artifactId,
        fileName: f.name,
        description: res.description,
        columns: parsedHeaders,
        rowCount: rowCount,
      });

      setCsvFile(null);
    } catch (err: any) {
      setError(err.message);
      // Clear progress on error
      if (file) {
        setUploadProgress((prev) => {
          const newProgress = { ...prev };
          delete newProgress[file.name];
          return newProgress;
        });
      }
    }
  }

  async function handleImageUpload(files: File[]) {
    if (files.length === 0) return;
    setError("");

    try {
      // Create a new session if we don't have one
      let activeSession = sessionId;
      if (!activeSession) {
        const sessionRes = await getJSON<{ sessionId: string }>(
          "/sessions/new?user_id=default_user"
        );
        activeSession = sessionRes.sessionId;
        setSessionId(activeSession);
      }

      const uploadedIds: string[] = [];
      const newImageArtifacts: Array<{
        artifactId: string;
        data: string;
        fileName: string;
        description: string;
      }> = [];

      // Upload each image with progress tracking
      for (const file of files) {
        // Initialize progress for this file
        setUploadProgress((prev) => ({ ...prev, [file.name]: 0 }));

        const form = new FormData();
        form.append("file", file);
        form.append("userId", "default_user");
        form.append("sessionId", activeSession);
        form.append("caption", `Uploaded image: ${file.name}`);

        // Use XMLHttpRequest for progress tracking
        const uploadResult = await new Promise<{
          artifactId: string;
          sessionId: string;
          userId: string;
          data: string;
          type: string;
          description: string;
          width: number;
          height: number;
          format: string;
        }>((resolve, reject) => {
          const xhr = new XMLHttpRequest();

          xhr.upload.addEventListener("progress", (event) => {
            if (event.lengthComputable) {
              const percentComplete = Math.round(
                (event.loaded / event.total) * 100
              );
              setUploadProgress((prev) => ({
                ...prev,
                [file.name]: percentComplete,
              }));
            }
          });

          xhr.addEventListener("load", () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              try {
                const response = JSON.parse(xhr.responseText);
                resolve(response);
              } catch (e) {
                reject(new Error("Invalid JSON response"));
              }
            } else {
              reject(new Error(`Upload failed: ${xhr.statusText}`));
            }
          });

          xhr.addEventListener("error", () => {
            reject(new Error("Upload failed"));
          });

          xhr.open("POST", API_BASE_URL + "/upload/image");
          xhr.send(form);
        });

        uploadedIds.push(uploadResult.artifactId);

        // Store image data for preview
        newImageArtifacts.push({
          artifactId: uploadResult.artifactId,
          data: uploadResult.data,
          fileName: file.name,
          description: uploadResult.description,
        });

        // Clear progress for this file
        setUploadProgress((prev) => {
          const newProgress = { ...prev };
          delete newProgress[file.name];
          return newProgress;
        });
      }

      // Add all uploaded artifact IDs to our list
      setUploadedArtifactIds((prev) => [...prev, ...uploadedIds]);
      setHasUploadedImages(true);
      setUploadedImageArtifacts((prev) => [...prev, ...newImageArtifacts]);

      // Remove the success message - we'll show previews instead
    } catch (err: any) {
      setError(err.message);
      // Clear all progress on error
      setUploadProgress({});
    }
  }

  function addImageFiles(files: File[]) {
    // Not needed anymore since we upload immediately
  }

  function removeImageArtifact(artifactId: string) {
    setUploadedArtifactIds((prev) => prev.filter((id) => id !== artifactId));
    setUploadedImageArtifacts((prev) =>
      prev.filter((artifact) => artifact.artifactId !== artifactId)
    );

    // Update hasUploadedImages based on remaining images
    setHasUploadedImages((prev) => {
      const remaining = uploadedImageArtifacts.filter(
        (artifact) => artifact.artifactId !== artifactId
      );
      return remaining.length > 0;
    });
  }

  return {
    messages,
    input,
    setInput,
    pending,
    error,
    csvFile,
    setCsvFile,
    sessionId,
    columns,
    head,
    uploadedArtifactIds,
    hasUploadedImages,
    uploadedImageArtifacts,
    uploadedCsvArtifact,
    uploadProgress,
    handleNewChat,
    handleSend,
    handleCsvUpload,
    handleImageUpload,
    removeImageArtifact,
    loadSessionMessages,
  };
};
