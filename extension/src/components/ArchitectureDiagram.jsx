/**
 * Renders the Mermaid architecture diagram.
 * Each node is clickable — navigates to the backing source file/line via evidenceMap.
 */
import { useEffect, useRef } from "react";
import mermaid from "mermaid";

mermaid.initialize({ startOnLoad: false });

export default function ArchitectureDiagram({ mermaid: diagram, evidenceMap }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!diagram || !ref.current) return;
    mermaid.render("arch-diagram", diagram).then(({ svg }) => {
      ref.current.innerHTML = svg;
      // TODO: attach click handlers to nodes using evidenceMap
      // On click → open github file URL at start_line
    });
  }, [diagram]);

  return (
    <div>
      <h3>Architecture</h3>
      <div ref={ref} />
    </div>
  );
}
