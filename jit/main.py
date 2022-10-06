import typer
from pathlib import Path

app = typer.Typer()

@app.callback()
def callback():
    """
    Awesome Git clone
    """

class Repository:
    def __init__(self, name):
        self.name = name
        path = Path(".")
        repo_path = (path / f"{name}")
        self.gitdir = (repo_path / ".git")
        self.gitdir.mkdir(parents=True)

    def create_git_dir_structure(self):
        for dir in ["branches", "objects", "refs//tags", "refs//heads"]:
            (self.gitdir/ dir).mkdir(parents=True)

        for file in ["description", "HEAD"]:
            (self.gitdir / file).touch()


@app.command()
def init(name: str):
    """
    Initialize the empty repository
    """
    typer.echo("Cooking git for ya ...")
    repo = Repository(name)
    repo.create_git_dir_structure()



