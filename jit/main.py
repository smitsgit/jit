import hashlib
import zlib
import os
from datetime import datetime

import typer
from pathlib import Path
from dataclasses import dataclass

from pytz import timezone
from tzlocal import get_localzone
from merry import Merry

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
        for dir_ in ["branches", "objects", "refs//tags", "refs//heads"]:
            (self.gitdir / dir_).mkdir(parents=True)

        for file in ["description", "HEAD"]:
            (self.gitdir / file).touch()


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

    @property
    def sha(self):
        return self._sha

    @sha.setter
    def sha(self, value):
        self._sha = value


class Commit:
    def __init__(self, repo, tree_sha, message):
        self.tree_sha = tree_sha
        self.message = message
        self.repo = repo

    def type(self):
        return b"commit"

    def serialize(self):
        name = os.getenv("GIT_AUTHOR_NAME", "Smital Desai")
        email = os.getenv("GIT_AUTHOR_EMAIL", "desaismital@gmail.com")
        timestamp = datetime.now(timezone('UTC')).astimezone(get_localzone()).strftime("%s %z")
        author = f"{name} <{email}> {timestamp}"
        committer = author
        parent: Path = (self.repo.gitdir / "HEAD").read_text()
        if parent:
            content = f"tree {self.tree_sha}\nparent {parent}\nauthor {author}\ncommitter {author}\n\n{self.message}"
        else:
            # skip parent
            content = f"tree {self.tree_sha}\nauthor {author}\ncommitter {author}\n\n{self.message}"
        print(content)
        return content.encode("utf-8")

    @property
    def sha(self):
        return self._sha

    @sha.setter
    def sha(self, value):
        self._sha = value


@app.command()
def commit(message: str = typer.Option(..., "-m")):
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
    tree_sha = database.store_object(tree)

    commit = Commit(repo, tree_sha, message)
    database.store_object(commit)
    path = repo.gitdir / "HEAD"
    path.write_text(commit.sha + "\n")


@dataclass()
class Entry:
    name: str
    sha: str


class Blob:
    def __init__(self, data):
        self.data = data
        self._sha = None

    def type(self):
        return b'blob'

    def serialize(self):
        return self.data

    @property
    def sha(self):
        return self._sha

    @sha.setter
    def sha(self, value):
        self._sha = value


class Database:
    def __init__(self, db_path: Path):
        self.path = db_path

    def store_object(self, obj):
        content_to_write = self.get_content_bytes(obj)
        sha = self.hash_it(content_to_write, obj)
        obj.sha = sha  # Set the hash in the object's field
        # compute the path
        path = (self.path / sha[:2])
        path.mkdir(parents=True, exist_ok=True)
        print(path)

        path = (path / sha[2:])
        if path.exists():
            print(f"Object as {path} already exists. Skipping overwriting un-necessarily")
            return sha
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
