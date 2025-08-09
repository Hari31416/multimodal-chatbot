import React, { useState, useEffect } from "react";
import UnifiedChat from "./components/UnifiedChat";

const App: React.FC = () => {
  const [dark, setDark] = useState<boolean>(
    () => window.matchMedia("(prefers-color-scheme: dark)").matches
  );
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  return (
    <div className="h-screen flex flex-col">
      <main className="flex-1 overflow-hidden">
        <UnifiedChat dark={dark} setDark={setDark} />
      </main>
    </div>
  );
};

export default App;
