import os
import shutil
import subprocess
import time
import types
import typing

from builder.constants import FILTER_STRIP, ENCODING, ARTIFACT_DEST_DIR
from builder.exceptions import BuildError

PWN = typing.TypeVar('PWN')

class FilepathMapping(typing.NamedTuple):
    rel_filepath: str
    source_filepath: str
    build_filepath: str
    gitignore_data: typing.List[str]

class Notebook(typing.NamedTuple):
    name: str
    filename: str
    filepath: str
    position: int = 0

    def create_build_script(self: PWN, categories: typing.List[str], build_dir: str, artifact_dir: str) -> None:
        build_script_filepath = os.path.join(build_dir, f'{self.filename}-builder.sh')
        output_dir = os.path.join(ARTIFACT_DEST_DIR, *categories)
        metadata_path = f'{output_dir}/{self.filename}.metadata.json'
        filename = self.filename.rsplit('.', 1)[0]
        html_path = f'{output_dir}/{filename}.html'
        build_script = f"""#!/usr/bin/env bash
set -e
cd {build_dir}
bash setup-build-env.sh
source env/bin/activate
if [ -f "environment.sh" ]; then
    source environment.sh
fi

mkdir -p {output_dir}
python extract_metadata_from_notebook.py --input "{self.filename}" --output "{metadata_path}"
jupyter nbconvert --debug --to html --execute "{self.filename}" --output "{html_path}" --ExecutePreprocessor.timeout=3600
cd -
"""
        with open(build_script_filepath, 'w') as stream:
            stream.write(build_script)

class Category(typing.NamedTuple):
    name: str
    notebooks: typing.List[Notebook]
    source_dir: str
    build_dir: str
    artifact_dir: str

    def inject_extra_files(self: PWN) -> None:
        filepath_mappings = []
        gitignore_data = load_gitignore_data(os.path.join(self.source_dir, '.gitignore'))
        for rel_filepath in extract_files_and_directories_from_folder_with_gitignore_filepath(self.source_dir):
            source_filepath = os.path.join(self.source_dir, rel_filepath)
            build_filepath = os.path.join(self.build_dir, rel_filepath)
            filepath_mappings.append(FilepathMapping(rel_filepath, source_filepath, build_filepath, gitignore_data))

        for mapping in filter(filter_gitignore_entry, filepath_mappings):
            if os.path.isdir(mapping.source_filepath):
                shutil.copytree(mapping.source_filepath, mapping.build_filepath)

            else:
                shutil.copyfile(mapping.source_filepath, mapping.build_filepath)

    def setup_build_env(self: PWN) -> None:
        env_setup_script: str = f"""#!/usr/bin/env bash
set -e
cd {self.build_dir}
virtualenv -p $(which python) env
source env/bin/activate
pip install -U pip setuptools
if [ -f "pre-install.sh" ]; then
    bash pre-install.sh
fi
if [ -f "pre-requirements.txt" ]; then
    pip install -U -r pre-requirements.txt
fi
if [ -f "requirements.txt" ]; then
    pip install -U -r requirements.txt
fi
if [ -f "environment.sh" ]; then
    source environment.sh
fi
pip install jupyter
mkdir -p {self.artifact_dir}
cd -
"""
        if os.path.exists(self.build_dir):
            shutil.rmtree(self.build_dir)

        if os.path.exists(self.artifact_dir):
            shutil.rmtree(self.artifact_dir)

        os.makedirs(self.build_dir)
        os.makedirs(self.artifact_dir)
        build_script_path = os.path.join(self.build_dir, 'setup-build-env.sh')
        with open(build_script_path, 'w') as stream:
            stream.write(env_setup_script)

        for filename in ['extract_metadata_from_notebook.py']:
            build_filepath = os.path.join(self.build_dir, filename)
            source_filepath = os.path.join(os.getcwd(), '.circleci', filename)
            if os.path.exists(source_filepath):
                shutil.copyfile(source_filepath, build_filepath)

class Collection(typing.NamedTuple):
    name: str
    categories: typing.List[Category]

class BuildJob(typing.NamedTuple):
    collection: Collection
    category: Category
    scripts: typing.List[str]

def filter_gitignore_entry__as_string(entry: str, gitignore_data: typing.List[str], filepath: str = None) -> bool:
    entry = entry.strip(FILTER_STRIP)
    for line in gitignore_data:
        line = line.strip(FILTER_STRIP)
        if line == entry:
            if filepath:
                return os.path.isfile(filepath) or os.path.isdir(filepath)

            return os.path.isfile(entry) or os.path.isidr(entry)

        elif '*' in line and entry.startswith(line):
            raise NotImplementedError

    return False

def filter_gitignore_entry(mapping: FilepathMapping) -> bool:
    return not filter_gitignore_entry__as_string(mapping.rel_filepath, mapping.gitignore_data, mapping.source_filepath)

def run_command(cmd: typing.Union[str, typing.List[str]]) -> None:
    if isinstance(cmd, str):
        cmd = [cmd]

    proc = subprocess.Popen(cmd, shell=True)
    while proc.poll() is None:
        time.sleep(.1)

    if proc.poll() > 0:
        raise BuildError(f'Process Exit Code[{proc.poll()}]')


def load_gitignore_data(filepath: str) -> typing.List[str]:
    if not os.path.exists(filepath):
        return []

    with open(filepath, 'rb') as stream:
        data = [line for line in stream.read().decode(ENCODING).split('\n') if line]

    data.extend(['.gitignore', 'venv', 'env', 'virtual-env', 'virtualenv', '.ipynb_checkpoints'])
    return data

def extract_files_and_directories_from_folder_with_gitignore_filepath(folder_path: str, deep_search: bool = False) -> types.GeneratorType:
    gitignore_filepath = os.path.join(folder_path, '.gitignore')
    for root, dirnames, filenames in os.walk(folder_path):
        for dirname in dirnames:
            yield dirname

        for filename in filenames:
            filepath = os.path.join(root, filename)
            if deep_search is False:
                rel_path = filepath.split(root, 1)[1].strip('/')
                yield rel_path

            else:
                raise NotImplementedError
                yield filepath
        break

