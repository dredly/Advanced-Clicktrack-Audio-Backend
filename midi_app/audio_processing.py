import subprocess

import soundfile as sf
from music21 import stream, tempo, meter, note
from mido import MidiFile

from .instruments import all_instruments
from .audio_processing_helpers import *

test_instr_list = [all_instruments["drum_metallic"], all_instruments["percussive_clap"]]


def make_midi_file(section_data, note_bpms, instruments=None) -> str | List[str]:
    """Generates a midi file from the given metadata"""

    clicktrack_stream = stream.Stream()
    main_rhythm_part = stream.Part()

    # Check if the clicktrack contains any polyrhythms
    has_polyrhythms = any(len(section["rhythms"]) > 1 for section in section_data)

    secondary_rhythm_part = (
        stream.Part()
        if has_polyrhythms or (instruments and len(instruments) > 1)
        else None
    )

    # If an instrument is specified, use the given note otherwise default to middle C
    note_pitch_main = "C4"
    note_pitch_secondary = "C4"
    if instruments:
        note_pitch_main: str = instruments[0].playback_note
        if len(instruments) > 1:
            note_pitch_secondary: str = instruments[1].playback_note
        else:
            note_pitch_secondary: str = instruments[0].playback_note

    # Add the notes
    for section in section_data:
        main_rhythm_part.append(
            make_section(
                time_sig=section["rhythms"][0]["timeSig"],
                num_measures=section["overallData"]["numMeasures"],
                note_pitch=note_pitch_main,
            )
        )
        if has_polyrhythms or (instruments and len(instruments) > 1):
            # Check if this particular section is a polyrhythm
            if len(section["rhythms"]) > 1:
                secondary_rhythm_part.append(
                    make_secondary_rhythm_section(
                        primary_time_sig=section["rhythms"][0]["timeSig"],
                        secondary_time_sig=section["rhythms"][1]["timeSig"],
                        num_measures=section["overallData"]["numMeasures"],
                        note_pitch=note_pitch_secondary,
                    )
                )
            else:
                secondary_rhythm_part.append(
                    make_silent_section(
                        time_sig=section["rhythms"][0]["timeSig"],
                        num_measures=section["overallData"]["numMeasures"],
                    )
                )

    # Add tempo markers
    for idx, bpm in enumerate(note_bpms):
        # Get the offset at which to insert the tempo marker, which can change depending on whether quarter,
        # eighth, or half notes are being used
        insert_at = main_rhythm_part.notes.offsetMap()[idx].offset
        main_rhythm_part.insert(insert_at, tempo.MetronomeMark(number=bpm))

    # Add time signature markers
    insert_at = 0
    for section in section_data:
        numerator = section["rhythms"][0]["timeSig"][0]
        denominator = section["rhythms"][0]["timeSig"][1]
        main_rhythm_part.insert(
            insert_at, meter.TimeSignature(f"{numerator}/{denominator}")
        )
        insert_at += (
            (4 / denominator) * numerator * section["overallData"]["numMeasures"]
        )

    # Calculate which notes the accents fall on from section_data
    accents: List[int] = get_accent_indices(section_data)

    if instruments and not has_polyrhythms and len(instruments) > 1:
        # Move all weak beats over to second track
        notes_and_rests_list_main = list(main_rhythm_part.notesAndRests)
        notes_and_rests_list_secondary = list(secondary_rhythm_part.notesAndRests)
        for i in range(len(notes_and_rests_list_main)):
            if i % 2 != 0:
                continue
            note_idx = i // 2
            if note_idx not in accents:
                weak_note = notes_and_rests_list_main[i]

                # First turn non accented notes into rests in the first track
                notes_and_rests_list_main[i] = note.Rest(
                    quarterLength=weak_note.quarterLength
                )

                # Then replace rest in second track with the note
                notes_and_rests_list_secondary[i] = note.Note(
                    instruments[1].playback_note, quarterLength=weak_note.quarterLength
                )

        main_rhythm_part_updated = stream.Part()
        main_rhythm_part_updated.append(notes_and_rests_list_main)
        secondary_rhythm_part_updated = stream.Part()
        secondary_rhythm_part_updated.append(notes_and_rests_list_secondary)

        # Add tempo markers
        for idx, bpm in enumerate(note_bpms):
            if idx % 2 != 0:
                continue
            insert_at = main_rhythm_part_updated.notesAndRests.offsetMap()[
                idx * 2
            ].offset
            main_rhythm_part_updated.insert(insert_at, tempo.MetronomeMark(number=bpm))

        # Add time signature markers
        insert_at = 0
        for section in section_data:
            numerator = section["rhythms"][0]["timeSig"][0]
            denominator = section["rhythms"][0]["timeSig"][1]
            main_rhythm_part_updated.insert(
                insert_at, meter.TimeSignature(f"{numerator}/{denominator}")
            )
            insert_at += (
                (4 / denominator) * numerator * section["overallData"]["numMeasures"]
            )

        clicktrack_stream.insert(0, main_rhythm_part_updated)
        clicktrack_stream.insert(0, secondary_rhythm_part_updated)
        clicktrack_stream.write("midi", "clicktrack.midi")

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
    if has_polyrhythms or (instruments and len(instruments) > 1):
        clicktrack_stream.insert(0, secondary_rhythm_part)
    clicktrack_stream.write("midi", "clicktrack.midi")

    mf = MidiFile("clicktrack.midi")

    # Add accents by directly modifying the velocity property of midi messages
    track = mf.tracks[1]
    # Filters out the MetaMessages and rests
    note_messages = [m for m in track if hasattr(m, "velocity") and m.velocity > 0]
    for idx, nm in enumerate(note_messages):
        if idx in accents:
            nm.velocity = 120
        else:
            nm.velocity = 80

    mf.save("clicktrack.midi")

    # Still need to split into 2 midi files in this case
    # Accents should hopefully be preserved
    if has_polyrhythms and instruments and len(instruments) > 1:
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


def make_file_with_fluidsynth(
    section_data: List[dict],
    note_bpms: List[int],
    file_format: str,
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
        midi_filenames = make_midi_file(section_data, note_bpms, instruments)
        for idx, mfn in enumerate(midi_filenames):
            soundfont_filename = instruments[idx].soundfont_file
            subprocess.run(
            [
                "fluidsynth",
                "-ni",
                "-g",
                "1",
                soundfont_filename,
                mfn,
                "-F",
                f"part{idx + 1}.{file_format}",
            ]
        )
        audio_data1, sample_rate = sf.read(f"part1.{file_format}")
        audio_data2, sample_rate = sf.read(f"part2.{file_format}")
        audio_data = audio_data1 + audio_data2
        sf.write(f"output.{file_format}", audio_data, sample_rate)

    else:
        midi_filename = make_midi_file(section_data, note_bpms, instruments)
        subprocess.run(
            [
                "fluidsynth",
                "-ni",
                "-g",
                "1",
                instruments[0].soundfont_file,
                midi_filename,
                "-F",
                f"output.{file_format}",
            ]
        )

    return f"output.{file_format}"


def make_ogg_file(section_data, note_bpms, instrument_vals=["woodblock_high"]) -> str:

    # First synthesise to a flac file (because should be faster than wav and will be further compressed anyway)
    flac_filename = make_file_with_fluidsynth(section_data, note_bpms, 'flac', instrument_vals)

    data, samplerate = sf.read(flac_filename)
    sf.write("output.ogg", data, samplerate)

    return "output.ogg"
