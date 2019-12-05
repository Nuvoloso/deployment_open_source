#!/bin/bash
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
docker image prune -f

if [ -z "$DOCKER_TAG" ]; then
  export DOCKER_TAG='*'
fi

cat > JenkinsResults.xml << EOF
<section name="Results" fontcolor="">
  <field name="Docker images" value="created">
    <![CDATA[
EOF
docker image ls *.amazonaws.com/nuvoloso/*:"$DOCKER_TAG">> JenkinsResults.xml
if [ "$JOB_NAME" = "ecr_acr_gcr_upload" ]; then
  echo '' >> JenkinsResults.xml
  docker image ls nuvoloso.azurecr.io/*:"$DOCKER_TAG" >> JenkinsResults.xml
  echo '' >> JenkinsResults.xml
  docker image ls gcr.io/nuvoloso/*:"$DOCKER_TAG">> JenkinsResults.xml
fi
cat >> JenkinsResults.xml << EOF
     ]]>
  </field>
</section>
EOF
echo SUCCESS
exit 0
