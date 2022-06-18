import os
import time
from slackeventsapi import SlackEventAdapter
from flask import Flask, jsonify, request
from math import fabs
import hmac
import json
import hmac
import hashlib
import base64

app = Flask(__name__)


@app.route("/health-check")
def alive():
    return jsonify({"health": "server is up and running"})


@app.route('/events', methods=["POST"])
def request_validation():
    # Signing secret for the app
    slack_signing_secret = "8e07f2dc80edcad0fd83abb73ba1b2ce"

    request_body = request.get_json()
    timestamp = request.headers.get("X-Slack-Request-Timestamp")

    print("REQUEST BODY: " + str(request_body))
    print("TIMESTAMP: " + str(timestamp))

    if abs(time.time() - float(timestamp)) > 60 * 5:
        print("FAILED TIME STAMP CHECK")
        return jsonify({"challenge": None})

    sig_basestring = 'v0:' + timestamp + ':' + request.get_data().decode("utf-8")
    print("SIG_BASESTRING: " + sig_basestring)

    # Convert to byte array
    key_bytes = bytearray()
    key_bytes.extend(map(ord, slack_signing_secret))

    message_bytes = bytearray()
    message_bytes.extend(map(ord, sig_basestring))

    h = hmac.new(key_bytes, message_bytes, hashlib.sha256)
    my_signature = "v0=" + h.hexdigest()
    slack_signature = request.headers.get("X-Slack-Signature")

    print("SLACK_SIGNATURE: " + str(slack_signature))
    print("MY_SIGNATURE: " + str(my_signature))

    if hmac.compare_digest(my_signature, slack_signature):
        print("VALID PAYLOAD")
        return jsonify({"challenge": request.get_json().get("challenge")})

    print("INVALID PAYLOAD")
    return jsonify({"challenge": None})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, use_reloader=False, threaded=True)
