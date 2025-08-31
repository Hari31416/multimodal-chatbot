import { useChatState } from "./chat/useChatState";
import { useFileUploads } from "./chat/useFileUploads";
import { useMessageHandling } from "./chat/useMessageHandling";

export const useChatLogic = () => {
  // Initialize state management
  const state = useChatState();

  // Initialize file upload handlers
  const fileUploads = useFileUploads({
    actions: {
      setError: state.setError,
      setUploadProgress: state.setUploadProgress,
      setUploadedArtifactIds: state.setUploadedArtifactIds,
      setColumns: state.setColumns,
      setHead: state.setHead,
      setUploadedCsvArtifact: state.setUploadedCsvArtifact,
      setCsvFile: state.setCsvFile,
      setHasUploadedImages: state.setHasUploadedImages,
      setUploadedImageArtifacts: state.setUploadedImageArtifacts,
      csvFile: state.csvFile,
      uploadedImageArtifacts: state.uploadedImageArtifacts,
      uploadedCsvArtifact: state.uploadedCsvArtifact,
    },
    sessionId: state.sessionId,
    setSessionId: state.setSessionId,
  });

  // Initialize message handling
  const messageHandling = useMessageHandling({
    actions: {
      messages: state.messages,
      setMessages: state.setMessages,
      input: state.input,
      setInput: state.setInput,
      setPending: state.setPending,
      setError: state.setError,
      uploadedArtifactIds: state.uploadedArtifactIds,
      uploadedImageArtifacts: state.uploadedImageArtifacts,
      columns: state.columns,
      setColumns: state.setColumns,
      setHead: state.setHead,
      setCsvFile: state.setCsvFile,
      setUploadedArtifactIds: state.setUploadedArtifactIds,
      setHasUploadedImages: state.setHasUploadedImages,
      setUploadedImageArtifacts: state.setUploadedImageArtifacts,
      setUploadedCsvArtifact: state.setUploadedCsvArtifact,
      setUploadProgress: state.setUploadProgress,
    },
    sessionId: state.sessionId,
    setSessionId: state.setSessionId,
  });

  return {
    // State
    messages: state.messages,
    input: state.input,
    pending: state.pending,
    error: state.error,
    csvFile: state.csvFile,
    sessionId: state.sessionId,
    columns: state.columns,
    head: state.head,
    uploadedArtifactIds: state.uploadedArtifactIds,
    hasUploadedImages: state.hasUploadedImages,
    uploadedImageArtifacts: state.uploadedImageArtifacts,
    uploadedCsvArtifact: state.uploadedCsvArtifact,
    uploadProgress: state.uploadProgress,

    // State setters
    setInput: state.setInput,
    setCsvFile: state.setCsvFile,

    // Actions
    handleNewChat: messageHandling.handleNewChat,
    handleSend: messageHandling.handleSend,
    handleRetry: messageHandling.handleRetry,
    handleCsvUpload: fileUploads.handleCsvUpload,
    handleImageUpload: fileUploads.handleImageUpload,
    removeImageArtifact: fileUploads.removeImageArtifact,
    removeCsvArtifact: fileUploads.removeCsvArtifact,
    loadSessionMessages: messageHandling.loadSessionMessages,
  };
};
