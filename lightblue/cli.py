import typer

app = typer.Typer()


@app.command()
def start():
    print("Hello World")


@app.command()
def status():
    print("✅")
