/**
 * Popup root component — rendered when the extension icon is clicked.
 */
import { useState, useEffect } from "react";
import RepoSummary from "../components/RepoSummary";
import ArchitectureDiagram from "../components/ArchitectureDiagram";
import FlowList from "../components/FlowList";

export default function Popup() {
  const [repoUrl, setRepoUrl] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Auto-detect current GitHub tab URL
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      setRepoUrl(tabs[0]?.url || "");
    });
  }, []);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    chrome.runtime.sendMessage({ type: "ANALYZE_REPO", repoUrl }, (res) => {
      setLoading(false);
      if (res?.error) setError(res.error);
      else setResult(res);
    });
  }

  return (
    <div style={{ padding: 16 }}>
      <h2>🔍 RepoLens</h2>
      <p style={{ fontSize: 12, color: "#555" }}>{repoUrl}</p>
      <button onClick={handleAnalyze} disabled={loading}>
        {loading ? "Analyzing…" : "Generate Architecture"}
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      {result && (
        <>
          <RepoSummary summary={result.repo_summary} stack={result.tech_stack} modules={result.main_modules} />
          <ArchitectureDiagram mermaid={result.architecture_mermaid} evidenceMap={result.evidence_map} />
          <FlowList flows={result.flow_mermaid} />
        </>
      )}
    </div>
  );
}
