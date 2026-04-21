/**
 * Renders the Mermaid architecture diagram.
 * Each node is clickable — navigates to the backing source file/line via evidenceMap.
 */
import { useEffect, useRef } from "react";
import mermaid from "mermaid";

mermaid.initialize({ startOnLoad: false });

function attachClicks(container, evidenceMap, repoUrl) {
  const nodes = container.querySelectorAll("g.node");

  nodes.forEach((node) => {
    node.style.cursor = "pointer";

    node.addEventListener("click", () => {
      const label = node.querySelector("title")?.textContent;

      if (!label) return;

      // match by file name (safe baseline approach)
      const match = evidenceMap?.find((e) =>
        label.includes(e.file.split(".")[0])
      );

      if (!match) return;

      const url =
        `${repoUrl}/blob/main/${match.file}` +
        `#L${match.start_line}-L${match.end_line}`;

      window.open(url, "_blank");
    });
  });
}

export default function ArchitectureDiagram({ code, evidenceMap, repoUrl }) {
  const ref = useRef(null);

  useEffect(() => {
  if (!code || !ref.current) return;

  const render = async () => {
    const { svg } = await mermaid.render(
      `arch-${Date.now()}`, // IMPORTANT: unique id
      code
    );

    ref.current.innerHTML = svg;

    attachClicks(ref.current, evidenceMap, repoUrl);
  };

  render();
}, [code]);

  return <div ref={ref} />;
}
