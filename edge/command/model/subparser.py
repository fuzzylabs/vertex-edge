import argparse

from edge.command.model.deploy import model_deploy
from edge.command.model.get_endpoint import get_model_endpoint
from edge.command.model.init import model_init
from edge.exception import EdgeException


def add_model_parser(subparsers):
    parser = subparsers.add_parser("model", help="Model related actions")
    actions = parser.add_subparsers(title="action", dest="action", required=True)
    actions.add_parser("init", help="Initialise model on Vertex AI")
    actions.add_parser("deploy", help="Deploy model on Vertex AI")
    actions.add_parser("get-endpoint", help="Get Vertex AI endpoint URI")


def run_model_actions(args: argparse.Namespace):
    if args.action == "init":
        model_init()
    elif args.action == "deploy":
        model_deploy()
    elif args.action == "get-endpoint":
        get_model_endpoint()
    else:
        raise EdgeException("Unexpected model command")
