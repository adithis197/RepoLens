import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  securityLevel: "loose",
  flowchart: {
    useMaxWidth: false,
    htmlLabels: true,
    curve: "basis",
    nodeSpacing: 60,
    rankSpacing: 80,
    padding: 20,
  },
  themeVariables: {
    fontSize: "16px",
  },
});

function attachClicks(container, evidenceMap, repoUrl, defaultBranch) {
  const nodes = container.querySelectorAll("g.node");

  nodes.forEach((node) => {
    node.style.cursor = "pointer";

    node.addEventListener("click", () => {
      const nodeId = node.id?.replace(/^flowchart-/, "").split("-")[0];
      const labelText =
        node.querySelector("title")?.textContent ||
        node.querySelector(".nodeLabel")?.textContent ||
        "";

      let match = null;
      if (nodeId && evidenceMap) {
        match = evidenceMap.find((e) => e.node_id === nodeId);
      }
      if (!match && labelText && evidenceMap) {
        match = evidenceMap.find((e) => {
          const fileName = e.file.split("/").pop().replace(/\.\w+$/, "");
          return labelText.toLowerCase().includes(fileName.toLowerCase());
        });
      }
      if (!match && labelText && evidenceMap) {
        match = evidenceMap.find((e) =>
          labelText.toLowerCase().includes(e.file.split("/").pop().toLowerCase())
        );
      }
      if (!match) return;

      const branch = defaultBranch || "main";
      const lineAnchor = match.start_line
        ? `#L${match.start_line}${match.end_line ? `-L${match.end_line}` : ""}`
        : "";
      const url = `${repoUrl}/blob/${branch}/${match.file}${lineAnchor}`;

      chrome.tabs.create({ url });
    });
  });
}

function openFullscreen(svgHtml) {
  const w = window.open("", "_blank", "width=1400,height=900");
  if (!w) return;
  w.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>RepoLens Architecture</title>
        <style>
          body { margin: 0; background: #0d1117; padding: 20px; }
          svg { max-width: 100%; height: auto; }
        </style>
      </head>
      <body>${svgHtml}</body>
    </html>
  `);
  w.document.close();
}

export default function ArchitectureDiagram({ code, evidenceMap, repoUrl, defaultBranch }) {
  const ref = useRef(null);
  const [zoom, setZoom] = useState(1.4); // start bigger

  useEffect(() => {
    if (!code || !ref.current) return;

    const render = async () => {
      try {
        const { svg } = await mermaid.render(`arch-${Date.now()}`, code);
        ref.current.innerHTML = svg;

        const svgEl = ref.current.querySelector("svg");
        if (svgEl) {
          svgEl.style.maxWidth = "none";
          svgEl.style.height = "auto";
          svgEl.style.minWidth = "100%";
          svgEl.removeAttribute("height");
        }

        attachClicks(ref.current, evidenceMap, repoUrl, defaultBranch);
      } catch (err) {
        console.error("Mermaid render error:", err);
        ref.current.innerHTML = `<pre style="color:#f85149;font-size:11px;white-space:pre-wrap">Diagram failed to render:\n${err.message}</pre>`;
      }
    };
    render();
  }, [code, evidenceMap, repoUrl, defaultBranch]);

  return (
    <div style={{ position: "relative" }}>
      <div style={controlsStyle}>
        <button onClick={() => setZoom((z) => Math.max(0.5, z - 0.2))} style={btnStyle}>−</button>
        <span style={zoomLabelStyle}>{Math.round(zoom * 100)}%</span>
        <button onClick={() => setZoom((z) => Math.min(3, z + 0.2))} style={btnStyle}>+</button>
        <button onClick={() => setZoom(1.4)} style={{ ...btnStyle, fontSize: 10, padding: "2px 8px" }}>reset</button>
        <button
          onClick={() => openFullscreen(ref.current?.innerHTML || "")}
          style={{ ...btnStyle, fontSize: 10, padding: "2px 8px", marginLeft: 4 }}
          title="Open in full window"
        >
          ⛶ fullscreen
        </button>
      </div>
      <div style={scrollBoxStyle}>
        <div
          style={{
            transform: `scale(${zoom})`,
            transformOrigin: "top left",
            display: "inline-block",
            minWidth: "100%",
          }}
        >
          <div ref={ref} />
        </div>
      </div>
    </div>
  );
}

const scrollBoxStyle = {
  overflow: "auto",
  height: 520,
  background: "#0d1117",
  border: "1px solid #21262d",
  borderRadius: 6,
  padding: 12,
};

const controlsStyle = {
  display: "flex",
  gap: 6,
  alignItems: "center",
  marginBottom: 8,
  justifyContent: "flex-end",
};

const btnStyle = {
  background: "#21262d",
  border: "1px solid #30363d",
  color: "#c9d1d9",
  borderRadius: 4,
  padding: "2px 10px",
  cursor: "pointer",
  fontSize: 13,
  lineHeight: 1,
};

const zoomLabelStyle = {
  fontSize: 11,
  color: "#8b949e",
  minWidth: 36,
  textAlign: "center",
};