from fastapi import FastAPI

from app.main import create_app


def test_app_loads() -> None:
    app = create_app()

    assert isinstance(app, FastAPI)
    assert app.title == "P-insight"
