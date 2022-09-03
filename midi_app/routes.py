from flask import request
from midi_app import app
from .audio_processing import (
    make_midi_file,
    make_file_with_fluidsynth,
    make_ogg_file,
)
from .file_management import upload_file

# Health check to quickly verify if the API is running or not
@app.route("/", methods=["GET", "POST"])
def home():
    return {"marco": "polo"}


@app.route("/api/make_midi", methods=["POST"])
def make_midi() -> dict:
    data = request.json
    section_data = data["sectionData"]
    note_bpms = data["noteBpms"]
    midi_filename = make_midi_file(section_data, note_bpms)
    midi_url = upload_file(midi_filename)
    return (
        {"url": midi_url}
        if midi_url != "error"
        else {"error": "Something went wrong with the file"}
    )


@app.route("/api/make_wav", methods=["POST"])
def make_wav() -> dict:
    data = request.json
    section_data = data["sectionData"]
    note_bpms = data["noteBpms"]
    instrument_vals = data["instruments"]
    wav_filename = make_file_with_fluidsynth(section_data, note_bpms, 'wav', instrument_vals)
    wav_url = upload_file(wav_filename)
    return (
        {"url": wav_url}
        if wav_url != "error"
        else {"error": "Something went wrong with the file"}
    )


@app.route("/api/make_flac", methods=["POST"])
def make_flac() -> dict:
    data = request.json
    section_data = data["sectionData"]
    note_bpms = data["noteBpms"]
    instrument_vals = data["instruments"]
    flac_filename = make_file_with_fluidsynth(section_data, note_bpms, 'flac', instrument_vals)
    flac_url = upload_file(flac_filename)
    return (
        {"url": flac_url}
        if flac_url != "error"
        else {"error": "Something went wrong with the file"}
    )


@app.route("/api/make_ogg", methods=["POST"])
def make_ogg() -> dict:
    data = request.json
    section_data = data["sectionData"]
    note_bpms = data["noteBpms"]
    instrument_vals = data["instruments"]
    ogg_filename = make_ogg_file(section_data, note_bpms, instrument_vals)
    ogg_url = upload_file(ogg_filename)
    return (
        {"url": ogg_url}
        if ogg_url != "error"
        else {"error": "Something went wrong with the file"}
    )
