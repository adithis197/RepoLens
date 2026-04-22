"""
Step 4: Output Formatting
"""
import json


def normalize_flow(flow_mermaid):
    if isinstance(flow_mermaid, list):
        return flow_mermaid
    if isinstance(flow_mermaid, str):
        return [flow_mermaid.strip()] if flow_mermaid.strip() else []
    return []


def format_output(raw_output: dict, context) -> dict:
    raw = raw_output.get("raw", "{}")
    print("[DEBUG] mermaid_input:", raw[:500])

    # Attempt 1: direct JSON parse
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # Attempt 2: strip markdown fences
        cleaned = raw
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[-1]
        if "```" in cleaned:
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()
        try:
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, TypeError):
            parsed = {
                "architecture_mermaid": "graph TD\n  error[Could not parse LLM response]",
                "flow_mermaid": [],
                "evidence_map": [],
                "narrative_summary": "",
            }

    return {
        # Person 2 context
        "repo_summary": context.summary,
        "tech_stack": context.tech_stack,
        "main_modules": context.main_modules,
        "entry_points": getattr(context, "entry_points", []),
        "keywords": getattr(context, "keywords", []),

        # Person 4 LLM output
        "narrative_summary": parsed.get("narrative_summary", ""),
        "architecture_mermaid": parsed.get("architecture_mermaid", ""),
        "flow_mermaid": normalize_flow(parsed.get("flow_mermaid", [])),
        "evidence_map": parsed.get("evidence_map", []),
    }