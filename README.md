# themis
Themis is a suit of tools for analyzing executables with the help of (dis)similarity to legitimate programs, making it useful for analyzing maliciously modified binaries. More about the overall tool can be found in my diploma thesis (link to be added).

## Dependencies
For dependency resolution we use [poetry](https://python-poetry.org), so you will need it for a smoother experience.

The tool can be used with the following sequence of commands, from the project root folder:
```
poetry install
poetry run python themis/main.py --help
```

## Usage
The tool supports the following modules:
```
options:
  -h, --help            show this help message and exit
  --conf CONF           Set different config file.

actions:
  {trace,transform,search,list,compare,collect}
    trace               Trace binaries with the help of Frida (frida.re)
    transform           Transform frida-traces into graphs.
    search              Search for most similar trusted binaries.
    list                Show all accumulated trusted binaries.
    compare             Compare two graphs in a more fine-grained way, and receive a combined graph with differences.
                        Due to some heuristics in this module, we suggest to run this module multiple times.
    collect             Collect suspicious binary with all its dependencies
```

More detailed help messages can be invoked by:
```
poetry run python themis/main.py <module name> --help
``` 

The default config file can be seen in `themis/config.toml`, the configurable items are:

```toml
lib_dir = "<path to dynamic libraries for the analyzed program, this will be used with LD_LIBRARY_PATH>" 
bin_dir = "<path to the libraries to be analyzed>"
trace_dir = "<path to save temporary and permanent trace files to>"
trusted_graph_dir = "<path to a folder of .gexf and . pickle representation of networkx graphs to be used as the database of legitimate programs>"
dirty_graph_dir = "<path to a folder where graphs of unknown programs should be saved and fetched from>"
result_dir = "<path to a folder where resulting difference graphs should be saved, for images it should have a subfolder named 'img'>"
img_dir = "<path to a folder for saving the transformed graphs as images>"
sample_dir = "<output folder for the sample collecting module>"
traced_libcalls_file = "./themis/trace_conf/libc_i_o.txt" # a list of OS API calls to trace
args = [
    "ptolemy@172.16.0.10",
    "sleep 5 & uname -a & sleep 5 & uname -a"
] # argumens for the analyzed program
```

## Tool Structure
The whole tool is in the subfolder `themis`, where the `modules` folder includes the source code. The other folders are for storing intermediary files, their meaning can be deduced by checking `config.toml`.
`statistics.py` is just a simple script that was used to create the statistics and images for the thesis.


