import argparse

from edge.command.experiments.get_dashboard import get_dashboard
from edge.command.experiments.get_mongodb import get_mongodb
from edge.exception import EdgeException
from edge.command.experiments.init import experiments_init


def add_experiments_parser(subparsers):
    parser = subparsers.add_parser("experiments", help="Experiments related actions")
    actions = parser.add_subparsers(title="action", dest="action", required=True)
    actions.add_parser("init", help="Initialise experiments")
    actions.add_parser("get-dashboard", help="Get experiment tracker dashboard URL")
    actions.add_parser("get-mongodb", help="Get MongoDB connection string")


def run_experiments_actions(args: argparse.Namespace):
    if args.action == "init":
        experiments_init()
    elif args.action == "get-dashboard":
        get_dashboard()
    elif args.action == "get-mongodb":
        get_mongodb()
    else:
        raise EdgeException("Unexpected experiments command")
