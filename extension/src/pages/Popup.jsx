import { useState, useEffect } from "react";

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
      setRepoUrl(url);
      const match = url.match(/github\.com\/([^/]+\/[^/]+)/);
      if (match) {
        setIsGitHub(true);
        setRepoName(match[1]);
      }
    });
  }, []);

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("http://localhost:8000/test/ingestion", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl }),
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError("Backend not running. Start it with: python3 -m uvicorn src.api.main:app --reload");
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
              <p style={styles.loadingText}>Fetching repo + building dependency graph...</p>
              <p style={styles.loadingSubtext}>This may take 20-30 seconds</p>
            </div>
          )}

          {error && (
            <div style={styles.errorBox}>
              <p style={styles.errorText}>{error}</p>
            </div>
          )}

          {result && (
            <div style={styles.resultBox}>
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

              <div style={styles.section}>
                <p style={styles.sectionTitle}>Top central files</p>
                {result.top_central_files?.slice(0, 5).map((f) => (
                  <div key={f} style={styles.fileRow}>
                    <span style={styles.fileName}>{f.split("/").pop()}</span>
                    <span style={styles.filePath}>{f}</span>
                  </div>
                ))}
              </div>

              <div style={styles.section}>
                <p style={styles.sectionTitle}>Signal files</p>
                {result.signal_files?.map((f) => (
                  <span key={f} style={styles.pill}>{f.split("/").pop()}</span>
                ))}
              </div>
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
    minHeight: 200,
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
    margin: 0,
  },
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
    fontSize: 14,
    fontWeight: 600,
    cursor: "pointer",
    marginBottom: 12,
  },
  loadingBox: {
    textAlign: "center",
    padding: "12px 0",
  },
  loadingText: {
    fontSize: 13,
    color: "#8b949e",
    margin: "0 0 4px",
  },
  loadingSubtext: {
    fontSize: 11,
    color: "#484f58",
    margin: 0,
  },
  errorBox: {
    background: "#3d1c1c",
    border: "1px solid #6e3535",
    borderRadius: 8,
    padding: 12,
  },
  errorText: {
    fontSize: 12,
    color: "#f85149",
    margin: 0,
  },
  resultBox: {
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  stat: {
    display: "inline-flex",
    flexDirection: "column",
    alignItems: "center",
    background: "#161b22",
    border: "1px solid #21262d",
    borderRadius: 8,
    padding: "8px 16px",
    marginRight: 8,
  },
  statNum: {
    fontSize: 20,
    fontWeight: 700,
    color: "#58a6ff",
  },
  statLabel: {
    fontSize: 10,
    color: "#8b949e",
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
  },
  fileRow: {
    display: "flex",
    flexDirection: "column",
    marginBottom: 6,
    paddingBottom: 6,
    borderBottom: "1px solid #21262d",
  },
  fileName: {
    fontSize: 13,
    fontWeight: 600,
    color: "#e6edf3",
  },
  filePath: {
    fontSize: 11,
    color: "#484f58",
  },
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
};

// add at the very bottom of the file, after the styles object
document.addEventListener('DOMContentLoaded', () => {
  console.log('root element:', document.getElementById('root'));
});