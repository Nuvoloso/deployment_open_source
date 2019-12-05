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

.phony: all lint internal-yaml customer-yaml clean

# Change the image version in release branches
IMAGE_VERSION=v1

# Path to directory with generated certs, can be specified on the command line or in the environment
CERTS_DIR?=certs

all: lint

LINT_DIRS=generator
lint: venv
	find $(LINT_DIRS) -name \*.py | xargs -n1 -t venv/bin/pylint

venv:
	python3 -m venv venv
	venv/bin/pip3 install --upgrade pip
	venv/bin/pip3 install pylint jinja2

# this target provides the automated test scripts with a predefined deployment file
nuvodeployment.yaml: venv
	./make_deployment.sh -i -t $(IMAGE_VERSION) --certs-dir=$(CERTS_DIR) -o $@

internal-yaml: venv
	./make_deployment.sh -i -t $(IMAGE_VERSION) --certs-dir=$(CERTS_DIR)

customer-yaml: venv
	./make_deployment.sh -c -t $(IMAGE_VERSION) --certs-dir=$(CERTS_DIR)

clean::
	$(RM) -r venv customer-*.yaml internal-*.yaml nuvodeployment.yaml
