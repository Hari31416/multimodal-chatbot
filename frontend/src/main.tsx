import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./styles.css";
import "katex/dist/katex.min.css"; // KaTeX styles for math rendering
import { initHighlightTheme } from "./highlightThemeLoader";

initHighlightTheme();

createRoot(document.getElementById("root")!).render(<App />);
