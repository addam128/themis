import argparse

from serde.toml import from_toml

from themis.common.config import Config


def parse_args():

    parser = argparse.ArgumentParser("themis")
    #parser.add_argument("--module", type=str, choices=["trace", "transform", "compare", "all"], help="functionality to invoke")
    subparsers = parser.add_subparsers(title="actions")

    trace_parser = subparsers.add_parser("trace")
    trace_parser.add_argument("executable", help="Name of executable. The path to its directory has to be set in the a config file.")
    trace_parser.add_argument("--set-ptrace-scope-to-zero", action="store_true", default=False ,help="You might need to set this for frida to work.")
    trace_parser.set_defaults(func=trace_entry)
    
    transform_parser = subparsers.add_parser("transform")
    transform_parser.add_argument("executable", help="Name of the executable, for which a trace file has already been created.")
    transform_parser.add_argument("--img", default=False, help="Save graphs as png.", action="store_true")
    transform_parser.add_argument("--trusted", default=False, action="store_true", help="Indicate whether this binary is trusted,\
        and whether it should populate the database of known programs.")
    transform_parser.set_defaults(func=transform_entry)

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("executable", help="Name of the executable, for which a graph has been already created,\
     and closest neighbours should be find.")
    search_parser.add_argument("-k", default=1, help="Number of neighbours to find. Default is 1.",
        choices=['1', '2', '3', '4', '5', '6', '7', '8'])
    search_parser.set_defaults(func=search_entry)

    list_action = subparsers.add_parser("list",help="Show all accumulated trusted binaries.")
    list_action.set_defaults(func=list_entry)

    stats_action = subparsers.add_parser("stats",help="Show all accumulated trusted binaries.")
    stats_action.add_argument("executable1", help="Name of the executable, for which a graph has been already created,\
     and closest neighbours should be find.")
    stats_action.add_argument("executable2", help="Name of the executable, for which a graph has been already created,\
     and closest neighbours should be find.")
    stats_action.set_defaults(func=stats_entry)

    parser.add_argument("--conf", type=str, default="./themis/config.toml", help="Set different config file.")
    
    return parser.parse_args()


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

    graph = transform(config)
    if args.img:
        to_img(config, graph)


def search_entry(config: Config, args):
    
    from themis.comparing.database import IOIntensiveVPTreeWrapper
    
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

    from themis.comparing.database import FileComparator, TrialGraphComparator

    FileComparator(TrialGraphComparator()).distance(
        f"{config.dirty_graph_dir}/{args.executable1}.gexf",
        f"{config.dirty_graph_dir}/{args.executable2}.gexf"
    )



def main():

    args = parse_args()

    conf_path = args.conf

    with open(conf_path, "r") as config_file:
        config = from_toml(Config, config_file.read())

    args.func(config, args)

        

if __name__ == '__main__':
    main()

