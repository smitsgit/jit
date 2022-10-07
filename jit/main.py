import hashlib
import zlib

import typer
from pathlib import Path

app = typer.Typer()


@app.callback()
def callback():
    """
    Awesome Git clone
    """


class Repository:
    def __init__(self, name=None):
        if name:
            self.name = name
        path = Path(".")
        self.work_dir = (path / f"{name}") if name else (path)
        self.gitdir = (self.work_dir / ".git")

    def create_git_dir_structure(self):
        self.gitdir.mkdir(parents=True)

        for dir in ["branches", "objects", "refs//tags", "refs//heads"]:
            try:
                (self.gitdir / dir).mkdir(parents=True)
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
    files = [item for item in repo.work_dir.iterdir() if Path.is_file(item)]
    db_path = (repo.gitdir / "objects")
    database = Database(db_path)

    for item in files:
        file_content = item.read_bytes()
        blob = Blob(file_content)
        database.store_object(blob)


class Blob:
    @property
    def sha(self):
        return self._sha

    @sha.setter
    def sha(self, value):
        self._sha = value

    def __init__(self, data):
        self.data = data
        self._sha = None

    def type(self):
        return b'blob'


class Database:
    def __init__(self, db_path: Path):
        self.path = db_path

    def store_object(self, obj: Blob):
        content_to_write = self.get_content_bytes(obj)
        sha = self.hash_it(content_to_write, obj)
        print(sha)

        # compute the path
        path = (self.path / sha[:2])
        path.mkdir(parents=True, exist_ok=True)
        print(path)

        path = (path / sha[2:])
        with open(path, "wb") as file:
            file.write(zlib.compress(content_to_write))

    def hash_it(self, content_to_write, obj):
        sha = hashlib.sha1(content_to_write).hexdigest()
        obj.sha = sha
        return sha

    def get_content_bytes(self, obj):
        blob_content = obj.data
        content_to_write = obj.type() + b' ' + str(len(blob_content)).encode() + b'\x00' + blob_content
        return content_to_write
