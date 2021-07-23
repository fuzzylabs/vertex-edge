import argparse
import sys

from edge.command.dvc.init import dvc_init
from edge.exception import EdgeException


def add_experiments_parser(subparsers):
    parser = subparsers.add_parser("experiments", help="Experiments related actions")
    actions = parser.add_subparsers(title="action", dest="action", required=True)
    actions.add_parser("init", help="Initialise experiments")


def run_experiments_actions(args: argparse.Namespace):
    if args.action == "init":
        print("Experiments initialisation is not supported yet")
        sys.exit(0)
    else:
        raise EdgeException("Unexpected experiments command")
