"""Tests for Step 0: repo ingestion."""
import pytest
from src.pipeline.step0_ingestion.ingestion import ingest_repo, SIGNAL_FILES


def test_signal_files_set_not_empty():
    assert len(SIGNAL_FILES) > 0


# TODO: add integration test with a small public GitHub repo
