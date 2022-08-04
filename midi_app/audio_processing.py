import numpy as np
import soundfile as sf

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


def make_midi_file(section_data, tempo_data, instrument=None):
    clicktrack_stream = stream.Stream()
    main_rhythm_part = stream.Part()
    secondary_rhythm_part = stream.Part()

    # Extract the bpm for each note into a list
    bpms = [n["bpm"] for n in tempo_data]

    # Extracts a list of boolean values to determine whether each note
    # is accented
    accents = [n["downBeat"] for n in tempo_data]
    print("accents", accents)

    # If an instrument is specified, use the given note otherwise default to middle C
    note_pitch: str = instrument.playback_note if instrument else "C4"

    # Actually add the notes
    for section in section_data:
        # Hardcode note pitch for now
        main_rhythm_part.append(
            make_section(
                int(section["numBeats"]), int(section["numMeasures"]), note_pitch
            )
        )
        if section["secondaryNumBeats"]:
            secondary_rhythm_part.append(
                make_secondary_rhythm_section(
                    int(section["numBeats"]),
                    int(section["numMeasures"]),
                    note_pitch,
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
    clicktrack_stream.write("midi", "clicktrack.midi")

    mf = MidiFile("clicktrack.midi")

    # Add accents by directly modifying the velocity property of midi messages
    track = mf.tracks[1]
    # Filters out the MetaMessages and rests
    note_messages = [m for m in track if hasattr(m, "velocity") and m.velocity > 0]
    for idx, acc in enumerate(accents):
        if acc:
            note_messages[idx].velocity = 120
        else:
            note_messages[idx].velocity = 80

    mf.save("clicktrack.midi")

    return "clicktrack.midi"


def make_wav_file(section_data, tempo_data, instrument_val="woodblock_high") -> str:
    """Takes metadata and creates a midi file with it, which is then used along with a soundfont
    to synthesise a wav file

    instrument_val is used as a key to look up the correct instrument object in the all_instruments dict

    Returns the name of the saved wav file.
    """

    instrument = all_instruments[instrument_val]
    # First make a midi which can then be synthesised into a wav
    # This time the instrument is important as it is used in the wav file synthesis
    midi_filename = make_midi_file(section_data, tempo_data, instrument)

    fs = FluidSynth(instrument.soundfont_file)

    fs.midi_to_audio(midi_filename, "output.wav")

    return "output.wav"

def make_flac_file(section_data, tempo_data, instrument_val="woodblock_high") -> str:

    instrument = all_instruments[instrument_val]
    midi_filename = make_midi_file(section_data, tempo_data, instrument)

    fs = FluidSynth(instrument.soundfont_file)

    fs.midi_to_audio(midi_filename, "output.flac")

    return "output.flac"

def make_ogg_file(section_data, tempo_data, instrument_val="woodblock_high") -> str:

    #First synthesise to a flac file (because should be faster than wav and will be further compressed anyway)
    flac_filename = make_flac_file(section_data, tempo_data, instrument_val)

    data, samplerate = sf.read(flac_filename)
    sf.write('output.ogg', data, samplerate)

    return 'output.ogg'

