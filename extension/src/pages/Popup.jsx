import { useState, useEffect } from "react";
import ArchitectureDiagram from "../components/ArchitectureDiagram";

const CACHE_KEY = "repolens_last_result";

export default function Popup() {
  const [repoUrl, setRepoUrl] = useState("");
  const [repoName, setRepoName] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [isGitHub, setIsGitHub] = useState(false);

  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const url = tabs[0]?.url || "";
      const match = url.match(/^https?:\/\/github\.com\/([^/]+)\/([^/?#]+)/);

      if (match) {
        const owner = match[1];
        const repo = match[2].replace(/\.git$/, "");
        const cleanRepoUrl = `https://github.com/${owner}/${repo}`;
        setIsGitHub(true);
        setRepoName(`${owner}/${repo}`);
        setRepoUrl(cleanRepoUrl);

        chrome.storage.local.get([CACHE_KEY], (data) => {
          const cached = data[CACHE_KEY];
          if (cached && cached.repoUrl === cleanRepoUrl) {
            setResult(cached.result);
          }
        });
      }
    });
  }, []);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl }),
      });
      const text = await res.text();
      if (!res.ok) throw new Error(`Backend ${res.status}: ${text.slice(0, 200)}`);

      const data = JSON.parse(text);
      setResult(data);

      chrome.storage.local.set({
        [CACHE_KEY]: { repoUrl, result: data, timestamp: Date.now() },
      });
    } catch (e) {
      setError(e.message || "Something went wrong.");
    }
    setLoading(false);
  }

  function clearCache() {
    chrome.storage.local.remove(CACHE_KEY);
    setResult(null);
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.logo}>RepoLens</span>
        {/* <span style={styles.badge}></span> */}
        {result && (
          <button onClick={clearCache} style={styles.resetBtn} title="Clear cached result">
            ↻
          </button>
        )}
      </div>

      {!isGitHub ? (
        <div style={styles.emptyState}>
          <p style={styles.emptyText}>Open a GitHub repository to get started</p>
        </div>
      ) : (
        <>
          <div style={styles.repoBox}>
            <span style={styles.repoLabel}>Repo detected</span>
            <span style={styles.repoName}>{repoName}</span>
          </div>

          {!result && (
            <button
              style={{ ...styles.button, opacity: loading ? 0.7 : 1 }}
              onClick={handleAnalyze}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Generate Architecture"}
            </button>
          )}

          {loading && (
            <div style={styles.loadingBox}>
              <p style={styles.loadingText}>Fetching repo + building graph + calling LLM...</p>
              <p style={styles.loadingSubtext}>This may take 30-60 seconds</p>
            </div>
          )}

          {error && (
            <div style={styles.errorBox}>
              <p style={styles.errorText}>{error}</p>
            </div>
          )}

          {result && (
            <div style={styles.resultBox}>
              {result.narrative_summary && (
                <div style={styles.heroSection}>
                  <p style={styles.heroTitle}>What this repo does</p>
                  <p style={styles.heroText}>{result.narrative_summary}</p>
                </div>
              )}

              {!result.narrative_summary && result.repo_summary && (
                <div style={styles.heroSection}>
                  <p style={styles.heroTitle}>What this repo does</p>
                  <p style={styles.heroText}>{result.repo_summary}</p>
                </div>
              )}

              <div style={styles.statsRow}>
                <div style={styles.stat}>
                  <span style={styles.statNum}>{result.total_files || 0}</span>
                  <span style={styles.statLabel}>files</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statNum}>{result.graph_edges || 0}</span>
                  <span style={styles.statLabel}>imports</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statNum}>{result.total_selected || 0}</span>
                  <span style={styles.statLabel}>analyzed</span>
                </div>
              </div>

              {result.architecture_mermaid && (
                <div style={styles.diagramSection}>
                  <p style={styles.sectionTitle}>Architecture · click any node to view code</p>
                  <ArchitectureDiagram
                    code={result.architecture_mermaid}
                    evidenceMap={result.evidence_map}
                    repoUrl={repoUrl}
                    defaultBranch={result.default_branch || "main"}
                  />
                </div>
              )}

              {result.tech_stack?.length > 0 && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Tech stack</p>
                  <div>
                    {result.tech_stack.map((item) => (
                      <span key={item} style={styles.pill}>{item}</span>
                    ))}
                  </div>
                </div>
              )}

              {result.main_modules?.length > 0 && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Main modules</p>
                  {result.main_modules.map((item) => (
                    <div key={item} style={styles.listItem}>· {item}</div>
                  ))}
                </div>
              )}

              {result.entry_points?.length > 0 && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Where to start reading</p>
                  {result.entry_points.slice(0, 5).map((f) => (
                    <a
                      key={f}
                      href={`${repoUrl}/blob/${result.default_branch || "main"}/${f}`}
                      target="_blank"
                      rel="noreferrer"
                      style={styles.fileLink}
                    >
                      <span style={styles.fileName}>{f.split("/").pop()}</span>
                      <span style={styles.filePath}>{f}</span>
                    </a>
                  ))}
                </div>
              )}

              {result.top_central_files?.length > 0 && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Most imported files</p>
                  {result.top_central_files.slice(0, 5).map((f) => (
                    <a
                      key={f}
                      href={`${repoUrl}/blob/${result.default_branch || "main"}/${f}`}
                      target="_blank"
                      rel="noreferrer"
                      style={styles.fileLink}
                    >
                      <span style={styles.fileName}>{f.split("/").pop()}</span>
                      <span style={styles.filePath}>{f}</span>
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

const styles = {
  container: {
    width: 520,
    maxHeight: 640,
    overflowY: "auto",
    padding: 16,
    fontFamily: "-apple-system, BlinkMacSystemFont, sans-serif",
    background: "#0d1117",
    color: "#e6edf3",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 14,
    borderBottom: "1px solid #21262d",
    paddingBottom: 12,
  },
  logo: { fontSize: 18, fontWeight: 700, color: "#58a6ff" },
  badge: {
    fontSize: 10,
    background: "#388bfd26",
    color: "#58a6ff",
    padding: "2px 6px",
    borderRadius: 10,
    border: "1px solid #388bfd",
  },
  resetBtn: {
    marginLeft: "auto",
    background: "transparent",
    border: "1px solid #30363d",
    color: "#8b949e",
    borderRadius: 6,
    padding: "2px 8px",
    cursor: "pointer",
    fontSize: 14,
  },
  emptyState: { padding: "32px 0", textAlign: "center" },
  emptyText: { color: "#8b949e", fontSize: 13 },
  repoBox: {
    background: "#161b22",
    border: "1px solid #21262d",
    borderRadius: 8,
    padding: "10px 12px",
    marginBottom: 12,
    display: "flex",
    flexDirection: "column",
    gap: 2,
  },
  repoLabel: {
    fontSize: 10,
    color: "#8b949e",
    textTransform: "uppercase",
    letterSpacing: 1,
  },
  repoName: { fontSize: 14, fontWeight: 600, color: "#58a6ff" },
  button: {
    width: "100%",
    padding: "12px 0",
    background: "#238636",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    marginBottom: 12,
  },
  loadingBox: { textAlign: "center", padding: "16px 0" },
  loadingText: { fontSize: 13, color: "#8b949e", margin: "0 0 4px" },
  loadingSubtext: { fontSize: 11, color: "#484f58", margin: 0 },
  errorBox: {
    background: "#3d1c1c",
    border: "1px solid #6e3535",
    borderRadius: 8,
    padding: 12,
  },
  errorText: { color: "#f85149", fontSize: 12, margin: 0 },
  resultBox: { display: "flex", flexDirection: "column", gap: 14 },

  heroSection: {
    background: "#161b22",
    border: "1px solid #30363d",
    borderRadius: 10,
    padding: 16,
    borderLeft: "3px solid #58a6ff",
  },
  heroTitle: {
    fontSize: 11,
    color: "#58a6ff",
    textTransform: "uppercase",
    letterSpacing: 1.2,
    margin: "0 0 8px",
    fontWeight: 600,
  },
  heroText: {
    fontSize: 13,
    lineHeight: 1.6,
    color: "#e6edf3",
    margin: 0,
  },

  statsRow: { display: "flex", gap: 8 },
  stat: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    background: "#161b22",
    border: "1px solid #21262d",
    borderRadius: 8,
    padding: "10px 8px",
  },
  statNum: { fontSize: 22, fontWeight: 700, color: "#58a6ff" },
  statLabel: { fontSize: 10, color: "#8b949e", marginTop: 2 },

  diagramSection: {
    background: "#161b22",
    border: "1px solid #21262d",
    borderRadius: 8,
    padding: 12,
  },

  section: {
    background: "#161b22",
    border: "1px solid #21262d",
    borderRadius: 8,
    padding: 12,
  },
  sectionTitle: {
    fontSize: 11,
    color: "#8b949e",
    textTransform: "uppercase",
    letterSpacing: 1,
    margin: "0 0 8px",
    fontWeight: 600,
  },
  fileLink: {
    display: "flex",
    flexDirection: "column",
    marginBottom: 6,
    paddingBottom: 6,
    borderBottom: "1px solid #21262d",
    textDecoration: "none",
    cursor: "pointer",
  },
  fileName: { fontSize: 13, fontWeight: 600, color: "#58a6ff" },
  filePath: { fontSize: 11, color: "#484f58" },
  pill: {
    display: "inline-block",
    background: "#21262d",
    color: "#c9d1d9",
    fontSize: 11,
    padding: "4px 10px",
    borderRadius: 12,
    marginRight: 5,
    marginBottom: 5,
  },
  listItem: { fontSize: 12, padding: "3px 0", color: "#c9d1d9" },
};