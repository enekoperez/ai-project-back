from pathlib import Path


class DocService:
    def __init__(self, docs_dir=None):
        self.docs_dir = Path(docs_dir) if docs_dir is not None else Path(__file__).resolve().parents[1] / "rag_docs"

    def get_source_files(self):
        if not self.docs_dir.exists():
            return []

        source_files = []
        for source_path in sorted(self.docs_dir.glob("*.md")):
            if not source_path.is_file():
                continue

            # stat = source_path.stat()
            source_files.append({
                "source_name": source_path.name,
                # "source_fingerprint": f"{stat.st_size}:{stat.st_mtime_ns}",  # is this a good/valid fingerprint ?
                # "mime_type": "text/markdown",
                "path": str(source_path.resolve()),  # Needed for get_source_text()
            })

        return source_files

    def get_source_text(self, source_file):
        source_path = source_file.get("path") if source_file else None
        if not source_path:
            return ""

        path = Path(source_path)
        if not path.exists() or not path.is_file():
            return ""

        return path.read_text(encoding="utf-8")
