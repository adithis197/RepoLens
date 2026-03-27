/**
 * Displays the one-line repo summary, tech stack badges, and main modules.
 */
export default function RepoSummary({ summary, stack, modules }) {
  return (
    <div>
      <p><strong>{summary}</strong></p>
      <div>
        {stack?.map((s) => (
          <span key={s} style={{ background: "#e0e0e0", borderRadius: 4, padding: "2px 6px", marginRight: 4 }}>
            {s}
          </span>
        ))}
      </div>
      <p style={{ fontSize: 12 }}>Modules: {modules?.join(", ")}</p>
    </div>
  );
}
