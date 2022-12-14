import hashlib
import zlib

import typer
from pathlib import Path
from dataclasses import dataclass

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


class Tree:
    def __init__(self, entries):
        self.entries = entries

    def type(self):
        return b"tree"

    def serialize(self):
        mode = b'100644'
        content = b''
        for item in self.entries:
            content += mode + b' ' + item.name.encode() + b'\x00' + bytes.fromhex(item.sha)
        return content



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
    entries = []

    for item in files:
        with open(item, "rb") as fd:
            file_content = fd.read()
            blob = Blob(file_content)
            sha = database.store_object(blob)
            entries.append(Entry(item.name, sha))

    # Tree is a snapshot of all the entries, so it should be made
    # out of the contents of all the entries which participated in that
    # commit
    tree = Tree(entries)
    database.store_object(tree)


@dataclass()
class Entry:
    name: str
    sha: str


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

    def serialize(self):
        return self.data


class Database:
    def __init__(self, db_path: Path):
        self.path = db_path

    def store_object(self, obj):
        content_to_write = self.get_content_bytes(obj)
        sha = self.hash_it(content_to_write, obj)
        # compute the path
        path = (self.path / sha[:2])
        path.mkdir(parents=True, exist_ok=True)
        print(path)

        path = (path / sha[2:])
        with open(path, "wb") as file:
            file.write(zlib.compress(content_to_write))
        return sha

    def hash_it(self, content_to_write, obj):
        sha = hashlib.sha1(content_to_write).hexdigest()
        obj.sha = sha
        return sha

    def get_content_bytes(self, obj):
        obj_content = obj.serialize()
        content_to_write = obj.type() + b' ' + str(len(obj_content)).encode() + b'\x00' + obj_content
        return content_to_write
