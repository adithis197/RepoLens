"""Maps file extensions to Tree-sitter language names."""

EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".jsx": "javascript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".rb": "ruby",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "c_sharp",
    ".php": "php",
}


def get_language(file_path: str) -> str | None:
    ext = "." + file_path.rsplit(".", 1)[-1] if "." in file_path else ""
    return EXTENSION_TO_LANGUAGE.get(ext)
