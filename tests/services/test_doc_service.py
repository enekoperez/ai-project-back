from pathlib import Path

from webapp.services.doc_service import DocService


def test_get_source_files_returns_markdown_files_sorted(tmp_path):
    docs_dir = tmp_path / "rag_docs"
    docs_dir.mkdir()
    (docs_dir / "football.md").write_text("# Football\n", encoding="utf-8")
    (docs_dir / "basketball.md").write_text("# Basketball\n", encoding="utf-8")
    (docs_dir / "notes.txt").write_text("Ignored", encoding="utf-8")
    (docs_dir / "folder.md").mkdir()

    source_files = DocService(docs_dir=docs_dir).get_source_files()

    assert [source_file["source_name"] for source_file in source_files] == [
        "basketball.md",
        "football.md",
    ]
    assert all(Path(source_file["path"]).is_absolute() for source_file in source_files)


def test_get_source_files_returns_empty_list_when_docs_dir_is_missing(tmp_path):
    assert DocService(docs_dir=tmp_path / "missing").get_source_files() == []


def test_get_source_text_returns_markdown_content(tmp_path):
    source_path = tmp_path / "football.md"
    source_path.write_text("# Football\n\nFootball has eleven players per team.", encoding="utf-8")

    assert DocService().get_source_text({"path": str(source_path)}) == (
        "# Football\n\nFootball has eleven players per team."
    )


def test_get_source_text_returns_empty_string_for_missing_input(tmp_path):
    assert DocService().get_source_text({}) == ""
    assert DocService().get_source_text(None) == ""
    assert DocService().get_source_text({"path": str(tmp_path / "missing.md")}) == ""
