from typing import List
from music21 import note
import numpy as np


def make_silent_section(num_quarters: int, num_measures: int) -> List[note.Rest]:
    return [
        note.Rest(quarterLength=0.5) for _ in range(2 * num_quarters * num_measures)
    ]


def make_section(
    num_quarters: int, num_measures: int, note_pitch: str
) -> List[note.Note | note.Rest]:
    note_rest_pairs = [
        [note.Note(note_pitch, quarterLength=0.5), note.Rest(quarterLength=0.5)]
        for _ in range(num_quarters * num_measures)
    ]
    return list(np.concatenate(note_rest_pairs).flat)


def make_secondary_rhythm_section(
    num_quarters: int, num_measures: int, note_pitch: str, secondary_num_beats: int
) -> List[note.Note | note.Rest]:
    quarter_length = 0.5 * (num_quarters / secondary_num_beats)
    note_rest_pairs = [
        [
            note.Note(note_pitch, quarterLength=quarter_length),
            note.Rest(quarterLength=quarter_length),
        ]
        for _ in range(secondary_num_beats * num_measures)
    ]
    return list(np.concatenate(note_rest_pairs).flat)
