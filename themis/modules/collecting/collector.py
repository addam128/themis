import lddwrap as ldd
import uuid

from pathlib import Path
from zipfile import ZipFile

from themis.modules.common.config import Config


class Collector:
    def __init__(
        self,
        config: Config,
        path: str,
        name: str
    ) -> None:

        self._path = path
        self._config = config
        self._name = name
        self._deps = None



    def collect(
        self
    ) -> 'Collector':

        self._deps = list(
            map(
                lambda dep: str(dep.path),
                ldd.list_dependencies(Path(self._path))
                )
        )
        print(self._deps)

        return self




    def archive(
        self
    ) -> None:

        with ZipFile(f"{self._config.sample_dir}/{self._name}_{uuid.uuid4()}.zip", mode='x') as zf:
            for dep in self._deps:
                if dep is None or dep == "None":
                    continue
                zf.write(dep)
    