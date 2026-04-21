"""
Step 4: Output Formatting

Converts raw LLM output into the final AnalyzeResponse schema:
  - Mermaid diagram strings (validated)
  - JSON evidence map (node_id → file + line range)
"""
import json
def normalize_flow(flow_mermaid):
    """
    Ensures consistent structure for flow_mermaid output.
    """
    if isinstance(flow_mermaid, list):
        return "\n\n".join(flow_mermaid)

    if isinstance(flow_mermaid, str):
        return flow_mermaid.strip()

    return ""

def format_output(raw_output: dict, context) -> dict:
    """
    Parse and validate architecture generation output into API response shape.
    """
    raw = raw_output.get("raw", "{}")
    print("[DEBUG] mermaid_input:", raw)
    # Attempt 1: direct JSON parse
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # Attempt 2: strip markdown fences if present
        cleaned = raw
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[-1]
        if "```" in cleaned:
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
            
        except (json.JSONDecodeError, TypeError):
            # Fallback: return empty diagram rather than crash
            parsed = {
                "architecture_mermaid": "graph TD\n  error[Could not parse LLM response]",
                "flow_mermaid": [],
                "evidence_map": [],
            }

    return {
        # From Person 2 context
        "repo_summary": context.summary,
        "tech_stack": context.tech_stack,
        "main_modules": context.main_modules,
        # From Person 3 (already in context via routes.py)
        "entry_points": getattr(context, "entry_points", []),
        "keywords": getattr(context, "keywords", []),
        # From Person 4 LLM call
        "architecture_mermaid": parsed.get("architecture_mermaid", ""),
        "flow_mermaid": normalize_flow(parsed.get("flow_mermaid", [])),
        "evidence_map": parsed.get("evidence_map", []),
    }
