import os
import sys

import configargparse

root_dir = os.path.dirname(os.path.abspath(__file__))
default_config_files = "{0}/{1}".format(root_dir, "default.yaml")
print(default_config_files)

parser = configargparse.ArgParser(config_file_parser_class=configargparse.YAMLConfigFileParser,
                                  default_config_files=[default_config_files],
                                  auto_env_var_prefix="")
parser.add('--locksmith_main_url', help='locksmith_main_url')
parser.add('--consumer_type', help='consumer_type')
parser.add('--env', help='env')
parser.add('--port', help='port')
parser.add('--host', help='host')
parser.add('--mode', help='mode')
parser.add('--server_type', help='server_type')
parser.add('--realm', help='realm')
# debug flag
parser.add('--debug', help='debug', action="store_true")
parser.add('--postgres_fynix_locksmith_read_write', help='postgres_fynix_locksmith_read_write')
# prometheus flag
parser.add('--prometheus', help='prometheus', action="store_true")

parser.add('--K8S_NODE_NAME', help='K8S_NODE_NAME')
parser.add('--K8S_POD_NAMESPACE', help='K8S_POD_NAMESPACE')
parser.add('--K8S_POD_NAME', help='K8S_POD_NAME')

parser.add('--sentry_dsn', help='SENTRY_DSN')
parser.add('--sentry_environment', help='SENTRY_ENVIRONMENT')

parser.add('--google_app_id', help='GOOGLE_APP_ID')
parser.add('--google_app_secret', help='GOOGLE_APP_SECRET')

parser.add('--kafka_broker_list', help='KAFKA_BROKER_LIST')

parser.add('--clerk_secret_key', help='clerk_secret_key')

arguments = sys.argv
print(arguments)
argument_options = parser.parse_known_args(arguments)
# print("argument values")
print(parser.format_values())
docker_args = argument_options[0]
