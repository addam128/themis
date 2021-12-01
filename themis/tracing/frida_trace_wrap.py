import subprocess
import os

from typing import List
from deprecated import deprecated

from themis.common.config import Config

class Analyzer:

    def __init__(self, config: Config) -> None:

        self.config = config
        self._exec_path = f"{config.bin_dir}/{config.executable}"

        self._traced_functions = set()
        self._load_function_names(config.traced_libcalls_file)


    @deprecated("we ar not spawning processes, as that breaks them")
    def _extract_dependencies(self):
        import lddwrap

        def _extract_pure_soname(dependency: List[lddwrap.Dependency]):
            return dependency.soname.split('.')[0]

        dependencies = lddwrap.list_dependencies(path=self._exec_path)
        for dep in filter(lambda dep: dep.soname is not None, dependencies):
            self._dependencies.add(_extract_pure_soname(dep))

    @deprecated("frida cant attach to suspended process")
    def _spawn_suspended_target(self):
        # cant attach frida tho
        # https://stackoverflow.com/questions/50002804/create-subprocess-in-python-in-suspended-state
        newEnv = dict(os.environ)
        newEnv['LD_AUDIT'] = './ld_audit.so'
        proc = subprocess.Popen(
            [self._exec_path, *self._cmd_args], \
            env=newEnv,
        )
        return proc

    def _spawn_target(self):
        changed_env = os.environ.copy()
        changed_env["LD_LIBRARY_PATH"] = f"{self.config.lib_dir}"
        proc = subprocess.Popen(
            [self._exec_path, *self.config.args],
            env=changed_env
        )
        return proc

    def _attach_trace(self, pid: int, outname: str):
        # simply via bash atm, as we dont want to reimplement frida-trace

        cmd = ["frida-trace"]
        for function in self._traced_functions:
            cmd.append("-i")
            cmd.append(function.strip())
        cmd.append("-p")
        cmd.append(f"{pid}")

        print(' '.join(cmd))
        with open(outname, "w") as file:
            trace_process = subprocess.Popen(
                cmd,
                stdout=file,
                stdin=subprocess.DEVNULL
            )
            return trace_process

    def extract_libcalls(self):

        proc = self._spawn_target()
        self._attach_trace(proc.pid, f"{self.config.data_dir}/libcalls_{self.config.executable}.txt")
        self._interact(proc)

    @deprecated("we are not writing to ssh, as it does not work")
    def _interact(self, process: subprocess.Popen):
        # process.communicate(b"ishtar\nuname -a\nexit", timeout=20)
        process.wait()

    def _load_function_names(self, filename):

        with open(filename, "r") as file:
            for line in file:
                self._traced_functions.add(line)


