# Nuvoloso Deployment Repository
This repository contains tools and scripts for creating a container-based deployment of Nuvoloso using Kubernetes.

- [Container assembly](#container-assembly)
- [Deployment assembly](#deployment-assembly)
   - [Internal deployment YAML](#internal-deployment-yaml)
   - [Customer deployment YAML](#customer-deployment-yaml)
   - [Advanced usage](#advanced-usage)

## Container assembly
Construction of container images is intended to be done with Jenkins jobs that import artifacts from multiple repositories and
build *all* the docker images necessary for deployment.
In general, all these images should be tagged consistently.

The imported artifacts should supply the Dockerfiles required to build the images and all the required content.
This repo itself contains the Dockerfile for the nginx frontend.

The "tools" repo supplies the certificate construction support for the built-in development certificates.

See also:
- https://jenkins.nuvoloso.com:8443/job/deployment-parameterized-flex/
- https://jenkins.nuvoloso.com:8443/job/deployment-parameterized/

## Deployment assembly
The YAML describing the Nuvoloso management application is constructed by the `make_deployment.sh` script
which invokes the `generator/make_deployment.py` script in a `python3` virtual environment.
The contents of the YAML will vary depending on whether it is intended for internal use or for a customer.

The source for the deployment is a [Jinja2](http://jinja.pocoo.org/) template named `generator/deployment.yaml.j2`.

### Internal deployment YAML
To create the standard YAML deployment for internal use do the following:
```sh
make internal-yaml CERTS_DIR=$HOME/src/tools/certs
```
This will construct the `python3` virtual environment and generate a file named `internal-v1.yaml`
in the current directory with default values.
You may need to customize the `CERTS_DIR` value (it defaults to 'certs' and can also be specified as an environment variable)
if you have cloned the tools repo to another location.
This may already have been done via Jenkins.

### Customer deployment YAML
The customer YAML includes a *placeholder* Kubernetes secret that will be used as the `ImagePullSecret`
to access container images from the Nuvoloso Docker repository.
The secret is also made available to the management server so that it can be incorporated into
the cluster deployment YAML generated at run time.

The customer is responsible for replacing the content of this secret with *real*
authentication data corresponding to their Docker Hub account.
(See [Pull an Image from a Private Registry](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)
in the Kubernetes document for details on how to construct such a secret value.)
The customer Docker Hub account used must be authorized to access the Nuvoloso Docker repository
(a process that is not defined here).

To construct the customer YAML do the following:
```sh
make customer-yaml CERTS_DIR=$HOME/src/tools/certs
```
This will construct the `python3` virtual environment and generate a file named `customer-v1.yaml`
in the current directory with default values.
You may need to customize the `CERTS_DIR` value (it defaults to 'certs' and can also be specified as an environment variable)
if you have cloned the tools repo to another location.
This may already have been done via Jenkins.

### Advanced usage
The `make_deployment.sh` script offers some additional options that are intended mainly for developers.
Run the script with the `-h` flag to view the possible options.

The image tag can be explicitly specified with the `-t` flag. For example:
```sh
make venv # if not already present
./make_deployment.sh -c -t mytag --certs-dir=$HOME/src/tools/certs # produces customer-mytag.yaml
./make_deployment.sh -i -t mytag --certs-dir=$HOME/src/tools/certs # produces internal-mytag.yaml
```

The `--certs-dir` option must be specified (customize as required) if `./certs` does not contain the certificates.

The output file name can be explicitly specified or the output viewed on stdout with the `-o` flag.

The default image paths for DockerHub or Amazon ECR can be modified. This is useful
for a developer to set up an internal deployment that emulates the customer deployment
in which the image pull secret is present:
```sh
./make_deployment.sh -c --dockerhub-image-path 407798037446.dkr.ecr.us-west-2.amazonaws.com/nuvoloso --certs-dir=$HOME/src/tools/certs -o flipped.yaml
```
The output file will need to be edited to remove the `imagePullSecrets` directives and the
deployment may then be used internally.  This enables validation of the generated
cluster deployment that is expected to embed the same image pull secret; to actually
run the generated cluster deployment yaml, it too will have to be tweaked by removing
the `imagePullSecrets` directives.
