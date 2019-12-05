#! /usr/bin/env python3
# Copyright 2019 Tad Lebeck
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Generate customer or internal deployment YAML
"""

import argparse
import base64
import os
import sys
import textwrap as _textwrap
from jinja2 import Environment, FileSystemLoader

DEF_AWS_IMAGE_PATH = '407798037446.dkr.ecr.us-west-2.amazonaws.com/nuvoloso'
DEF_GCP_IMAGE_PATH = 'gcr.io/nuvoloso'
DEF_AZURE_IMAGE_PATH = 'nuvoloso.azurecr.io'
DEF_INTERNAL_IMAGE_REPO_SECRET = 'internal-repo-secret'

class SmarterArgparseFormatter(argparse.RawDescriptionHelpFormatter):
    """
    Smarter argparse help formatter for description and argument help.
    Adapted from multiple solutions in
    https://stackoverflow.com/questions/3853722/python-argparse-how-to-insert-newline-in-the-help-text
    """

    def _fill_text(self, text, width, indent):
        """
        Description help formatter for argparse adapted from https://stackoverflow.com/a/43139055
        Minor fixes applied:
        - the call to _textwrap
        - re-formatted to pass pylint
        """
        if text.startswith('R|'):
            paragraphs = text[2:].splitlines()
            rebroken = [_textwrap.wrap(tpar, width) for tpar in paragraphs]
            rebrokenstr = []
            for tlinearr in rebroken:
                if not tlinearr:
                    rebrokenstr.append("")
                else:
                    for tlinepiece in tlinearr:
                        rebrokenstr.append(tlinepiece)
            return '\n'.join(rebrokenstr)
        return argparse.RawDescriptionHelpFormatter._fill_text(self, text, width, indent)

    def _split_lines(self, text, width):
        """
        Argument help formatter for argparse adapted from https://stackoverflow.com/a/22157136
        Minor fixes applied:
            - use python3 syntax
        """
        if text.startswith('R|'):
            return text[2:].splitlines()
        return super()._split_lines(text, width)


def load_certs(certs_dir):
    """
    Load all of the certificate, key and PEM files from the given directory.
    Only files with "crt", "key" and "pem" extentions are loaded.

    Returns: A dictionary of the file name keys (dots are removed and the names are camel-cased,
    eg "ca.crt" becomes "caCrt") to base64-encoded contents.
    """

    if not os.path.isdir(certs_dir):
        raise Exception('{0}: not found'.format(certs_dir))
    if not os.access(certs_dir, os.R_OK):
        raise Exception('{0}: not a readable directory'.format(certs_dir))
    certs = dict()
    for file in os.listdir(certs_dir):
        if file.endswith('.crt') or file.endswith('.key') or file.endswith('.pem'):
            parts = os.path.splitext(file)
            key = parts[0] + parts[1][1:].capitalize()
            path = os.path.join(certs_dir, file)
            with open(path, 'rb') as in_file:
                contents = in_file.read()
                contents = base64.b64encode(contents)
                certs[key] = contents.decode(encoding='ascii')
    if not certs:
        raise Exception('{0}: no recognized files'.format(certs_dir))
    return certs


def render_template(args, certs):
    """
    Generate the deployment template
    """
    env = Environment(loader=FileSystemLoader('.'))
    template_file = os.path.dirname(sys.argv[0]) + '/deployment.yaml.j2'
    template = env.get_template(template_file)
    t_args = dict(certs)
    t_args['configDbReplicas'] = args.configdb_replicas
    t_args['cspType'] = args.csp_type
    t_args['enableREI'] = args.enable_rei
    t_args['internal'] = args.internal
    t_args['imageTag'] = args.image_tag
    if args.internal:
        t_args['imagePath'] = args.internal_image_path
        t_args['imagePullSecretName'] = DEF_INTERNAL_IMAGE_REPO_SECRET
    else:
        t_args['imagePath'] = args.dockerhub_image_path
        t_args['imagePullSecretName'] = args.dockerhub_secret_name
    return template.render(t_args)


def get_parser():
    """
    Parse input arguments
    """
    parser = argparse.ArgumentParser(formatter_class=SmarterArgparseFormatter, description="""R|
Generate deployment YAML for customer or internal environments.

The customer environment YAML will create a placeholder Kubernetes secret
which will be referenced as the ImagePullSecret for Nuvoloso images
obtained from the Nuvoloso DockerHub repository. The same secret will be
created in the managed cluster deployment YAML that can be obtained from
the management server.

The internal YAML does not use an image pull secret as images are fetched
from internal repo such as AWS ECR or Google GCR.
    """)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('-c', '--customer', action='store_true', help="""
    Generate the customer deployment YAML.""")
    action_group.add_argument('-i', '--internal', action='store_true', help="""
    Generate the internal deployment YAML.""")
    parser.add_argument('-T', '--csp-type', choices=['AWS', 'Azure', 'GCP'], default='AWS',
                        help='The type of cloud service provider to which this deployment ' +
                        'is targetted. [%(default)s]')
    parser.add_argument('-r', '--configdb-replicas', type=int, choices=[1, 3], help="""
    Number of replicas for the configuration database. If unspecified, 1 is used for internal
    and 3 for customer.""")
    parser.add_argument('-t', '--image-tag', help="""
    The image tag version. [%(default)s]""", default='v1')
    parser.add_argument('-o', '--output-file', help="""R|Specify an output file name. The default
is to create a name of the form:
    {customer|internal}-<CSP_TYPE>-<IMAGE_TAG>.yaml
The name will be printed to stdout if defaulted.
Use '-' to send the output to stdout.""")
    parser.add_argument('--certs-dir', default='certs',
                        help='The path to the directory containing the generated ' +
                        'SSL certificates and keys [%(default)s]')
    parser.add_argument('--dockerhub-image-path',
                        help='The repository path for customer image access. [%(default)s]',
                        default='nuvolosocom')
    parser.add_argument('--internal-image-path',
                        help='The repository path for internal image access. ' +
                        'If unspecified a CSP-specific value is used: ' +
                        '%s for AWS, %s for Azure, %s for GCP.' % \
                            (DEF_AWS_IMAGE_PATH, DEF_AZURE_IMAGE_PATH, DEF_GCP_IMAGE_PATH))
    parser.add_argument('--dockerhub-secret-name', help="""
    The name of the Kubernetes secret object with the DockerHub
    credentials in a customer deployment. [%(default)s]""", default='customer-dockerhub-secret')
    parser.add_argument('--enable-rei', action='store_true',
                        help='Enable error injection in the centrald service')
    return parser


def parse_args_and_render():
    """
    Parse the command line flags and render the desired template
    """
    parser = get_parser()
    args = parser.parse_args()
    if not args.configdb_replicas:
        if args.internal:
            args.configdb_replicas = 1
        else:
            args.configdb_replicas = 3
    if not args.internal_image_path:
        args.internal_image_path = DEF_AWS_IMAGE_PATH
        if args.csp_type == 'GCP':
            args.internal_image_path = DEF_GCP_IMAGE_PATH
        elif args.csp_type == 'Azure':
            args.internal_image_path = DEF_AZURE_IMAGE_PATH
    certs = load_certs(args.certs_dir)
    res = render_template(args, certs)
    filename = args.output_file
    if not filename:
        if args.internal:
            filename = 'internal-' + args.csp_type + '-' + args.image_tag + '.yaml'
        else:
            filename = 'customer-' + args.csp_type + '-' + args.image_tag + '.yaml'
    if filename == '-':
        print(res)
    else:
        with open(filename, "w+") as out_file:
            out_file.write(res)
            out_file.write("\n")
        if not args.output_file:
            print(filename)


# launch the program
if __name__ == '__main__':
    parse_args_and_render()
