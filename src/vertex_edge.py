#!/usr/bin/env python
"""
vertex:edge CLI tool
"""
import argparse
import warnings
import logging

from edge.command.force_unlock import force_unlock
from edge.command.experiments.subparser import add_experiments_parser, run_experiments_actions
from edge.command.init import edge_init
from edge.command.dvc.subparser import add_dvc_parser, run_dvc_actions
from edge.command.config.subparser import add_config_parser, run_config_actions
from edge.command.model.subparser import add_model_parser, run_model_actions

logging.disable(logging.WARNING)
warnings.filterwarnings(
    "ignore",
    "Your application has authenticated using end user credentials from Google Cloud SDK without a quota project.",
)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Edge", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "-c", "--config", type=str, default="edge.yaml", help="Path to the configuration file (default: edge.yaml)"
    )

    subparsers = parser.add_subparsers(title="command", dest="command", required=True)
    init_parser = subparsers.add_parser("init", help="Initialise vertex:edge")
    force_unlock_parser = subparsers.add_parser("force-unlock", help="Force unlock vertex:edge state")

    add_dvc_parser(subparsers)
    add_model_parser(subparsers)
    add_experiments_parser(subparsers)
    add_config_parser(subparsers)

    args = parser.parse_args()

    if args.command == "init":
        edge_init()
    elif args.command == "force-unlock":
        force_unlock()
    elif args.command == "dvc":
        run_dvc_actions(args)
    elif args.command == "model":
        run_model_actions(args)
    elif args.command == "experiments":
        run_experiments_actions(args)
    elif args.command == "config":
        run_config_actions(args)

    raise NotImplementedError("The rest of the commands are not implemented")
