import flask
from flask import request
import json
import mimetypes
import os

import decorators


site = flask.Flask(__name__)
site.config.update(
    SEND_FILE_MAX_AGE_DEFAULT=180,
    TEMPLATES_AUTO_RELOAD=True,
)
site.jinja_env.add_extension('jinja2.ext.do')
site.debug = True


####################################################################################################
####################################################################################################
####################################################################################################
####################################################################################################

def make_json_response(j, *args, **kwargs):
    dumped = json.dumps(j)
    response = flask.Response(dumped, *args, **kwargs)
    response.headers['Content-Type'] = 'application/json;charset=utf-8'
    return response

def send_file(filepath):
    '''
    Range-enabled file sending.
    '''
    try:
        file_size = os.path.getsize(filepath)
    except FileNotFoundError:
        flask.abort(404)

    outgoing_headers = {}
    mimetype = mimetypes.guess_type(filepath)[0]
    if mimetype is not None:
        if 'text/' in mimetype:
            mimetype += '; charset=utf-8'
        outgoing_headers['Content-Type'] = mimetype

    if 'range' in request.headers:
        desired_range = request.headers['range'].lower()
        desired_range = desired_range.split('bytes=')[-1]

        int_helper = lambda x: int(x) if x.isdigit() else None
        if '-' in desired_range:
            (desired_min, desired_max) = desired_range.split('-')
            range_min = int_helper(desired_min)
            range_max = int_helper(desired_max)
        else:
            range_min = int_helper(desired_range)

        if range_min is None:
            range_min = 0
        if range_max is None:
            range_max = file_size

        # because ranges are 0-indexed
        range_max = min(range_max, file_size - 1)
        range_min = max(range_min, 0)

        range_header = 'bytes {min}-{max}/{outof}'.format(
            min=range_min,
            max=range_max,
            outof=file_size,
        )
        outgoing_headers['Content-Range'] = range_header
        status = 206
    else:
        range_max = file_size - 1
        range_min = 0
        status = 200

    outgoing_headers['Accept-Ranges'] = 'bytes'
    outgoing_headers['Content-Length'] = (range_max - range_min) + 1

    if request.method == 'HEAD':
        outgoing_data = bytes()
    else:
        outgoing_data = helpers.read_filebytes(filepath, range_min=range_min, range_max=range_max)

    response = flask.Response(
        outgoing_data,
        status=status,
        headers=outgoing_headers,
    )
    return response


####################################################################################################
####################################################################################################
####################################################################################################
####################################################################################################

@site.route('/')
@decorators.give_session_token
def root():
    return flask.render_template('root.html')

@site.route('/favicon.ico')
@site.route('/favicon.png')
def favicon():
    filename = os.path.join('static', 'favicon.png')
    return flask.send_file(filename)

@site.route('/static/<filename>')
def get_static(filename):
    filename = filename.replace('\\', os.sep)
    filename = filename.replace('/', os.sep)
    filename = os.path.join('static', filename)
    return flask.send_file(filename)

@site.route("/float/<float:value>")
def float_type(value):
    print(value + 1)
    return "correct"

if __name__ == '__main__':
    #site.run(threaded=True)
    pass
