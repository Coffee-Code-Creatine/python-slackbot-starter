import time
from flask import Flask, jsonify, request
import json
import hmac
import hashlib
import requests

app = Flask(__name__)

slack_signing_secret = "8e07f2dc80edcad0fd83abb73ba1b2ce"
message_url = "https://slack.com/api/chat.postMessage"
token = "xoxb-470864710675-3685068422261-RAccnoN7xdozus7ckCyOHg78"


@app.route("/health-check")
def alive():
    return jsonify({"health": "server is up and running"})


@app.route('/event-consumer', methods=["POST"])
def consume_event():
    if message_secure(request):
        payload_json = request.get_json()
        print("log: json payload: " + str(payload_json))



        if "url_verification" == payload_json.get("type"):
            return jsonify({"challenge": request.get_json().get("challenge")})

        # Payload parsing
        event = payload_json.get("event")
        if "bot_id" in event:
            print("log: we dont want to talk to ourself")
            return jsonify({"challenge": request.get_json().get("challenge")})

        type = event.get("type")
        text = event.get("text")
        print("log: event type: " + str(type))
        print("log: event text: " + str(text))
        payload = {}
        headers = {}
        headers["Authorization"] = "Bearer " + token
        headers["Content-type"] = "application/json"

        # Logic to determine response type
        if type == "app_mention":
            if "secret" in text:
                print("log: should respond in private message")
                payload["channel"] = "D03L7T9MD51"
                payload["text"] = "I would love to hear a secret, but we should talk in a private channel"
                response = requests.post(message_url, headers=headers, data=json.dumps(payload))
                print("log: response code: " + str(response.status_code))
                response_payload = response.json()
                print("log: " + str(response_payload))

            else:
                print("log: should respond publicly")
                payload["channel"] = "CE9KC9PP1"
                payload["text"] = "I heard my name"
                response = requests.post(message_url, headers=headers, data=json.dumps(payload))
                print("log: response code: " + str(response.status_code))
                response_payload = response.json()
                print("log: " + str(response_payload))

        elif type == "message":
            if "shh" in text:
                return jsonify({"challenge": request.get_json().get("challenge")})
            print("log: should respond in private message")
            payload["channel"] = "D03L7T9MD51"
            payload["text"] = "I love sending messages"
            response = requests.post(message_url, headers=headers, data=json.dumps(payload))
            print("log: response code: " + str(response.status_code))
            response_payload = response.json()
            print("log: " + str(response_payload))


        return jsonify({"challenge": request.get_json().get("challenge")})

    print("log: message provided failed challenge")
    return jsonify({"challenge": None})


def message_secure(request):
    request_body = request.get_json()
    timestamp = request.headers.get("X-Slack-Request-Timestamp")

    print("log: request body: " + str(request_body))
    print("log: timestamp header: " + str(timestamp))

    if abs(time.time() - float(timestamp)) > 60 * 5:
        print("log: message provided failed challenge: timestamp outside range")
        return jsonify({"challenge": None})

    sig_basestring = 'v0:' + timestamp + ':' + request.get_data().decode("utf-8")
    print("log: sig_basestring: " + sig_basestring)

    # Convert to byte array
    key_bytes = bytearray()
    key_bytes.extend(map(ord, slack_signing_secret))

    message_bytes = bytearray()
    message_bytes.extend(map(ord, sig_basestring))

    h = hmac.new(key_bytes, message_bytes, hashlib.sha256)
    my_signature = "v0=" + h.hexdigest()
    slack_signature = request.headers.get("X-Slack-Signature")

    print("log: slack signature: " + str(slack_signature))
    print("log: computed signature: " + str(my_signature))

    if hmac.compare_digest(my_signature, slack_signature):
        print("log: message is secure")
        return True

    print("log: message is not secure")
    return False


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
        payload = request.get_json()
        event = payload.get("event")
        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text")

        if text.contains("secret"):
            payload = {"text": "yes I want to hear a secret!"}
            response = requests.post(final_url, data=json.dumps(payload))

        elif not text.contains("secret"):
            payload = {"text": "You called?"}
            response = requests.post(final_url, data=json.dumps(payload))

        # Do work here
        final_url = "https://hooks.slack.com/services/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"

        return jsonify({"challenge": request.get_json().get("challenge")})

    print("INVALID PAYLOAD")
    return jsonify({"challenge": None})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, use_reloader=False, threaded=True)
