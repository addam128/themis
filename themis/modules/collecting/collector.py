import lddwrap as ldd
import pyminizip as zip
import uuid

from pathlib import Path

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

        return self




    def archive(
        self
    ) -> None:

        zip.compress_multiple(
            self._deps,
            None,
            f"{self._config.sample_dir}/{self._name}_{uuid.uuid4()}.zip",
            b'inf3cted',
            4,
            None
        )
    