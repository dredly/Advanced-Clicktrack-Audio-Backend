import numpy as np

from music21 import stream, note, tempo, meter
from mido import MidiFile
from midi2audio import FluidSynth

import cloudinary
import cloudinary.uploader
import cloudinary.api

from .instruments import all_instruments
from .audio_processing_helpers import *

from dotenv import load_dotenv

load_dotenv()

config = cloudinary.config(secure=True)

# Quickly test midi to wav conversion through external api
def make_midi_file(tempo_data: dict, time_sig_data: dict, instrument=None) -> str:
    """Converts metadata into a music21 stream object which is then written to a midi file

    Returns the name of the saved midi file

    For some reason, any accents or volume adjustments made with music21 did not show up in the exported midi
    file, so I had to then open it with the mido library to accent the downbeats
    """

    # clicktrack_part = stream.Part()
    # clicktrack_part.insert(0, instrument.BongoDrums())

    clicktrack_stream = stream.Stream()

    # Extract the bpm for each note into a list
    bpms = [n["bpm"] for n in tempo_data]

    # Extracts a list of boolean values to determine whether each note
    # is accented
    accents = [n["downBeat"] for n in tempo_data]

    # If an instrument is specified, use the given note otherwise default to middle C
    note_pitch: str = instrument.playback_note if instrument else "C3"

    # Construct the clicktrack as a music21 stream object
    note_rest_pairs = [
        [note.Note(note_pitch, quarterLength=0.5), note.Rest(quarterLength=0.5)]
        for _ in range(len(tempo_data))
    ]
    notes_and_rests = list(np.concatenate(note_rest_pairs).flat)
    clicktrack_stream.append(notes_and_rests)

    # Add tempo markers
    for idx, bpm in enumerate(bpms):
        clicktrack_stream.insert(idx, tempo.MetronomeMark(number=bpm))

    # Add time signature markers
    insert_at = 0
    for idx, section in enumerate(time_sig_data):
        time_sig = section["numBeats"]
        clicktrack_stream.insert(insert_at, meter.TimeSignature(f"{time_sig}/4"))
        insert_at += time_sig * int(section["numMeasures"])

    clicktrack_stream.write("midi", "clicktrack.midi")

    mf = MidiFile("clicktrack.midi")

    # Add accents by directly modifying the velocity property of midi messages
    track = mf.tracks[1]
    # Filters out the MetaMessages and rests
    note_messages = [m for m in track if hasattr(m, "velocity") and m.velocity > 0]
    for idx, acc in enumerate(accents):
        if acc:
            note_messages[idx].velocity = 120

    mf.save("clicktrack.midi")

    return "clicktrack.midi"


def make_midi_file_with_polyrhythms(section_data, tempo_data):
    clicktrack_stream = stream.Stream()
    main_rhythm_part = stream.Part()
    secondary_rhythm_part = stream.Part()

    # Extract the bpm for each note into a list
    # print("tempo_data", tempo_data[0]['bpm'])
    # for n in tempo_data:
    #     print(n)
    bpms = [n["bpm"] for n in tempo_data]

    #Actually add the notes
    for section in section_data:
        # Hardcode note pitch for now
        main_rhythm_part.append(
            make_section(int(section["numBeats"]), int(section["numMeasures"]), "C4")
        )
        if section["secondaryNumBeats"]:
            secondary_rhythm_part.append(
                make_secondary_rhythm_section(
                    int(section["numBeats"]),
                    int(section["numMeasures"]),
                    "C4",
                    int(section["secondaryNumBeats"]),
                )
            )
        else:
            secondary_rhythm_part.append(
                make_silent_section(
                    int(section["numBeats"]), int(section["numMeasures"])
                )
            )

    # Add tempo markers
    for idx, bpm in enumerate(bpms):
        main_rhythm_part.insert(idx, tempo.MetronomeMark(number=bpm))

    # Add time signature markers
    insert_at = 0
    for idx, section in enumerate(section_data):
        time_sig = section["numBeats"]
        main_rhythm_part.insert(insert_at, meter.TimeSignature(f"{time_sig}/4"))
        insert_at += int(time_sig) * int(section["numMeasures"])

    clicktrack_stream.insert(0, main_rhythm_part)
    clicktrack_stream.insert(0, secondary_rhythm_part)
    clicktrack_stream.write("midi", "polyrhythm.midi")


def make_wav_file(
    tempo_data: dict,
    time_sig_data: dict,
    instrument_val="woodblock_high",  # Used to look up the correct instrument object in the all_instruments dict
) -> str:
    """Takes metadata and creates a midi file with it, which is then used along with a soundfont
    to synthesise a wav file

    Returns the name of the saved wav file.
    """

    instrument = all_instruments[instrument_val]
    # First make a midi which can then be synthesised into a wav
    # This time the instrument is important as it is used in the wav file synthesis
    midi_filename = make_midi_file(tempo_data, time_sig_data, instrument)

    fs = FluidSynth(instrument.soundfont_file)

    fs.midi_to_audio("clicktrack.midi", "output.wav")

    return "output.wav"
