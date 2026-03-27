# RepoLens

> Generating Traceable Architecture Diagrams for Fast Codebase Onboarding

A Chrome extension that generates an interactive onboarding map for unfamiliar GitHub repos:
- High-level architecture diagram (Mermaid)
- Concise repo/use-case summary
- Key execution flows with click-through traceability to source files

## Pipeline Overview

```
Step 0: Repo Ingestion & Snapshot
Step 1: Tree-sitter AST Parsing → Dependency Graph
Step 2A: LLM Context Inference (stack, domain, modules)
Step 2B: Hybrid Retrieval & Importance Scoring (top-K)
Step 3: Evidence-Grounded Architecture Generation (LLM)
Step 4: Mermaid Diagrams + JSON Evidence Map → Chrome Extension UI
```

## Structure

```
repolens/
  backend/    # Python pipeline + REST API
  extension/  # Chrome extension (JS/React)
```

## Quickstart

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn src.api.main:app --reload

# Extension
cd extension
npm install
npm run build
# Load unpacked from extension/dist in Chrome
```
