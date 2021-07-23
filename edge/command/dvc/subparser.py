import argparse
from edge.command.dvc.init import dvc_init
from edge.exception import EdgeException


def add_dvc_parser(subparsers):
    parser = subparsers.add_parser("dvc", help="DVC related actions")
    actions = parser.add_subparsers(title="action", dest="action", required=True)
    actions.add_parser("init", help="Initialise DVC")


def run_dvc_actions(args: argparse.Namespace):
    if args.action == "init":
        dvc_init()
    else:
        raise EdgeException("Unexpected DVC command")
