import typer
from pathlib import Path

app = typer.Typer()

@app.callback()
def callback():
    """
    Awesome Git clone
    """

class Repository:
    def __init__(self, name = None):
        if name:
            self.name = name
        path = Path(".")
        self.work_dir = (path / f"{name}") if name else (path)
        self.gitdir = (self.work_dir / ".git")


    def create_git_dir_structure(self):
        self.gitdir.mkdir(parents=True)

        for dir in ["branches", "objects", "refs//tags", "refs//heads"]:
            try:
                (self.gitdir/ dir).mkdir(parents=True)
            except PermissionError as e:
                print(f"Permission denied {dir}")

        for file in ["description", "HEAD"]:
            try:
                (self.gitdir / file).touch()
            except PermissionError as e:
                print(f"Permission denied {file}")

@app.command()
def init(name: str = "."):
    """
    Initialize the empty repository
    """
    repo = Repository(name)
    repo.create_git_dir_structure()
    print(f"Initialized empty repository in {repo.gitdir.absolute()}")


@app.command()
def commit():
    """
    list the files to commit - [ for the time being ]
    :return:
    """
    repo = Repository()
    files = [item.name for item in repo.work_dir.iterdir() if Path.is_file(item)]
    print(str(files))




