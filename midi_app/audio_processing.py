import subprocess
import time

import soundfile as sf
from music21 import stream

from .instruments import all_instruments
from .audio_processing_helpers import *

def make_midi_file(section_data, note_bpms, instruments=None) -> str | List[str]:
    """Generates a midi file from the given metadata"""

    # Check if the clicktrack contains any polyrhythms
    has_polyrhythms = any(len(section["rhythms"]) > 1 for section in section_data)

    # If an instrument is specified, use the given note otherwise default to middle C
    note_pitch_main = "C4"
    note_pitch_secondary = "C4"
    if instruments:
        note_pitch_main: str = instruments[0].playback_note
        if len(instruments) > 1:
            note_pitch_secondary: str = instruments[1].playback_note
        else:
            note_pitch_secondary: str = instruments[0].playback_note

    

    # From note bpms, generate a tempo_dict of format {note_idx: bpm}, so that we only put tempo markers where
    # the tempo actually changes
    tempo_dict: dict = get_tempo_dict(note_bpms)
    notes_so_far = 0

    # The simplest case, where we dont need to worry about a second part
    if (not instruments or len(instruments) == 1) and not has_polyrhythms:
        clicktrack_stream = stream.Stream()
        for section in section_data:
            notes_so_far, section_notes = make_section(
                notes_so_far, 
                section["rhythms"][0]["timeSig"], 
                section["overallData"]["numMeasures"], 
                section["rhythms"][0]["accentedBeats"],
                note_pitch_main, 
                tempo_dict
            )
            clicktrack_stream.append(section_notes)
        
        clicktrack_stream.write("midi", "clicktrack.midi")
        return "clicktrack.midi"

    # In this case a separate stream made for each instrument
    elif instruments and len(instruments) > 1 and not has_polyrhythms:
        main_stream = stream.Stream()
        secondary_stream = stream.Stream()
        for section in section_data:
            notes_so_far, section_notes = make_section_separated(
                notes_so_far, 
                section["rhythms"][0]["timeSig"], 
                section["overallData"]["numMeasures"], 
                section["rhythms"][0]["accentedBeats"],
                note_pitch_main,
                note_pitch_secondary, 
                tempo_dict
            )
            main_stream.append(section_notes["main"])
            secondary_stream.append(section_notes["secondary"])

        main_stream.write("midi", "main.midi")
        secondary_stream.write("midi", "secondary.midi")
        return ["main.midi", "secondary.midi"]
    
    # In this case a separate part is made for each instrument but then they are combined
    elif (not instruments or len(instruments) == 1) and has_polyrhythms:
        clicktrack_stream = stream.Stream()
        main_rhythm_part = stream.Part()
        secondary_rhythm_part = stream.Part()

        for section in section_data:
            time_sigs = [r["timeSig"] for r in section["rhythms"]]
            notes_so_far, section_notes = make_section_polyrhythm_one_instrument(
                notes_so_far,
                time_sigs,
                section["overallData"]["numMeasures"],
                section["rhythms"][0]["accentedBeats"],
                note_pitch_main,
                tempo_dict
            )
            main_rhythm_part.append(section_notes["main"])
            secondary_rhythm_part.append(section_notes["secondary"])

        #Combine the two parts
        clicktrack_stream.insert(0, main_rhythm_part)
        clicktrack_stream.insert(0, secondary_rhythm_part)
        clicktrack_stream.write("midi", "clicktrack.midi")
        return "clicktrack.midi"

    # In this case a separate stream is made for each instrument
    elif instruments and len(instruments) > 1 and has_polyrhythms:
        main_stream = stream.Stream()
        secondary_stream = stream.Stream()
        for section in section_data:
            time_sigs = [r["timeSig"] for r in section["rhythms"]]
            notes_so_far, section_notes = make_section_polyrhythm_two_instruments(
                notes_so_far,
                time_sigs,
                section["overallData"]["numMeasures"],
                section["rhythms"][0]["accentedBeats"],
                note_pitch_main,
                note_pitch_secondary,
                tempo_dict
            )
            main_stream.append(section_notes["main"])
            secondary_stream.append(section_notes["secondary"])

        main_stream.write("midi", "main.midi")
        secondary_stream.write("midi", "secondary.midi")
        return ["main.midi", "secondary.midi"]

    else:
        return "error"
    
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

    start_time = time.time()
    midi_time = 0
    audio_time = 0

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

        # May be a slightly different amount of silence at the end of each track, so need to trim down
        # the longer one so that the np arrays can be added
        shorter_length = min(len(audio_data1), len(audio_data2))
        audio_data = audio_data1[:shorter_length] + audio_data2[:shorter_length]

        sf.write(f"output.{file_format}", audio_data, sample_rate)

    else:
        midi_filename = make_midi_file(section_data, note_bpms, instruments)
        midi_time = time.time()
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
        audio_time = time.time()

    midi_time_taken = midi_time - start_time
    audio_time_taken = audio_time - midi_time

    return f"output.{file_format}", midi_time_taken, audio_time_taken