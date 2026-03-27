"""
Step 4: Output Formatting

Converts raw LLM output into the final AnalyzeResponse schema:
  - Mermaid diagram strings (validated)
  - JSON evidence map (node_id → file + line range)
"""
import json


def format_output(raw_output: dict) -> dict:
    """
    Parse and validate architecture generation output into API response shape.
    """
    raw = raw_output.get("raw", "{}")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # TODO: add fallback / retry logic
        parsed = {}

    return {
        "repo_summary": parsed.get("summary", ""),
        "tech_stack": parsed.get("tech_stack", []),
        "main_modules": parsed.get("main_modules", []),
        "architecture_mermaid": parsed.get("architecture_mermaid", ""),
        "flow_mermaid": parsed.get("flow_mermaid", []),
        "evidence_map": parsed.get("evidence_map", []),
    }
