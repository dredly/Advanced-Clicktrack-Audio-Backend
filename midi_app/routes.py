from flask import request
from midi_app import app
from .audio_processing import make_midi_file, make_wav_file
from .file_management import upload_file

#Health check to quickly verify if the API is running or not
@app.route("/")
def home():
    return {"marco": "polo!!!"}

@app.route("/api/make_midi", methods=["POST"])
def make_midi() -> dict:
    data = request.json
    tempo_data: dict = data["tempoData"]
    time_sig_data: dict = data["timeSigData"]
    midi_filename = make_midi_file(tempo_data, time_sig_data)
    midi_url = upload_file(midi_filename)
    return {"url": midi_url} if midi_url != "error" else {"error": "Something went wrong with the file"}


@app.route("/api/make_wav", methods=["POST"])
def make_wav() -> dict:
    data = request.json
    tempo_data = data["tempoData"]
    time_sig_data = data["timeSigData"]
    wav_filename = make_wav_file(tempo_data, time_sig_data)
    wav_url = upload_file(wav_filename)
    return (
        {"url": wav_url}
        if wav_url != "error"
        else {"error": "Something went wrong with the file"}
    )
