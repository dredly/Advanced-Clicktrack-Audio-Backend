from typing import List
from music21 import note, tempo, meter
import numpy as np

def get_tempo_dict(note_bpms: List[int]) -> dict:
    return dict((idx, bpm) for idx, bpm in enumerate(note_bpms) if idx == 0 or bpm != note_bpms[idx -1] )

def make_section(
    num_notes_before: int,
    time_sig: List[int], 
    num_measures: int,
    accented_notes: List[int], 
    note_pitch: str, 
    tempo_dict: dict,
):
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

def make_section_separated(
    num_notes_before: int,
    time_sig: List[int], 
    num_measures: int,
    accented_notes: List[int], 
    note_pitch_primary: str, 
    note_pitch_secondary: str,
    tempo_dict: dict,
):
    quarter_length = 4 / time_sig[1]
    numerator = time_sig[0]
    denominator = time_sig[1]
    notes_so_far = num_notes_before + time_sig[0] * num_measures
    main_rhythm = [meter.TimeSignature(f"{numerator}/{denominator}")]
    secondary_rhythm = [meter.TimeSignature(f"{numerator}/{denominator}")]
    for i in range(time_sig[0] * num_measures):
        #Check if there is a tempo marker to add
        if num_notes_before + i in tempo_dict.keys():
            main_rhythm.append(tempo.MetronomeMark(number=tempo_dict[num_notes_before + i]))
            secondary_rhythm.append(tempo.MetronomeMark(number=tempo_dict[num_notes_before + i]))
        is_accented = i % time_sig[0] in accented_notes
        if is_accented:
            click_note = note.Note(note_pitch_primary, quarterLength=0.5*quarter_length)
            main_rhythm.extend([
                click_note,
                note.Rest(quarterLength=0.5*quarter_length),
            ])
            secondary_rhythm.extend([
                #May need to change this to 2 rests of 0.5 * quarter_length instead
                note.Rest(quarterLength=quarter_length)
            ])
        else:
            click_note = note.Note(note_pitch_secondary, quarterLength=0.5*quarter_length)
            main_rhythm.extend([
                #May need to change this to 2 rests of 0.5 * quarter_length instead
                note.Rest(quarterLength=quarter_length)
            ])
            secondary_rhythm.extend([
                click_note,
                note.Rest(quarterLength=0.5*quarter_length),
            ])
    return notes_so_far, {"main": main_rhythm, "secondary": secondary_rhythm}

def make_section_polyrhythm_one_instrument(
    num_notes_before: int,
    time_sigs: List[List[int]],
    num_measures: int,
    accented_notes: List[int], 
    note_pitch: str, 
    tempo_dict: dict,
):
    numerator = time_sigs[0][0]
    denominator = time_sigs[0][1]
    notes_so_far = num_notes_before + time_sigs[0][0] * num_measures
    main_rhythm = [meter.TimeSignature(f"{numerator}/{denominator}")]
    secondary_rhythm = []

    #Check if this particular section is a polyrhythm
    if len(time_sigs) > 1:
        primary_quarter_length = 4 / time_sigs[0][1]
        secondary_quarter_length = (time_sigs[0][0] / time_sigs[1][0]) * (4 / time_sigs[1][1])
        for i in range(time_sigs[0][0] * num_measures):
            #Check if there is a tempo marker to add
            if num_notes_before + i in tempo_dict.keys():
                main_rhythm.append(tempo.MetronomeMark(number=tempo_dict[num_notes_before + i]))
            is_accented = i % time_sigs[0][0] in accented_notes
            click_note = note.Note(note_pitch, quarterLength=0.5*primary_quarter_length)
            click_note.volume = 120 if is_accented else 80
            main_rhythm.extend([
                click_note,
                note.Rest(quarterLength=0.5*primary_quarter_length)
            ])
        for j in range(time_sigs[1][0] * num_measures):
            click_note = note.Note(note_pitch, quarterLength=0.5*secondary_quarter_length)
            click_note.volume = 80
            secondary_rhythm.extend([
                click_note,
                note.Rest(quarterLength=0.5*secondary_quarter_length)
            ])
    else:
        quarter_length = 4 / time_sigs[0][1]
        for i in range(time_sigs[0][0] * num_measures):
            #Check if there is a tempo marker to add
            if num_notes_before + i in tempo_dict.keys():
                main_rhythm.append(tempo.MetronomeMark(number=tempo_dict[num_notes_before + i]))
            is_accented = i % time_sigs[0][0] in accented_notes
            click_note = note.Note(note_pitch, quarterLength=0.5*quarter_length)
            click_note.volume = 120 if is_accented else 80
            main_rhythm.extend([
                click_note,
                note.Rest(quarterLength=0.5*quarter_length),
            ])
            secondary_rhythm.extend([note.Rest(quarterLength=quarter_length)])
            
    return notes_so_far, {"main": main_rhythm, "secondary": secondary_rhythm}

def make_section_polyrhythm_two_instruments(
    num_notes_before: int,
    time_sigs: List[List[int]],
    num_measures: int,
    accented_notes: List[int], 
    note_pitch_primary: str, 
    note_pitch_secondary: str,
    tempo_dict: dict,
):
    numerator = time_sigs[0][0]
    denominator = time_sigs[0][1]
    notes_so_far = num_notes_before + time_sigs[0][0] * num_measures
    main_rhythm = [meter.TimeSignature(f"{numerator}/{denominator}")]
    secondary_rhythm = [meter.TimeSignature(f"{numerator}/{denominator}")]    

    #Check if this particular section is a polyrhythm
    if len(time_sigs) > 1:
        primary_quarter_length = 4 / time_sigs[0][1]
        secondary_quarter_length = (time_sigs[0][0] / time_sigs[1][0]) * (4 / time_sigs[1][1])
        for i in range(time_sigs[0][0] * num_measures):
            #Check if there is a tempo marker to add
            if num_notes_before + i in tempo_dict.keys():
                main_rhythm.append(tempo.MetronomeMark(number=tempo_dict[num_notes_before + i]))
                secondary_rhythm.append(tempo.MetronomeMark(number=tempo_dict[num_notes_before + i]))
            main_rhythm.extend([
                note.Note(note_pitch_primary, quarterLength=0.5*primary_quarter_length),
                note.Rest(quarterLength=0.5*primary_quarter_length)
            ])
        for j in range(time_sigs[1][0] * num_measures):
            secondary_rhythm.extend([
                note.Note(note_pitch_secondary, quarterLength=0.5*secondary_quarter_length),
                note.Rest(quarterLength=0.5*secondary_quarter_length)
            ])

    else:
        quarter_length = 4 / time_sigs[0][1]
        for i in range(time_sigs[0][0] * num_measures):
            #Check if there is a tempo marker to add
            if num_notes_before + i in tempo_dict.keys():
                main_rhythm.append(tempo.MetronomeMark(number=tempo_dict[num_notes_before + i]))
                secondary_rhythm.append(tempo.MetronomeMark(number=tempo_dict[num_notes_before + i]))
            is_accented = i % time_sigs[0][0] in accented_notes
            click_note = note.Note(note_pitch_primary, quarterLength=0.5*quarter_length)
            click_note.volume = 120 if is_accented else 80
            main_rhythm.extend([
                click_note,
                note.Rest(quarterLength=0.5*quarter_length),
            ])
            secondary_rhythm.extend([note.Rest(quarterLength=quarter_length)])

    return notes_so_far, {"main": main_rhythm, "secondary": secondary_rhythm}
