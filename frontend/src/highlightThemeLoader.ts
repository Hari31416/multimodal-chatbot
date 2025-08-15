// Dynamically load appropriate highlight.js theme based on presence of 'dark' class.
// This avoids importing both themes globally which would override each other.

const LIGHT_THEME =
  "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-light.min.css";
const DARK_THEME =
  "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css";

export function initHighlightTheme() {
  const id = "hljs-theme";
  const head = document.head;

  const apply = () => {
    const isDark =
      document.documentElement.classList.contains("dark") ||
      document.body.classList.contains("dark");
    let link = document.getElementById(id) as HTMLLinkElement | null;
    const href = isDark ? DARK_THEME : LIGHT_THEME;
    if (link && link.getAttribute("href") === href) return; // already correct
    if (!link) {
      link = document.createElement("link");
      link.id = id;
      link.rel = "stylesheet";
      head.appendChild(link);
    }
    link.href = href;
  };

  // Initial apply
  apply();

  // Observe class changes on <html> and <body>
  const observer = new MutationObserver(apply);
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["class"],
  });
  observer.observe(document.body, {
    attributes: true,
    attributeFilter: ["class"],
  });
}
