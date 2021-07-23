import argparse
from edge.command.model.init import model_init
from edge.exception import EdgeException


def add_model_parser(subparsers):
    parser = subparsers.add_parser("model", help="Model related actions")
    actions = parser.add_subparsers(title="action", dest="action", required=True)
    actions.add_parser("init", help="Initialise model on Vertex AI")


def run_model_actions(args: argparse.Namespace):
    if args.action == "init":
        model_init()
    else:
        raise EdgeException("Unexpected model command")
