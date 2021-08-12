import argparse

from edge.command.model.deploy import model_deploy
from edge.command.model.describe import describe_model
from edge.command.model.get_endpoint import get_model_endpoint
from edge.command.model.init import model_init
from edge.command.model.list import list_models
from edge.command.model.remove import remove_model
from edge.command.model.template import create_model_from_template
from edge.exception import EdgeException


def add_model_parser(subparsers):
    parser = subparsers.add_parser("model", help="Model related actions")
    actions = parser.add_subparsers(title="action", dest="action", required=True)

    init_parser = actions.add_parser("init", help="Initialise model on Vertex AI")
    init_parser.add_argument("model_name", metavar="model-name", help="Model name")

    deploy_parser = actions.add_parser("deploy", help="Deploy model on Vertex AI")
    deploy_parser.add_argument("model_name", metavar="model-name", help="Model name")

    get_endpoint_parser = actions.add_parser("get-endpoint", help="Get Vertex AI endpoint URI")
    get_endpoint_parser.add_argument("model_name", metavar="model-name", help="Model name")

    actions.add_parser("list", help="List initialised models")

    describe_parser = actions.add_parser("describe", help="Describe an initialised model")
    describe_parser.add_argument("model_name", metavar="model-name", help="Model name")

    remove_parser = actions.add_parser("remove", help="Remove an initialised model from vertex:edge")
    remove_parser.add_argument("model_name", metavar="model-name", help="Model name")

    template_parser = actions.add_parser("template", help="Create a model pipeline from a template")
    template_parser.add_argument("model_name", metavar="model-name", help="Model name")
    template_parser.add_argument("-f", action="store_true",
                                 help="Force override a pipeline directory if already exists")


def run_model_actions(args: argparse.Namespace):
    if args.action == "init":
        model_init(args.model_name)
    elif args.action == "deploy":
        model_deploy(args.model_name)
    elif args.action == "get-endpoint":
        get_model_endpoint(args.model_name)
    elif args.action == "list":
        list_models()
    elif args.action == "describe":
        describe_model(args.model_name)
    elif args.action == "remove":
        remove_model(args.model_name)
    elif args.action == "template":
        create_model_from_template(args.model_name, args.f)
    else:
        raise EdgeException("Unexpected model command")
