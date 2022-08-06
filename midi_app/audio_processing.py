import sys

import numpy as np
import soundfile as sf

from music21 import stream, tempo, meter, note
from mido import MidiFile, Message, MidiTrack
from midi2audio import FluidSynth

import cloudinary
import cloudinary.uploader
import cloudinary.api

from .instruments import Instrument, all_instruments
from .audio_processing_helpers import *

from dotenv import load_dotenv

load_dotenv()

config = cloudinary.config(secure=True)

test_instr_list = [all_instruments["drum_metallic"], all_instruments["percussive_clap"]]


def make_midi_file(
    section_data, tempo_data, instruments=None, separate=False
) -> str | List[str]:
    """Generates a midi file from the given metadata

    If separate=True, then a separate file is generated for each track. These separate files can then be used to synthesise audio
    using different soundfonts
    """

    print("Called make_mid_file()")
    clicktrack_stream = stream.Stream()
    main_rhythm_part = stream.Part()
    secondary_rhythm_part = stream.Part()

    # Extract the bpm for each note into a list
    bpms = [n["bpm"] for n in tempo_data]

    # Extracts a list of boolean values to determine whether each note
    # is accented
    accents = [n["downBeat"] for n in tempo_data]
    print("accents", accents)

    # Find out if there are any polyrhthmic sections
    has_polyrhythms = any(s["secondaryNumBeats"] for s in section_data)

    # If an instrument is specified, use the given note otherwise default to middle C
    note_pitch_main = "C4"
    note_pitch_secondary = "C4"
    if instruments:
        note_pitch_main: str = instruments[0].playback_note
        if len(instruments) > 1:
            note_pitch_secondary: str = instruments[1].playback_note
        else:
            note_pitch_secondary: str = instruments[0].playback_note

    # Actually add the notes
    for section in section_data:
        main_rhythm_part.append(
            make_section(
                int(section["numBeats"]), int(section["numMeasures"]), note_pitch_main
            )
        )
        if section["secondaryNumBeats"]:
            secondary_rhythm_part.append(
                make_secondary_rhythm_section(
                    int(section["numBeats"]),
                    int(section["numMeasures"]),
                    note_pitch_secondary,
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

    if not has_polyrhythms and len(instruments) > 1:
        # Move all weak beats over to second track
        notes_and_rests_list_main = list(main_rhythm_part.notesAndRests)
        notes_and_rests_list_secondary = list(secondary_rhythm_part.notesAndRests)
        for i in range(len(notes_and_rests_list_main)):
            note_idx = 2 * i
            try:
                if not accents[i]:
                    # First turn non accented notes into rests in the first track
                    notes_and_rests_list_main[note_idx] = note.Rest(quarterLength=0.5)
                    notes_and_rests_list_secondary[note_idx] = note.Note(
                        instruments[1].playback_note, quarterLength=0.5
                    )
            except:
                pass

        main_rhythm_part_updated = stream.Part()
        main_rhythm_part_updated.append(notes_and_rests_list_main)
        secondary_rhythm_part_updated = stream.Part()
        secondary_rhythm_part_updated.append(notes_and_rests_list_secondary)

        # Add tempo markers
        for idx, bpm in enumerate(bpms):
            main_rhythm_part_updated.insert(idx, tempo.MetronomeMark(number=bpm))

        # Add time signature markers
        insert_at = 0
        for idx, section in enumerate(section_data):
            time_sig = section["numBeats"]
            main_rhythm_part_updated.insert(
                insert_at, meter.TimeSignature(f"{time_sig}/4")
            )
            insert_at += int(time_sig) * int(section["numMeasures"])

        clicktrack_stream.insert(0, main_rhythm_part_updated)
        clicktrack_stream.insert(0, secondary_rhythm_part_updated)
        clicktrack_stream.write("midi", "clicktrack.midi")

        if separate:
            mf1 = MidiFile("clicktrack.midi")
            secondary_track = mf1.tracks[2]
            # Mute the secondary track
            note_messages = [
                m for m in secondary_track if hasattr(m, "velocity") and m.velocity > 0
            ]
            for nm in note_messages:
                nm.velocity = 0
            mf1.save("main_part.midi")

            mf2 = MidiFile("clicktrack.midi")
            main_track = mf2.tracks[1]
            # Mute the main track
            note_messages = [
                m for m in main_track if hasattr(m, "velocity") and m.velocity > 0
            ]
            for nm in note_messages:
                nm.velocity = 0
            mf2.save("secondary_part.midi")

            return ["main_part.midi", "secondary_part.midi"]

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

    if separate:
        # Both files need tracks[0] as it is the tempo track

        mf1 = MidiFile("clicktrack.midi")
        secondary_track = mf1.tracks[2]
        # Mute the secondary track
        note_messages = [
            m for m in secondary_track if hasattr(m, "velocity") and m.velocity > 0
        ]
        for nm in note_messages:
            nm.velocity = 0
        mf1.save("main_part.midi")

        mf2 = MidiFile("clicktrack.midi")
        main_track = mf2.tracks[1]
        # Mute the main track
        note_messages = [
            m for m in main_track if hasattr(m, "velocity") and m.velocity > 0
        ]
        for nm in note_messages:
            nm.velocity = 0
        mf2.save("secondary_part.midi")

        return ["main_part.midi", "secondary_part.midi"]

    return "clicktrack.midi"


def make_wav_file(
    section_data: List[dict],
    tempo_data: List[dict],
    instrument_vals: List[str] = ["woodblock_high"],
) -> str:
    """Takes metadata and creates a midi file with it, which is then used along with a soundfont
    to synthesise a wav file

    instrument_val is used as a key to look up the correct instrument object in the all_instruments dict

    Returns the name of the saved wav file.
    """

    instruments = [all_instruments[iv] for iv in instrument_vals]
    # First make a midi which can then be synthesised into a wav
    # This time the instrument is important as it is used in the wav file synthesis

    # Check if a second instrument has been specified
    if len(instruments) > 1:
        # Get a different midi file for each instrument, then combine them after
        midi_filenames = make_midi_file(section_data, tempo_data, instruments, True)
        for idx, mfn in enumerate(midi_filenames):
            fs = FluidSynth(instruments[idx].soundfont_file)
            fs.midi_to_audio(mfn, f"part{idx + 1}.wav")
        wav_data1, sample_rate = sf.read("part1.wav")
        wav_data2, sample_rate = sf.read("part2.wav")
        wav_data = wav_data1 + wav_data2
        sf.write("output.wav", wav_data, sample_rate)

    else:
        midi_filename = make_midi_file(section_data, tempo_data, instruments)

        fs = FluidSynth(instruments[0].soundfont_file)

        fs.midi_to_audio(midi_filename, "output.wav")

    return "output.wav"


def make_flac_file(
    section_data, tempo_data, instrument_vals: List[str] = ["woodblock_high"]
) -> str:

    instruments = [all_instruments[iv] for iv in instrument_vals]
    # Check if a second instrument has been specified
    if len(instruments) > 1:
        # Get a different midi file for each instrument, then combine them after
        midi_filenames = make_midi_file(section_data, tempo_data, instruments, True)
        for idx, mfn in enumerate(midi_filenames):
            fs = FluidSynth(instruments[idx].soundfont_file)
            fs.midi_to_audio(mfn, f"part{idx + 1}.flac")
        flac_data1, sample_rate = sf.read("part1.flac")
        flac_data2, sample_rate = sf.read("part2.flac")
        flac_data = flac_data1 + flac_data2
        sf.write("output.flac", flac_data, sample_rate)

    else:
        midi_filename = make_midi_file(section_data, tempo_data, instruments)

        fs = FluidSynth(instruments[0].soundfont_file)

        fs.midi_to_audio(midi_filename, "output.flac")

    return "output.flac"


def make_ogg_file(section_data, tempo_data, instrument_vals=["woodblock_high"]) -> str:

    # First synthesise to a flac file (because should be faster than wav and will be further compressed anyway)
    flac_filename = make_flac_file(section_data, tempo_data, instrument_vals)

    data, samplerate = sf.read(flac_filename)
    sf.write("output.ogg", data, samplerate)

    return "output.ogg"
