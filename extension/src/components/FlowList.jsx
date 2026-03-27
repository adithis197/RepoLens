/**
 * Renders the list of representative execution flow diagrams.
 */
import { useEffect, useRef } from "react";
import mermaid from "mermaid";

function FlowDiagram({ diagram, index }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!diagram || !ref.current) return;
    mermaid.render(`flow-${index}`, diagram).then(({ svg }) => {
      ref.current.innerHTML = svg;
    });
  }, [diagram]);

  return <div ref={ref} style={{ marginBottom: 16 }} />;
}

export default function FlowList({ flows }) {
  if (!flows?.length) return null;
  return (
    <div>
      <h3>Key Flows</h3>
      {flows.map((f, i) => <FlowDiagram key={i} diagram={f} index={i} />)}
    </div>
  );
}
