import React, { useEffect, useRef, useState } from "react";

interface LazyDataImageProps {
  dataUrl: string; // base64 data URL
  alt?: string;
  className?: string;
  wrapperClassName?: string;
  eager?: boolean; // if true, skip lazy logic
  largeThresholdBytes?: number; // override threshold
  onClick?: () => void;
}

// Rough size calculation from base64 length
function estimateBytes(dataUrl: string): number {
  const idx = dataUrl.indexOf(",");
  if (idx === -1) return 0;
  const b64 = dataUrl.slice(idx + 1);
  // 4 base64 chars ~ 3 bytes
  return Math.floor((b64.length * 3) / 4);
}

export const LazyDataImage: React.FC<LazyDataImageProps> = ({
  dataUrl,
  alt = "image",
  className = "",
  wrapperClassName = "",
  eager = false,
  largeThresholdBytes = 200 * 1024, // 200KB
  onClick,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [visible, setVisible] = useState(false);
  const [ready, setReady] = useState(eager);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const estimated = estimateBytes(dataUrl);
  const isLarge = estimated > largeThresholdBytes;

  // Intersection Observer to mark visible
  useEffect(() => {
    if (eager) {
      setVisible(true);
      return;
    }
    const el = containerRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setVisible(true);
            observer.disconnect();
            break;
          }
        }
      },
      { rootMargin: "200px" }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [eager]);

  // Defer heavy decode for large images slightly / until idle once visible
  useEffect(() => {
    if (!visible || ready) return;
    const startDecode = () => {
      // Convert data URL to object URL to hint caching & potential GC later
      try {
        fetch(dataUrl)
          .then((r) => r.blob())
          .then((blob) => {
            const url = URL.createObjectURL(blob);
            setObjectUrl(url);
            setReady(true);
          })
          .catch(() => setReady(true));
      } catch {
        setReady(true);
      }
    };
    if (isLarge && "requestIdleCallback" in window) {
      const id = (window as any).requestIdleCallback(() => startDecode(), {
        timeout: 1500,
      });
      return () => (window as any).cancelIdleCallback?.(id);
    } else if (isLarge) {
      const t = setTimeout(startDecode, 50);
      return () => clearTimeout(t);
    } else {
      startDecode();
    }
  }, [visible, ready, dataUrl, isLarge]);

  // Cleanup object URL
  useEffect(() => {
    return () => {
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [objectUrl]);

  const imgSrc = objectUrl || (ready ? dataUrl : undefined);

  return (
    <div
      ref={containerRef}
      className={`relative overflow-hidden ${wrapperClassName}`}
      onClick={onClick}
    >
      {/* Skeleton / placeholder */}
      {!ready && (
        <div className="absolute inset-0 animate-pulse bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-[10px] text-slate-500 dark:text-slate-400 select-none">
          {isLarge ? "Loading image…" : "Loading…"}
        </div>
      )}
      {imgSrc && (
        <img
          src={imgSrc}
          alt={alt}
          loading={eager ? "eager" : "lazy"}
          className={`w-full h-full object-cover transition-opacity duration-300 ${
            ready ? "opacity-100" : "opacity-0"
          } ${className}`}
        />
      )}
    </div>
  );
};

export default LazyDataImage;
