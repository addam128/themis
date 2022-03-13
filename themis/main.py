import argparse

from serde.toml import from_toml

from themis.common.config import Config


def get_argparser():

    parser = argparse.ArgumentParser("themis")
    #parser.add_argument("--module", type=str, choices=["trace", "transform", "compare", "all"], help="functionality to invoke")
    subparsers = parser.add_subparsers(title="actions")

    trace_parser = subparsers.add_parser("trace", help="Trace binaries with the help of Frida (frida.re)")
    trace_parser.add_argument("executable", help="Name of executable. The path to its directory has to be set in the a config file.")
    trace_parser.add_argument("--set-ptrace-scope-to-zero", action="store_true", default=False ,help="You might need to set this for frida to work.")
    trace_parser.set_defaults(func=trace_entry)
    
    transform_parser = subparsers.add_parser("transform", help="Transform frida-traces into graphs.")
    transform_parser.add_argument("executable", help="Name of the executable, for which a trace file has already been created.")
    transform_parser.add_argument("--img", default=False, help="Save graphs as png.", action="store_true")
    transform_parser.add_argument("--trusted", default=False, action="store_true", help="Indicate whether this binary is trusted")
    transform_parser.add_argument("--save", default=False, action="store_true", help="Indicate whether this graph should be saved\
        in pickle and gexf formats. If the flag trusted is also used, it will populate the valid graphs used for comparison.")
    transform_parser.set_defaults(func=transform_entry)

    search_parser = subparsers.add_parser("search", help="Search for most similar trusted binaries.")
    search_parser.add_argument("executable", help="Name of the executable, for which a graph has been already created,\
     and closest neighbours should be find.")
    search_parser.add_argument("-k", default=1, help="Number of neighbours to find. Default is 1.",
        choices=['1', '2', '3', '4', '5', '6', '7', '8'])
    search_parser.set_defaults(func=search_entry)

    list_action = subparsers.add_parser("list",help="Show all accumulated trusted binaries.")
    list_action.set_defaults(func=list_entry)

    compare_action = subparsers.add_parser("compare")
    compare_action.add_argument("unknown_exec", help="Name of the executable, for which a graph has been already created,\
     and is meant to be compared to a valid program.")
    compare_action.add_argument("trusted_exec", help="Name of the executable, for which a graph has been already created,\
     the valid program to compare to.")
    compare_action.set_defaults(func=compare_entry)

    parser.add_argument("--conf", type=str, default="./themis/config.toml", help="Set different config file.")
    
    return parser



def trace_entry(config: Config, args):
    
    import os
    from themis.tracing.tracer import trace

    config.executable = args.executable

    if args.set_ptrace_scope_to_zero:
        print("Setting up kernel for tracing...")
        print("sudo sysctl kernel.yama.ptrace_scope=0")
        os.system("sudo sysctl kernel.yama.ptrace_scope=0")

    trace(config)



def transform_entry(config: Config, args):

    from themis.transforming.transform import transform, to_img

    config.executable = args.executable
    config.trust = args.trusted

    graph = transform(config, args.save)

    if args.img:
        to_img(config, graph)



def search_entry(config: Config, args):
    
    from themis.searching.indexing import IOIntensiveVPTreeWrapper
    
    config.executable = args.executable

    index = IOIntensiveVPTreeWrapper(config)
    res = index.query_k_nearest(f"{config.dirty_graph_dir}/{config.executable}.gexf", int(args.k))
    print(res)



def list_entry(config, args):
    
    import os
    
    with os.scandir(config.graph_dir) as graph_db:
        for item in  map(
                        lambda entry: os.path.splitext(entry.name)[0],
                        filter(
                            lambda entry: entry.is_file() and entry.name.endswith(".gexf"),
                            graph_db
                        )
                    ):
            print(item)
            


def stats_entry(config: Config, args):

    from themis.searching.indexing import FileComparator, TrialGraphComparator

    FileComparator(TrialGraphComparator()).distance(
        f"{config.dirty_graph_dir}/{args.executable1}.gexf",
        f"{config.dirty_graph_dir}/{args.executable2}.gexf"
    )



def compare_entry(config: Config, args):
    
    from themis.comparing.comparator import DeepGraphComparator

    DeepGraphComparator(config, args.unknown_exec, args.trusted_exec).compare()



def main():

    parser = get_argparser() 
    args = parser.parse_args()

    conf_path = args.conf

    with open(conf_path, "r") as config_file:
        config = from_toml(Config, config_file.read())

    try: 
        args.func(config, args)
    
    except AttributeError:
        print("Something went wrong ...")
        parser.print_help()
        

        

if __name__ == '__main__':
    main()

