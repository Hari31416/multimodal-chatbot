import { ChatMessage } from "../../types/chat";
import { BackendMessage, UploadedImageArtifact } from "./types";

// Helper function to convert image file to base64
export async function convertImageToBase64(file: File): Promise<string> {
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

// Generate unique message ID
export function generateMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

// Ensure a session exists, creating one if necessary
export async function ensureSessionExists(
  currentSessionId: string | null,
  setSessionId: (sessionId: string) => void,
  setError: (error: string) => void,
  operationName: string = "operation"
): Promise<string | null> {
  if (currentSessionId) {
    return currentSessionId;
  }

  try {
    const { getJSON } = await import("../../api/client");
    const res = await getJSON<{ sessionId: string }>(
      "/sessions/new?user_id=default_user"
    );
    setSessionId(res.sessionId);
    return res.sessionId;
  } catch (e: any) {
    const errorMessage = `Failed to create session for ${operationName}: ${e.message}`;
    setError(errorMessage);
    console.error(errorMessage, e);
    return null;
  }
}

// Convert backend message to chat message
export function convertBackendMessage(
  msg: BackendMessage,
  index: number,
  sessionId: string
): ChatMessage {
  let modality: ChatMessage["modality"] = "text";
  let content: string = "";
  let imageUrl: string | undefined;
  let imageUrls: string[] = [];
  let code: string | undefined;
  let artifact: ChatMessage["artifact"];

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
    const imageParts = msg.content.filter((p: any) => p?.type === "image_url");
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
}

// Extract CSV data from session messages
export function extractCsvDataFromSession(
  backendMessages: BackendMessage[],
  setColumns: (columns: string[]) => void,
  setHead: (head: any[][]) => void,
  setUploadedCsvArtifact: (artifact: any) => void
) {
  // Validate that the setter functions are actually functions
  if (typeof setColumns !== "function") {
    console.error("setColumns is not a function:", setColumns);
    return;
  }
  if (typeof setHead !== "function") {
    console.error("setHead is not a function:", setHead);
    return;
  }
  if (typeof setUploadedCsvArtifact !== "function") {
    console.error(
      "setUploadedCsvArtifact is not a function:",
      setUploadedCsvArtifact
    );
    return;
  }

  const sessionHasCsvData = backendMessages.some((msg: any) => {
    return (
      msg.artifacts &&
      msg.artifacts.some((artifact: any) => artifact.type === "csv")
    );
  });

  if (sessionHasCsvData) {
    // Extract CSV data from the first CSV artifact found
    for (const msg of backendMessages as any[]) {
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

              return; // Found CSV data, stop searching
            } catch (e) {
              console.warn("Could not parse CSV data from artifact:", e);
              // Continue to next artifact instead of failing completely
            }
          }
        }
      }
    }
  } else {
    // Clear CSV data if no CSV artifacts found
    try {
      setColumns([]);
      setHead([]);
    } catch (e) {
      console.error("Error clearing CSV data:", e);
    }
  }
}

// Extract all artifact IDs from session
export function extractArtifactIdsFromSession(
  backendMessages: BackendMessage[]
) {
  const allArtifactIds: string[] = [];
  let sessionHasImages = false;

  for (const msg of backendMessages as any[]) {
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

  return { allArtifactIds, sessionHasImages };
}
