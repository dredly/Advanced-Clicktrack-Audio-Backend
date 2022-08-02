class Instrument:
    def __init__(self, name: str, playback_note: str, soundfont_file: str):
        self.name = name
        self.playback_note = playback_note
        self.soundfont_file = soundfont_file


drum1: Instrument = Instrument("Drum Sample 1", "F3", "African_Percussion.sf2")
