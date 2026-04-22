from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent


@pytest.fixture(scope="session")
def crp_html() -> str:
    return (FIXTURES / "fixture_crp.html").read_text(encoding="utf-8")
