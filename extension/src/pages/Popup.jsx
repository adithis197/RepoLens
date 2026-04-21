import { useState, useEffect } from "react";
import ArchitectureDiagram from "../components/ArchitectureDiagram";

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
      console.log("Current tab URL:", url);

      const match = url.match(/^https?:\/\/github\.com\/([^/]+)\/([^/?#]+)/);

      if (match) {
        const owner = match[1];
        const repo = match[2].replace(/\.git$/, "");
        const cleanRepoUrl = `https://github.com/${owner}/${repo}`;

        setIsGitHub(true);
        setRepoName(`${owner}/${repo}`);
        setRepoUrl(cleanRepoUrl);

        console.log("Clean repo URL:", cleanRepoUrl);
      } else {
        setIsGitHub(false);
        setRepoName("");
        setRepoUrl("");
      }
    });
  }, []);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      console.log("Sending repo_url:", repoUrl);

      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl }),
      });

      const text = await res.text();
      console.log("Raw response:", text);

      if (!res.ok) {
        throw new Error(`Backend returned ${res.status}: ${text}`);
      }

      const data = JSON.parse(text);
      setResult(data);
    } catch (e) {
      console.error("Analyze failed:", e);
      setError(e.message || "Something went wrong.");
    }

    setLoading(false);
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.logo}>RepoLens</span>
        <span style={styles.badge}>beta</span>
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

          <button
            style={{ ...styles.button, opacity: loading ? 0.7 : 1 }}
            onClick={handleAnalyze}
            disabled={loading}
          >
            {loading ? "Analyzing..." : "Generate Architecture"}
          </button>

          {loading && (
            <div style={styles.loadingBox}>
              <p style={styles.loadingText}>
                Fetching repo + building dependency graph...
              </p>
              <p style={styles.loadingSubtext}>This may take 20–30 seconds</p>
            </div>
          )}

          {error && (
            <div style={styles.errorBox}>
              <p style={styles.errorText}>{error}</p>
            </div>
          )}

          {result && (
            <div style={styles.resultBox}>
              {/* Stats (Person 1) */}
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <div style={styles.stat}>
                  <span style={styles.statNum}>{result.total_files}</span>
                  <span style={styles.statLabel}>files</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statNum}>{result.graph_edges}</span>
                  <span style={styles.statLabel}>imports</span>
                </div>
                <div style={styles.stat}>
                  <span style={styles.statNum}>{result.graph_nodes}</span>
                  <span style={styles.statLabel}>nodes</span>
                </div>
              </div>

              {/* Summary */}
              {result.repo_summary && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Repository summary</p>
                  <p style={styles.bodyText}>{result.repo_summary}</p>
                </div>
              )}

              {/* Domain */}
              {result.domain && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Domain</p>
                  <p style={styles.bodyText}>{result.domain}</p>
                </div>
              )}

              {/* Tech Stack */}
              {result.tech_stack?.length > 0 && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Tech stack</p>
                  {result.tech_stack.map((item) => (
                    <span key={item} style={styles.pill}>{item}</span>
                  ))}
                </div>
              )}

              {/* Main Modules */}
              {result.main_modules?.length > 0 && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Main modules</p>
                  {result.main_modules.map((item) => (
                    <div key={item} style={styles.listItem}>{item}</div>
                  ))}
                </div>
              )}

              {/* Entry Points */}
              {result.entry_points?.length > 0 && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Entry points</p>
                  {result.entry_points.map((item) => (
                    <div key={item} style={styles.fileRow}>
                      <span style={styles.fileName}>{item.split("/").pop()}</span>
                      <span style={styles.filePath}>{item}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Keywords */}
              {result.keywords?.length > 0 && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Keywords</p>
                  {result.keywords.map((item) => (
                    <span key={item} style={styles.pill}>{item}</span>
                  ))}
                </div>
              )}

              {/* Top Central Files (Person 1) */}
              {result.top_central_files?.length > 0 && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Top central files</p>
                  {result.top_central_files.slice(0, 5).map((f) => (
                    <div key={f} style={styles.fileRow}>
                      <span style={styles.fileName}>{f.split("/").pop()}</span>
                      <span style={styles.filePath}>{f}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Signal Files (Person 1) */}
              {result.signal_files?.length > 0 && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Signal files</p>
                  {result.signal_files.map((f) => (
                    <span key={f} style={styles.pill}>{f.split("/").pop()}</span>
                  ))}
                </div>
              )}

              {/* Architecture Diagram */}
              {result.architecture_mermaid && (
                <div style={styles.section}>
                  <p style={styles.sectionTitle}>Architecture</p>

              <ArchitectureDiagram
                code={result.architecture_mermaid}
                evidenceMap={result.evidence_map}
                repoUrl={repoUrl}
              />
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
    width: 380,
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
  logo: {
    fontSize: 18,
    fontWeight: 700,
    color: "#58a6ff",
  },
  badge: {
    fontSize: 10,
    background: "#388bfd26",
    color: "#58a6ff",
    padding: "2px 6px",
    borderRadius: 10,
    border: "1px solid #388bfd",
  },
  emptyState: {
    padding: "32px 0",
    textAlign: "center",
  },
  emptyText: {
    color: "#8b949e",
    fontSize: 13,
  },
  repoBox: {
    background: "#e1e8f1",
    border: "1px solid #21262d",
    borderRadius: 8,
    padding: "10px 12px",
    marginBottom: 12,
  },
  repoLabel: {
    fontSize: 10,
    color: "#8b949e",
    textTransform: "uppercase",
  },
  repoName: {
    fontSize: 14,
    fontWeight: 600,
    color: "#58a6ff",
  },
  button: {
    width: "100%",
    padding: "10px 0",
    background: "#238636",
    color: "#fff",
    border: "none",
    borderRadius: 8,
    fontWeight: 600,
    cursor: "pointer",
    marginBottom: 12,
  },
  loadingBox: { textAlign: "center" },
  loadingText: { fontSize: 13, color: "#8b949e" },
  loadingSubtext: { fontSize: 11, color: "#484f58" },
  errorBox: {
    background: "#3d1c1c",
    border: "1px solid #6e3535",
    borderRadius: 8,
    padding: 12,
  },
  errorText: { color: "#f85149" },
  resultBox: { display: "flex", flexDirection: "column", gap: 12 },
  stat: {
    background: "#161b22",
    border: "1px solid #21262d",
    borderRadius: 8,
    padding: "8px 16px",
    alignItems: "center",
  },
  statNum: { fontSize: 20, fontWeight: 700, color: "#58a6ff" },
  statLabel: { fontSize: 10, color: "#8b949e" },
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
  },
  fileRow: { marginBottom: 6 },
  fileName: { fontSize: 13, fontWeight: 600 },
  filePath: { fontSize: 11, color: "#484f58" },
  pill: {
    display: "inline-block",
    background: "#21262d",
    color: "#8b949e",
    fontSize: 11,
    padding: "3px 8px",
    borderRadius: 10,
    marginRight: 4,
    marginBottom: 4,
  },
  bodyText: { fontSize: 13 },
  listItem: { fontSize: 12, padding: "4px 0" },
};