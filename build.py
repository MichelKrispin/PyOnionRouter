#!/usr/bin/env python3
import subprocess
import sys

PREFIX = '\n\x1b[4m➤ '
SUFFIX = '\x1b[0m [y/N] '

LOCATION = 'europe-west3'
LOCATION_NICE_NAME = 'Frankfurt'

REPOSITORY = 'router-repo'


def notify(msg, prefix=None, divider=False):
    suffix = ''
    if divider:
        suffix = '\n' + 62 * '-'
    if prefix == 'tick':
        prefix = '\x1b[32m✓\x1b[0m '
    elif prefix == 'cross':
        prefix = '\x1b[31m✗\x1b[0m '
    else:
        prefix = '⟳ '
    print(f"""\
╔════════════════════════════════════════════════════════════╗
╠═ {prefix}{msg: <55}═╣
╚════════════════════════════════════════════════════════════╝{suffix}""")


def ask(msg):
    response = ''
    while 'y' != response and 'n' != response and 'N' != response:
        print(f'{PREFIX}{msg:<60}{SUFFIX}', end='')
        response = input().strip()
    return response == 'y'


def cmd_output(msg, err=False):
    out = ''
    for s in msg.split('\n'):
        if len(s) > 58:
            s = s[:55] + '...'
        out += f'│ {s: <59}│\n'
    out += '└────────────────────────────────────────────────────────────┘'
    print(f'{out}')


def run_cmd(cmd, special=False):
    """Runs a command and outputs it.

    Args:
        cmd (List[str]): The command list

    Returns:
        Tuple[str, str]: (stdout, stderr)
    """
    cmd_print = ' '.join(cmd)
    if len(cmd_print) > 58:
        cmd_print = cmd_print[:55] + '...'
    print(f"""\
┌────────────────────────────────────────────────────────────┐
│ \x1b[1m{cmd_print: <59}\x1b[0m│
├────────────────────────────────────────────────────────────┤""")
    if special:
        p = subprocess.run([' '.join(cmd)],
                           capture_output=True,
                           text=True,
                           shell=True)
        return p.stdout.strip(), p.stderr.strip()
    else:
        p = subprocess.Popen(cmd,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        try:
            out = out.decode('utf-8').strip()
            err = err.decode('utf-8').strip()
        except Exception as e:
            print('Panic!!! run_cmd: ' + str(e))
            sys.exit(-1)
        return out, err


def run_and_print(cmd, special=False):
    out, err = run_cmd(cmd, special)
    if err:
        cmd_output(err, True)
        return False
    cmd_output(out)
    return True


# --- GCloud ---


def check_for_gcloud_login():
    """
    Checks whether there is a credentialed account in the output.
    Returns True if one can be found, otherwise it asks for continuation or returns False.

    Returns:
        Bool: True if logged in.
    """
    out, err = run_cmd(['gcloud', 'auth', 'list'])
    if out and 'ACTIVE' in out:
        cmd_output(out)
        return True
    else:
        cmd_output(err, True)
        notify(
            'You are probably not logged into GCloud. Please run `gcloud auth login` and rerun this script.',
            prefix='cross')
        return ask('Do you still want to continue?')


def check_for_gcloud_project():
    out, err = run_cmd(["gcloud config list --format 'value(core.project)'"],
                       special=True)
    if err:
        cmd_output(err, True)
        notify('Something bad happened with GCloud...', prefix='cross')
        return ask('Do you still want to continue?')
    cmd_output(out)
    if not out:
        notify('It seems that you do not have a project set.', prefix='cross')
        notify('Please change it with `gcloud config set project <name>`.',
               prefix='cross')
        return None
    use_it = ask(
        f'Currently [{out}] is the active project. Do you want to use it?')
    if not use_it:
        notify(
            'Then please change it yourself (`gcloud config set project <name>`).',
            prefix='cross')
        return None
    return out


def check_for_service(name, print_name):
    out, err = run_cmd(['gcloud', 'services', 'list', '--enabled'])
    if err:
        cmd_output(err, True)
        notify('Something bad happened with GCloud...', prefix='cross')
        if not ask('Do you still want to continue?'):
            sys.exit(-1)
    else:
        cmd_output(out)
    if name in out:
        notify(f'{print_name} enabled.', prefix='tick')
    else:
        notify(f'{print_name} not enabled yet.', prefix='cross')
        if ask(f'Enable {print_name} in GCloud?'):
            out, err = run_cmd(['gcloud', 'services', 'enable', name])
            # Prints everything to stderr
            cmd_output(err)
            notify(f'{print_name} enabled', prefix='tick')


def check_for_services(project_id):
    # Check if the services are enabled and if not, enable them
    check_for_service('run.googleapis.com', 'Cloud Run API')
    check_for_service('artifactregistry.googleapis.com', 'Artifact Registry')

    # Check if REPOSITORY already exists
    out, err = run_cmd([
        'gcloud', 'artifacts', 'repositories', 'list',
        f'--project={project_id}'
    ])
    cmd_output(err if err else out, True if err else False)
    if REPOSITORY in out:
        notify(f'{REPOSITORY} already exists.', prefix='tick')
        return

    # Create a new repository
    if not ask(
            'A new Artifact Registry repository will be created next. Continue?'
    ):
        sys.exit(-1)
    out, err = run_cmd([
        'gcloud', 'artifacts', 'repositories', 'create', REPOSITORY,
        '--repository-format=docker', f'--location={LOCATION}'
    ],
                       special=True)
    cmd_output(err if err else out, True if err else False)
    notify(f'Created a new Artifact Repository (`{REPOSITORY}`)',
           prefix='tick',
           divider=True)
    notify('All services enabled', prefix='tick')


def start_gcloud_services(project_id):
    service_urls = []
    for service in ['directory', 'service', 'client']:
        service_url = f'{LOCATION}-docker.pkg.dev/{project_id}/{REPOSITORY}/{service}'
        out, err = run_cmd([
            'gcloud', 'run', 'deploy', service, f'--region={LOCATION}',
            '--allow-unauthenticated', '--image', service_url
        ])
        out.replace(10 * '.', '')  # Remove a lot of dots
        cmd_output(err if err else out, True if err else False)
        notify(f'Deployed {service}', prefix='tick')
        out, err = run_cmd([
            'gcloud', 'run', 'services', 'describe', service, '--region',
            LOCATION, '--format="value(status.url)"'
        ],
                           special=True)
        cmd_output(out)
        service_urls.append(out)
    return service_urls


# --- Docker ---


def build_docker_container(use_sudo):
    build_cmd = ['docker', 'build', '-t']
    if use_sudo:
        build_cmd = ['sudo'] + build_cmd
    if not run_and_print(build_cmd + ['directory', 'DirectoryNode/.']):
        return False
    if not run_and_print(build_cmd + ['node', 'IntermediateNode/.']):
        return False
    if not run_and_print(build_cmd + ['service', 'Service/.']):
        return False
    if not run_and_print(build_cmd + ['client', 'Originator/.']):
        return False
    return True


def pull_docker_container(use_sudo):
    build_cmd = ['docker', 'pull']
    if use_sudo:
        build_cmd = ['sudo'] + build_cmd
    if not run_and_print(build_cmd + ['michelkrispin/directory']):
        return False
    if not run_and_print(build_cmd + ['michelkrispin/node']):
        return False
    if not run_and_print(build_cmd + ['michelkrispin/service']):
        return False
    if not run_and_print(build_cmd + ['michelkrispin/client']):
        return False
    # Tag them correctly when locally existent
    build_cmd = ['docker', 'tag']
    if use_sudo:
        build_cmd = ['sudo'] + build_cmd
    if not run_and_print(build_cmd + ['michelkrispin/directory', 'directory']):
        return False
    if not run_and_print(build_cmd + ['michelkrispin/node', 'node']):
        return False
    if not run_and_print(build_cmd + ['michelkrispin/service', 'service']):
        return False
    if not run_and_print(build_cmd + ['michelkrispin/client', 'client']):
        return False
    return True


def push_docker_container(project_id, use_sudo):
    out, err = run_cmd([
        'gcloud', 'auth', 'configure-docker', f'{LOCATION}-docker.pkg.dev',
        '--quiet'
    ])
    cmd_output(out if out else err)
    for service in ['directory', 'node', 'service', 'client']:
        service_url = f'{LOCATION}-docker.pkg.dev/{project_id}/{REPOSITORY}/{service}'
        build_cmd = ['docker', 'tag', service, service_url]
        if use_sudo:
            build_cmd = ['sudo'] + build_cmd
        if not run_and_print(build_cmd):
            sys.exit(-1)
        build_cmd = ['docker', 'push', service_url]
        if not run_and_print(build_cmd):
            sys.exit(-1)
        notify(f'Successfully pushed {service} to GCloud', prefix='tick')


# --- Main ---
if __name__ == '__main__':
    if not ask('Helper script to start (upload) the Onion Router. Continue?'):
        sys.exit(-1)

    if not ask(
            f'Using {LOCATION} ({LOCATION_NICE_NAME}) as the location for GCloud. Continue?'
    ):
        notify('Please change the location at the top of this script.',
               prefix='cross')
        sys.exit(-1)

    # --- GCloud ---
    notify('Checking if logged in to GCloud first.')
    if not check_for_gcloud_login():
        sys.exit(-1)
    notify('You are logged in to GCloud.', prefix='tick', divider=True)

    notify('Checking for active GCloud project.')
    project_id = check_for_gcloud_project()
    if not project_id:
        sys.exit(-1)
    notify(f'Saving {project_id} for later use.', prefix='tick')

    notify('Checking for active services (registry/run)')
    check_for_services(project_id)

    # --- Docker ---
    use_sudo = ask('Do you need sudo to run Docker?')
    if ask('Do you want to build the Docker containers yourself?'):
        # Build Docker container
        notify('Running the build commands now')
        if not build_docker_container(use_sudo):
            notify('Exiting.. There is an error with Docker.', prefix='cross')
            sys.exit(-1)
        notify('Successfully built the Docker container.', prefix='tick')
    else:
        # Pull from Docker Hub
        notify('Pulling the Docker container from Docker Hub.')
        if not pull_docker_container(use_sudo):
            notify('Exiting.. There is an error with Docker Pull.',
                   prefix='cross')
            sys.exit(-1)
        notify('Successfully built the Docker container.', prefix='tick')

    # Now tag and upload them to Artifact Registry
    notify('Uploading the Docker container to GCloud now.')
    push_docker_container(project_id, use_sudo)

    # Now start the directory, the service and the client.
    notify('Deploying services to GCloud now.')
    urls = start_gcloud_services(project_id)

    # Print the services nicely
    url_list = '\n'
    for name, url in zip(['directory', 'service', 'client'], urls):
        url_list += f'│ {name:<59}│\n│   🠖 {url:<55}│\n'
    print('┌────────────────────────────────────────────────────────────┐\n'
          f'│ \x1b[1m{"Services are up at": <59}\x1b[0m│' + url_list +
          '└────────────────────────────────────────────────────────────┘')

    # And finally print some information about how to stop everything
    print(
        'Stop everything:\n'
        'Option 1: Deleting the project\n'
        'Option 2: Run `./stop_services.sh`\n'
        'Option 3: Copy and paste the following lines into a terminal and run them:\n'
        '          (There might be some nodes still running. List them with\n'
        "           `gcloud run services list --format='value(name)'`)\n```\n"
        f'gcloud run services delete directory -q --region {LOCATION}\n'
        f'gcloud run services delete service -q --region {LOCATION}\n'
        f'gcloud run services delete client -q --region {LOCATION}\n```')
