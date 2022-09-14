#!/usr/bin/env python3

PREFIX = '\n\x1b[4m➤ '
SUFFIX = '\x1b[0m '


def ask(msg, y_n=False):
    response = ''
    if y_n:
        while 'y' != response and 'n' != response and 'N' != response:
            print(f'{PREFIX}{msg:<40}{SUFFIX} [y/N] ', end='')
            response = input().strip()
        return response == 'y'
    while not response:
        print(f'{PREFIX}{msg}:{SUFFIX}', end='')
        response = input().strip()
    return response


DOCKER_COMMAND = {'build': []}

SHELL_SCRIPT = '''\
# Set the active project that will be used
gcloud config set project {project}

# Enable Artifact Registry and Cloud Run
gcloud services enable artifactregistry.googleapis.com
gcloud services enable run.googleapis.com

# Create a repository in the Artifact Registry if it doesn't exist yet
gcloud artifacts repositories list --project={project} --format='value(name)' 2> /dev/null | grep {repository}
if [ $? -ne 0 ]; then
    gcloud artifacts repositories create {repository} \\
        --repository-format=docker \\
        --location={location}
fi

# Create a new IAM role so that the Directory Node can instantiate nodes
# At least if it doesn't already exists
gcloud iam roles list --project={project} --format='value(title)' | grep "Directory Node Permission"
if [ $? -ne 0 ]; then
    gcloud iam roles create hello \
        --project {project} \
        --title "Directory Node Permission" \
        --description "This role has only the run.services.setIamPolicy permission" \
        --permissions run.services.setIamPolicy
fi
MEMBER=serviceAccount:$(gcloud projects describe {project} --format="value(projectNumber)")-compute@developer.gserviceaccount.com
gcloud projects add-iam-policy-binding {project} \
      --member=$MEMBER \
      --role='projects/{project}/roles/hello'

# Add the artifact registry to docker push
gcloud auth configure-docker {location}-docker.pkg.dev --quiet

# Build and push the directory node
# {sudo}docker build -t directory DirectoryNode/.
# {sudo}docker tag directory {location}-docker.pkg.dev/{project}/{repository}/directory
# Pull and push the directory node
{sudo}docker pull michelkrispin/directory
{sudo}docker tag michelkrispin/directory {location}-docker.pkg.dev/{project}/{repository}/directory
docker push {location}-docker.pkg.dev/{project}/{repository}/directory

# Build and push the intermediate node
# {sudo}docker build -t node IntermediateNode/.
# {sudo}docker tag node {location}-docker.pkg.dev/{project}/{repository}/node
# Pull and push the intermediate node
{sudo}docker pull michelkrispin/node
{sudo}docker tag michelkrispin/node {location}-docker.pkg.dev/{project}/{repository}/node
docker push {location}-docker.pkg.dev/{project}/{repository}/node

# Build and push the service
# {sudo}docker build -t service Service/.
# {sudo}docker tag service {location}-docker.pkg.dev/{project}/{repository}/service
# Pull and push the service
{sudo}docker pull michelkrispin/service
{sudo}docker tag michelkrispin/service {location}-docker.pkg.dev/{project}/{repository}/service
docker push {location}-docker.pkg.dev/{project}/{repository}/service

# Build and push the client
# {sudo}docker build -t client Originator/.
# {sudo}docker tag client {location}-docker.pkg.dev/{project}/{repository}/client
# Pull and push the client
{sudo}docker pull michelkrispin/client
{sudo}docker tag michelkrispin/client {location}-docker.pkg.dev/{project}/{repository}/client
docker push {location}-docker.pkg.dev/{project}/{repository}/client

# Deploy all services to the cloud
gcloud run deploy service --region {location} --allow-unauthenticated --image {location}-docker.pkg.dev/{project}/{repository}/service
gcloud run deploy directory --region {location} --allow-unauthenticated --image {location}-docker.pkg.dev/{project}/{repository}/directory
gcloud run deploy client --region {location} --allow-unauthenticated --image {location}-docker.pkg.dev/{project}/{repository}/client'''

if __name__ == '__main__':
    location = 'europe-west3'
    repository = 'router-repo'
    project = ''
    sudo = ''

    correct = False
    while not correct:
        project = ask('Please input the GCloud project id')
        correct = ask(f'GCloud project id: {project}. Correct?', True)

    correct = ask(f'GCloud location: {location}. Use that?', True)
    while not correct:
        project = ask('Please input the GCloud location')
        correct = ask(f'GCloud location: {location}. Correct?', True)

    correct = ask(f'GCloud repository: {repository}. Use that?', True)
    while not correct:
        project = ask('Please input the GCloud repository name')
        correct = ask(f'GCloud repository: {repository}. Correct?', True)

    if ask('Do you need sudo to run Docker?', True):
        sudo = 'sudo '

    build_script = SHELL_SCRIPT.format(project=project,
                                       location=location,
                                       repository=repository,
                                       sudo=sudo)
    with open('build.sh', 'w') as f:
        f.write(build_script)
    print('\n✓ Wrote the shell script to file. Run `sh build.sh`.')
