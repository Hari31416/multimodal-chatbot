import React, { useState, useRef, useEffect } from "react";
import {
  ChatHeader,
  ChatMessage,
  ChatInput,
  EmptyState,
  LoadingIndicator,
  DatasetModal,
  Sidebar,
} from "./chat";
import { useChatLogic } from "../hooks/useChatLogic";

interface UnifiedChatProps {
  dark: boolean;
  setDark: (dark: boolean) => void;
}

const UnifiedChat: React.FC<UnifiedChatProps> = ({ dark, setDark }) => {
  const [pickerOpen, setPickerOpen] = useState(false);
  const [showDatasetModal, setShowDatasetModal] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const fileInputImageRef = useRef<HTMLInputElement | null>(null);
  const fileInputCsvRef = useRef<HTMLInputElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const {
    messages,
    input,
    setInput,
    pending,
    error,
    sessionId,
    columns,
    head,
    uploadedArtifactIds,
    hasUploadedImages,
    uploadedImageArtifacts,
    handleNewChat,
    handleSend,
    handleCsvUpload,
    handleImageUpload,
    removeImageArtifact,
    loadSessionMessages,
  } = useChatLogic();

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, pending]);

  // Handle clicking outside picker to close it
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      const target = event.target as Node;
      // Check if click is outside picker and attachment button
      if (
        !target.closest("[data-picker]") &&
        !target.closest("[data-attachment-button]")
      ) {
        setPickerOpen(false);
      }
    }

    if (pickerOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }
  }, [pickerOpen]);

  // Clear file inputs when creating new chat
  const handleNewChatWithCleanup = () => {
    handleNewChat();
    setPickerOpen(false);
    if (fileInputImageRef.current) fileInputImageRef.current.value = "";
    if (fileInputCsvRef.current) fileInputCsvRef.current.value = "";
  };

  // Handle session selection from sidebar
  const handleSessionSelect = (sessionId: string, backendMessages: any[]) => {
    loadSessionMessages(sessionId, backendMessages);
    // Reset other states when switching sessions
    setPickerOpen(false);
    if (fileInputImageRef.current) fileInputImageRef.current.value = "";
    if (fileInputCsvRef.current) fileInputCsvRef.current.value = "";
  };

  return (
    <div className="h-full flex">
      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen((o) => !o)}
        currentSessionId={sessionId}
        onSessionSelect={handleSessionSelect}
        onNewChat={handleNewChatWithCleanup}
        dark={dark}
      />

      {/* Main Chat Area */}
      <section
        className={`flex-1 flex flex-col bg-white dark:bg-slate-900 transition-all duration-300 ${
          sidebarOpen ? "lg:ml-0" : ""
        }`}
      >
        <ChatHeader
          sessionId={sessionId}
          dark={dark}
          setDark={setDark}
          hasMessages={messages.length > 0}
          onShowDataset={() => setShowDatasetModal(true)}
          datasetAvailable={columns.length > 0}
          onToggleSidebar={() => setSidebarOpen((o) => !o)}
          sidebarOpen={sidebarOpen}
          onNewChat={handleNewChatWithCleanup}
        />

        {/* Messages Container */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto px-6 py-6 space-y-6 text-[15px] leading-relaxed"
        >
          {messages.length === 0 && !pending && <EmptyState />}

          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              isLast={message === messages[messages.length - 1]}
              pending={pending}
            />
          ))}

          {pending && messages.length > 0 && <LoadingIndicator />}
        </div>

        {/* Chat Input */}
        <ChatInput
          input={input}
          setInput={setInput}
          pending={pending}
          sessionId={sessionId}
          pickerOpen={pickerOpen}
          setPickerOpen={setPickerOpen}
          onSend={handleSend}
          error={error}
          fileInputImageRef={fileInputImageRef}
          fileInputCsvRef={fileInputCsvRef}
          onImageUpload={handleImageUpload}
          hasUploadedImages={hasUploadedImages}
          hasUploadedData={columns.length > 0}
          uploadedImageArtifacts={uploadedImageArtifacts}
          onRemoveImageArtifact={removeImageArtifact}
        />

        <DatasetModal
          open={showDatasetModal}
          onClose={() => setShowDatasetModal(false)}
          columns={columns}
          head={head}
        />

        {/* Hidden file inputs */}
        <input
          ref={fileInputImageRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={(e) => {
            const files = Array.from(e.target.files || []);
            if (files.length > 0) {
              // Upload images immediately
              handleImageUpload(files);
              // Reset the input
              e.target.value = "";
            }
          }}
        />
        <input
          ref={fileInputCsvRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) {
              handleCsvUpload(f);
            }
          }}
        />
      </section>
    </div>
  );
};

export default UnifiedChat;
