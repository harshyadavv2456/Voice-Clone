# Client examples

Start the local server from the repository root after downloading a fine-tuned model:

    export VOICE_MODEL_PATH="$PWD/models/harsh-yadav-qwen3-voice"
    export VOICE_SPEAKER="harsh_yadav"
    python serve_local.py

The server uses 127.0.0.1:8765 by default. Your application sends a POST request to /v1/audio/speech with a JSON body containing input and optionally voice; it receives WAV bytes. Examples are provided for Python and Node.js.

Do not expose the unauthenticated local server on a public IP. For a remote app, run the model on a secured server and add authentication and rate limits before exposing an endpoint.
