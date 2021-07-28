import argparse
import sys

from edge.config import EdgeConfig
from edge.exception import EdgeException


def add_misc_parser(subparsers):
    parser = subparsers.add_parser("misc", help="Miscellaneous actions")
    actions = parser.add_subparsers(title="action", dest="action", required=True)
    actions.add_parser("get-region", help="Get configured region")


def run_misc_actions(args: argparse.Namespace):
    if args.action == "get-region":
        with EdgeConfig.context(silent=True) as config:
            print(config.google_cloud_project.region)
            sys.exit(0)
    else:
        raise EdgeException("Unexpected experiments command")
