#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid

import eventlet
from flask import Flask, send_from_directory, session
from flask_socketio import SocketIO, emit
from system import Pipeline

app = Flask(__name__)
app.secret_key = uuid.uuid4()
socketio = SocketIO(app)


@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


@app.route('/')
def hello():
    return app.send_static_file('index.html')


@socketio.on('message')
def socket_message(message):
    query = message["query"]
    for output in session["system"].input(query):
        if isinstance(output, str):
            emit('message', {
                'type': 'progress',
                'lines': [output]
            })
        else:
            emit('message', {
                'type': output.output_type.name,
                'lines': output.lines
            })
        eventlet.sleep(0)
    emit('state', session["system"].user_state())


@socketio.on('my broadcast event')
def socket_message(message):
    emit('message', {'data': message['data']}, broadcast=True)


@socketio.on('connect')
def socket_connect():
    session["system"] = Pipeline()
    for output in session["system"].output():
        emit('message', {
            'type': output.output_type.name,
            'lines': output.lines
        })
    emit('state', session["system"].user_state())
    print("New user connected")


@socketio.on('disconnect')
def socket_disconnect():
    print('User disconnected')

if __name__ == '__main__':
    socketio.run(app)
