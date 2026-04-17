from main import app


def test_app_metadata() -> None:
    assert app.title == "Hackathon UFMG 2026 API"
