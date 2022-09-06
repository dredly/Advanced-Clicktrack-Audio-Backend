from typing import List
from music21 import note, tempo, meter
import numpy as np


def make_silent_section(time_sig: List[int], num_measures: int) -> List[note.Rest]:
    quarter_length = 0.5 * (4 / time_sig[1])
    return [
        note.Rest(quarterLength=quarter_length)
        for _ in range(2 * time_sig[0] * num_measures)
    ]


def make_section(
    time_sig: List[int], num_measures: int, note_pitch: str
) -> List[note.Note | note.Rest]:
    quarter_length = 0.5 * (4 / time_sig[1])
    note_rest_pairs = [
        [
            note.Note(note_pitch, quarterLength=quarter_length),
            note.Rest(quarterLength=quarter_length),
        ]
        for _ in range(time_sig[0] * num_measures)
    ]
    return list(np.concatenate(note_rest_pairs).flat)


def make_secondary_rhythm_section(
    primary_time_sig: List[int],
    secondary_time_sig: List[int],
    num_measures: int,
    note_pitch: str,
) -> List[note.Note | note.Rest]:
    primary_quarter_length = 0.5 * (4 / primary_time_sig[1])
    secondary_quarter_length = 0.5 * (4 / secondary_time_sig[1])
    # Might be the other way around, we'll soon find out
    quarter_length = (
        primary_time_sig[0] / secondary_time_sig[0]
    ) * secondary_quarter_length
    note_rest_pairs = [
        [
            note.Note(note_pitch, quarterLength=quarter_length),
            note.Rest(quarterLength=quarter_length),
        ]
        for _ in range(secondary_time_sig[0] * num_measures)
    ]
    return list(np.concatenate(note_rest_pairs).flat)


def get_accent_indices(section_data: List[dict]) -> List[int]:
    indices = []
    notes_so_far = 0
    for section in section_data:
        accented_beats: List[int] = section["rhythms"][0]["accentedBeats"]
        section_accents = []
        for i in range(section["overallData"]["numMeasures"]):
            measure_accents = [
                (i * section["rhythms"][0]["timeSig"][0]) + ab for ab in accented_beats
            ]
            section_accents.append(measure_accents)
        section_accents_absolute = [
            notes_so_far + sa for sa in list(np.concatenate(section_accents).flat)
        ]
        indices.append(section_accents_absolute)
        notes_in_section = (
            section["overallData"]["numMeasures"] * section["rhythms"][0]["timeSig"][0]
        )
        notes_so_far += notes_in_section
    return list(np.concatenate(indices).flat)

def get_tempo_dict(note_bpms: List[int]) -> dict:
    return dict((idx, bpm) for idx, bpm in enumerate(note_bpms) if idx == 0 or bpm != note_bpms[idx -1] )

def make_section_v2(
    num_notes_before: int,
    time_sig: List[int], 
    num_measures: int,
    accented_notes: List[int], 
    note_pitch: str, 
    tempo_dict: dict,
) -> list:
    quarter_length = 4 / time_sig[1]
    #Start with a time signature marker
    numerator = time_sig[0]
    denominator = time_sig[1]
    notes_so_far = num_notes_before + time_sig[0] * num_measures
    result = [meter.TimeSignature(f"{numerator}/{denominator}")]
    for i in range(time_sig[0] * num_measures):
        #Check if there is a tempo marker to add
        if num_notes_before + i in tempo_dict.keys():
            result.append(tempo.MetronomeMark(number=tempo_dict[num_notes_before + i]))
        is_accented = i % time_sig[0] in accented_notes
        click_note = note.Note(note_pitch, quarterLength=0.5*quarter_length)
        click_note.volume = 120 if is_accented else 80
        result.extend([
            click_note,
            note.Rest(quarterLength=0.5*quarter_length),
        ])
    return notes_so_far, result


#Just for testing the functionality
def main():
    test_bpms = [120, 120, 120, 120, 120, 150, 150, 150, 150, 140, 138, 136]
    print(get_tempo_dict(test_bpms))

if __name__=='__main__':
    main()
