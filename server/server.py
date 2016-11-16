#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import render_template, Flask
from flask import send_from_directory
from flask.ext.socketio import SocketIO, emit
import getpass
from qpx import qpx
import json

app = Flask(__name__)
socketio = SocketIO(app)

user_name = getpass.getuser().capitalize()


@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


@app.route('/')
def hello():
    return app.send_static_file('index.html')


@socketio.on('message')
def socket_message(message):
    query = message["query"]
    if " to " in query:
        origin = query[:query.index(" to ")].upper()
        destination = query[query.index(" to ")+len(" to "):].upper()
        request = {
            "request": {
                "passengers": {
                    "adultCount": 1
                },
                "slice": [
                    {
                        "date": "2016-12-09",
                        "origin": origin,
                        "destination": destination
                    }
                ]
            }
        }
        print(json.dumps(request, indent=4))
        flights = qpx.extract_flights(qpx.get_flights(request))
        if flights is None or len(flights) == 0:
            lines = ["Sorry, I couldn't find any flights from %s to %s." % (origin, destination)]
        elif len(flights) <= 10:
            lines = ["Here are the %i flights I could find:" % len(flights)] + list(map(qpx.stringify, flights))
        else:
            lines = ["I found %i flights in total but I will only show the first 10 flights:" % len(flights)] + list(map(qpx.stringify, flights[:10]))
    else:
        lines = ["Sorry, %s, I didn't understand your query." % user_name]
    emit('message', {
        'type': 'answer',
        'lines': lines
    })


@socketio.on('my broadcast event')
def socket_message(message):
    emit('message', {'data': message['data']}, broadcast=True)


@socketio.on('connect')
def socket_connect():
    emit('message', {
        'type': 'greeting',
        'lines': [
            ("Hello %s!" % user_name),
            "I'm your personal assistant to help you find the best flight 😊"
        ]
    })
    print("New user connected")


@socketio.on('disconnect')
def socket_disconnect():
    print('Client disconnected')
