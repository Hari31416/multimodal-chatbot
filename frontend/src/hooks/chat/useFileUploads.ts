import { postJSON, getJSON, deleteJSON, API_BASE_URL } from "../../api/client";
import {
  ChatActions,
  UploadedImageArtifact,
  UploadedCsvArtifact,
} from "./types";
import { ensureSessionExists } from "./utils";

interface UseFileUploadsProps {
  actions: ChatActions;
  sessionId: string | null;
  setSessionId: (sessionId: string) => void;
}

export function useFileUploads({
  actions,
  sessionId,
  setSessionId,
}: UseFileUploadsProps) {
  const {
    setError,
    setUploadProgress,
    setUploadedArtifactIds,
    setColumns,
    setHead,
    setUploadedCsvArtifact,
    setCsvFile,
    setHasUploadedImages,
    setUploadedImageArtifacts,
  } = actions;

  async function handleCsvUpload(file?: File) {
    const f = file || actions.csvFile;
    if (!f) return;
    setError("");

    try {
      // Initialize progress for this file
      setUploadProgress((prev) => ({ ...prev, [f.name]: 0 }));

      const form = new FormData();
      form.append("file", f);
      form.append("userId", "default_user"); // Use fixed user_id for now

      // Create a new session if we don't have one
      const activeSession = await ensureSessionExists(
        sessionId,
        setSessionId,
        setError,
        "CSV upload"
      );

      if (!activeSession) {
        return; // Abort the upload operation if session creation failed
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
      const activeSession = await ensureSessionExists(
        sessionId,
        setSessionId,
        setError,
        "image upload"
      );

      if (!activeSession) {
        return; // Abort the upload operation if session creation failed
      }

      const uploadedIds: string[] = [];
      const newImageArtifacts: UploadedImageArtifact[] = [];

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

  async function removeImageArtifact(artifactId: string) {
    // Ensure we have a session before attempting deletion
    let activeSession = sessionId;
    if (!activeSession) {
      console.log("No session ID available, creating one for image deletion");
      activeSession = await ensureSessionExists(
        sessionId,
        setSessionId,
        setError,
        "image deletion"
      );

      if (!activeSession) {
        console.error("Failed to create session for image deletion");
        return;
      }
    }

    try {
      // Call the delete artifact endpoint
      await deleteJSON(
        `/artifacts/delete/${artifactId}?message_id=dummy&session_id=${activeSession}&user_id=default_user`
      );

      // Remove from local state
      setUploadedArtifactIds((prev) => prev.filter((id) => id !== artifactId));
      setUploadedImageArtifacts((prev) => {
        const remaining = prev.filter(
          (artifact) => artifact.artifactId !== artifactId
        );
        setHasUploadedImages(remaining.length > 0);
        return remaining;
      });
    } catch (error) {
      console.error("Failed to delete image artifact:", error);
      setError("Failed to delete image artifact");
    }
  }

  async function removeCsvArtifact() {
    if (!actions.uploadedCsvArtifact) {
      console.warn("No CSV artifact available for deletion");
      return;
    }

    // Ensure we have a session before attempting deletion
    let activeSession = sessionId;
    if (!activeSession) {
      console.log("No session ID available, creating one for CSV deletion");
      activeSession = await ensureSessionExists(
        sessionId,
        setSessionId,
        setError,
        "CSV deletion"
      );

      if (!activeSession) {
        console.error("Failed to create session for CSV deletion");
        return;
      }
    }

    try {
      // Call the delete artifact endpoint
      await deleteJSON(
        `/artifacts/delete/${actions.uploadedCsvArtifact.artifactId}?message_id=dummy&session_id=${activeSession}&user_id=default_user`
      );

      // Remove from local state
      setUploadedArtifactIds((prev) => {
        // Remove the CSV artifact ID if it exists
        const csvArtifactId = actions.uploadedCsvArtifact?.artifactId;
        if (csvArtifactId) {
          return prev.filter((id) => id !== csvArtifactId);
        }
        return prev;
      });
      setUploadedCsvArtifact(null);
      setColumns([]);
      setHead([]);
      setCsvFile(null);
    } catch (error) {
      console.error("Failed to delete CSV artifact:", error);
      setError("Failed to delete CSV artifact");
    }
  }

  return {
    handleCsvUpload,
    handleImageUpload,
    removeImageArtifact,
    removeCsvArtifact,
  };
}
