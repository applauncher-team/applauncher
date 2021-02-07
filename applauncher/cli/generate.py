import typer
from .generate import bundle

app = typer.Typer()
app.add_typer(bundle.app, name="bundle")

if __name__ == "__main__":
    app()
