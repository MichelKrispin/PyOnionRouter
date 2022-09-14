#!/usr/bin/env python3
import asyncio
import json
import os
import random
import time
import traceback
from uuid import uuid4

from flask import Flask, abort, jsonify, request
from flask_cors import CORS, cross_origin

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADER'] = 'Content-Type'

routes = {}


@app.route('/')
def index():
    """Show information for logging purposes."""
    return jsonify({'routes': routes})


# ----------------
# Get the route and instantiate the gcloud container
# ----------------


async def run(cmd, name='', ret=None, p_stdout=False, p_stderr=True):
    """ Run the command asynchronously in the shell.

    Args:
        cmd (str): The command to execute.
        name (str, optional): An output name for logging. Defaults to ''.
        ret (str, optional): If not None, which output should be returned. Defaults to None.
        p_stdout (bool, optional): Print stdout. Defaults to False.
        p_stderr (bool, optional): Print stderr. Defaults to True.

    Returns:
        _type_: _description_
    """
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    print(f'[{name if name else cmd!r} -> {proc.returncode}]')
    if p_stdout and stdout:
        print(f'[stdout]\n{stdout.decode()}')
    if ret == 'stdout' and stdout:
        return stdout.decode()
    if p_stderr and stderr:
        print(f'[stderr]\n{stderr.decode()}')
    if ret == 'stderr' and stderr:
        return stderr.decode()
    if ret:
        return 'No output.'


async def stop_nodes(node_ids):
    """Shut down the nodes GCloud services with the given names.
    Shutdown call happens asynchronously.
    
    Args:
        node_ids (List[str]): The node ids to shut down. 3 overall.
    """
    cmd = "gcloud run services delete node-{node_id} -q --region europe-west3"

    await asyncio.gather(
        run(cmd.format(node_id=node_ids[0]), f'stop node-{node_ids[0]}'),
        run(cmd.format(node_id=node_ids[1]), f'stop node-{node_ids[1]}'),
        run(cmd.format(node_id=node_ids[2]), f'stop node-{node_ids[2]}'))


async def instantiate_nodes(public_key, directory_service_url,
                            directory_repo_url, node_ids, tracking_id):
    """Instantiates the nodes with the given node_ids by using the gcloud cli.
    Are instantiates asynchronously to speed up the process.

    Args:
        public_key (str): The public key of the client to pass on.
        directory_service_url (str): This directory nodes URL to pass on.
        directory_repo_url (str): The repository from which to pull the node images.
        node_ids (List[str]): Node ids for the GCloud service name (e.g. node-014).
        tracking_id (str): Unique tracking id of the route for notification service.
    """
    cmd = """\
PUBLIC_KEY="{public_key}"
DIRECTORY_NODE="{directory_service_url}"

gcloud run deploy node-{idx} --region europe-west3 --allow-unauthenticated \
    --image {directory_repo_url} \
    --set-env-vars="PUBLIC_KEY=$PUBLIC_KEY" \
    --set-env-vars="DIRECTORY_NODE=$DIRECTORY_NODE" \
    --set-env-vars="THIS_NODE={node_url}" \
    --set-env-vars="TRACKING_ID={tracking_id}"
    """
    await asyncio.gather(
        run(
            cmd.format(public_key=public_key,
                       directory_service_url=directory_service_url,
                       directory_repo_url=directory_repo_url,
                       node_url=directory_service_url.replace(
                           'directory', f'node-{node_ids[0]}'),
                       idx=node_ids[0],
                       tracking_id=tracking_id), f'deploy node-{node_ids[0]}'),
        run(
            cmd.format(public_key=public_key,
                       directory_service_url=directory_service_url,
                       directory_repo_url=directory_repo_url,
                       node_url=directory_service_url.replace(
                           'directory', f'node-{node_ids[1]}'),
                       idx=node_ids[1],
                       tracking_id=tracking_id), f'deploy node-{node_ids[1]}'),
        run(
            cmd.format(public_key=public_key,
                       directory_service_url=directory_service_url,
                       directory_repo_url=directory_repo_url,
                       node_url=directory_service_url.replace(
                           'directory', f'node-{node_ids[2]}'),
                       idx=node_ids[2],
                       tracking_id=tracking_id), f'deploy node-{node_ids[2]}'))


def generate_route(public_key, tracking_id):
    """ Generates a route by passing the public key to each node
    and instantiates them.

    Might throw an exception.

    Args:
        public_key (str): The public key of the client.
        tracking_id (str): A unique id to remember this route.

    Returns:
        List[str]: A list of nodes with their URLs.
    """
    cmd_get_service_url = 'gcloud run services describe directory --region europe-west3 --format=json'

    # Get repo URL and URL of this node and remove the trailing new line
    data_raw = asyncio.run(
        run(cmd_get_service_url,
            '',
            ret='stdout',
            p_stdout=False,
            p_stderr=False))
    data = json.loads(data_raw)
    directory_service_url = data['status']['url']
    directory_repo_url = data['spec']['template']['metadata']['annotations'][
        'client.knative.dev/user-image']
    directory_repo_url = directory_repo_url.replace('directory', 'node')

    # Generate three random nodes that do not exist yet
    existent_ids = [
        int(node.split('-')[1]) for tracking in routes.keys()
        for node in routes[tracking]
    ]
    ids = []
    while len(ids) < 3:
        v = random.randint(1, 99)
        if v not in ids or v not in existent_ids:
            ids.append(v)
    node_ids = [f'{ids[0]:03d}', f'{ids[1]:03d}', f'{ids[2]:03d}']
    asyncio.run(
        instantiate_nodes(public_key, directory_service_url,
                          directory_repo_url, node_ids, tracking_id))
    node_urls = [
        directory_service_url.replace('directory', f'node-{node_id}')
        for node_id in node_ids
    ]
    return node_urls


@app.route('/route', methods=['POST'])
def get_route():
    """Get a random route of registered nodes.
    Does not affect any data at the directory node

    Returns:
        json: A route of three nodes in random order.
    """
    print(request.get_data())
    try:
        print(f'Asking for a route with {request.json}')
        if not request.json or not 'public_key' in request.json:
            return jsonify(
                {'error': 'public_key has to be send to get a route.'}), 400
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400

    tracking_id = uuid4().hex
    try:
        route = generate_route(request.json['public_key'], tracking_id)
        globals()['routes'][tracking_id] = {node: 2 for node in route}
        return jsonify({'tracking_id': tracking_id, 'route': route})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 400


@app.route('/notify', methods=['POST'])
def notify():
    """
    Gets called by the node which notify their status: Success or failure.
    Updates the global existing routes dict so that the client can then
    ask for failures in the node sending process.

    Expects a POST request with json data:
    {'status': 'success/error msg', 'node_address': node_url, 'tracking_id': unique_id_of_route}
    """
    if (not request.json or not 'status' in request.json
            or not 'node_address' in request.json
            or not 'tracking_id' in request.json):
        error = 'No json found in request'
        if request.json:
            error = request.json
        print(f'[ERROR] Node error in request /notify: {error}')
        abort(400)
    tracking_id = request.json['tracking_id']
    node_address = request.json['node_address']
    try:
        if request.json['status'] == 'success':
            globals()['routes'][tracking_id][node_address] -= 1
        else:
            globals(
            )['routes'][tracking_id][node_address] = request.json['status']
    except Exception as e:
        traceback.print_exc()
        print(f'[ERROR] Node error at /notify: {str(e)}')
    return jsonify({'success': True})


@app.route('/check', methods=['POST'])
@cross_origin()
def check():
    """
    Gets called by the client to check for any errors that might have
    appeared in the node sending process.

    Expects a POST request with json data:
    {'tracking_id': unique_id_of_route}
    """
    if not request.json or not 'tracking_id' in request.json:
        return jsonify(
            {'error':
             'tracking_id has to be send to identify the route.'}), 400
    if not request.json['tracking_id'] in globals()['routes']:
        return jsonify({
            'error':
            f'The given tracking_id is not valid anymore.\nAsked for {request.json["tracking_id"]}'
        }), 400
    response = {}
    num_iterations = 1000
    for idx in range(num_iterations):
        values = globals()['routes'][request.json['tracking_id']]
        num_correct = 0
        for key in values:
            if type(values[key]) == str:
                response = {'error': f'Error at {key}: {values[key]}'}
                break
            elif values[key] <= 0:
                num_correct += 1
                if num_correct == 3:
                    response = {'status': 'success'}
                    break
            elif idx == num_iterations - 1:
                response = {'error': 'Timeout'}
                break
        time.sleep(0.001)
    node_ids = [
        adr[adr.find('node-') + 5:adr.find('node-') + 8]
        for adr in globals()['routes'][request.json['tracking_id']]
    ]
    print(f'Stopping nodes:\n' + '\n'.join(node_ids))
    asyncio.run(stop_nodes(node_ids))
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True, port=os.getenv('PORT', 8888), host='0.0.0.0')
