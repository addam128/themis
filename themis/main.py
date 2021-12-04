import argparse
import os

from serde.toml import from_toml

from themis.common.config import Config
from themis.tracing.tracer import trace
from themis.transforming.transform import transform, reconstruct, to_img



def parse_args():

    parser = argparse.ArgumentParser("themis")
    parser.add_argument("--module", type=str, choices=["trace", "transform", "compare", "all"], help="functionality to invoke")
    parser.add_argument("--conf", type=str, default="./themis/config.toml", help="set different config file")
    
    return parser.parse_args()


def main():

    args = parse_args()

    conf_path = args.conf

    with open(conf_path, "r") as config_file:
        config = from_toml(Config, config_file.read())

    
    module = args.module
    graph = None

    if module == "trace" or module == "all":
        
        print("Setting up kernel for tracing...")
        print("sudo sysctl kernel.yama.ptrace_scope=0")
        os.system("sudo sysctl kernel.yama.ptrace_scope=0")

        trace(config=config)

    if module == "transform" or module == "all":
        graph = transform(config)
        to_img(config, graph)


    if module == "compare" or module == "all":
        if graph is not None:
            pass # TODO: work with graph instance
        else:
            graph = reconstruct(config)
            for node in graph.nodes(data=True):
                print(node)
                # TODO: loading does not work as it wont reconstruct dataclasses
            #to_img(config, graph=graph)




if __name__ == '__main__':
    main()

