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
