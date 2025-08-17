import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeHighlight from "rehype-highlight";
import rehypeKatex from "rehype-katex";
import { CodeBlock } from "./CodeBlock";

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
}) => {
  return (
    <ReactMarkdown
      className="prose prose-slate dark:prose-invert max-w-none text-sm"
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[
        [
          rehypeHighlight,
          {
            ignoreMissing: true,
            subset: false,
          },
        ],
        rehypeKatex,
      ]}
      components={{
        p({ children }) {
          if (Array.isArray(children) && children.length === 1) {
            const only = children[0];
            if (React.isValidElement(only)) {
              if ((only as any).type === "pre") return <>{children}</>;
              if (
                (only as any).type === "code" &&
                typeof (only as any).props?.className === "string" &&
                /language-/.test((only as any).props.className)
              ) {
                return <>{children}</>;
              }
            }
          }
          return <p>{children}</p>;
        },
        code({ inline, className, children, ...props }) {
          const text = Array.isArray(children)
            ? children.join("")
            : (children as any) ?? "";
          const isFenced =
            typeof className === "string" && /language-/.test(className);
          const isMultiline = typeof text === "string" && /\n/.test(text);
          const isBlock = !inline && (isFenced || isMultiline);
          if (!isBlock) {
            return (
              <code
                className={
                  (className || "") +
                  " px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-700 text-slate-800 dark:text-slate-200 font-medium text-[0.875em]"
                }
                {...props}
              >
                {children}
              </code>
            );
          }
          const effective = className || "language-plaintext";
          return <CodeBlock className={effective}>{children}</CodeBlock>;
        },
        a({ children, ...props }) {
          return (
            <a
              {...props}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              {children}
            </a>
          );
        },
      }}
    >
      {content}
    </ReactMarkdown>
  );
};
