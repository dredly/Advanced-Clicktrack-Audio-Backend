from typing import List
from music21 import note
import numpy as np


def make_silent_section(time_sig: List[int], num_measures: int) -> List[note.Rest]:
    quarter_length = 0.5 * (4 / time_sig[1])
    return [
        note.Rest(quarterLength=quarter_length) for _ in range(2 * time_sig[0] * num_measures)
    ]

def make_section(time_sig: List[int], num_measures: int, note_pitch: str) -> List[note.Note | note.Rest]:
    quarter_length = 0.5 * (4 / time_sig[1])
    note_rest_pairs = [
        [note.Note(note_pitch, quarterLength=quarter_length), note.Rest(quarterLength=quarter_length)]
        for _ in range(time_sig[0] * num_measures)
    ]
    return list(np.concatenate(note_rest_pairs).flat)

def make_secondary_rhythm_section(
    primary_time_sig: List[int], secondary_time_sig: List[int], num_measures: int, note_pitch: str,
) -> List[note.Note | note.Rest]:
    primary_quarter_length = 0.5 * (4 / primary_time_sig[1])
    secondary_quarter_length = 0.5 * (4 / secondary_time_sig[1])
    # Might be the other way around, we'll soon find out
    quarter_length = (primary_time_sig[0] / secondary_time_sig[0]) * secondary_quarter_length
    note_rest_pairs = [
        [
            note.Note(note_pitch, quarterLength=quarter_length),
            note.Rest(quarterLength=quarter_length),
        ]
        for _ in range(secondary_time_sig[0] * num_measures)
    ]
    return list(np.concatenate(note_rest_pairs).flat)

def get_accent_indices(section_data: List[dict]) -> List[int]:
    indices =[]
    notes_so_far = 0
    for section in section_data:
        accented_beats: List[int] = section["rhythms"][0]["accentedBeats"]
        section_accents = []
        for i in range(section["overallData"]["numMeasures"]):
            measure_accents = [(i * section["rhythms"][0]["timeSig"][0]) + ab for ab in accented_beats]
            section_accents.append(measure_accents)
        section_accents_absolute = [notes_so_far + sa for sa in list(np.concatenate(section_accents).flat)]
        indices.append(section_accents_absolute)
        notes_in_section = section["overallData"]["numMeasures"] * section["rhythms"][0]["timeSig"][0]
        notes_so_far += notes_in_section
    return list(np.concatenate(indices).flat)