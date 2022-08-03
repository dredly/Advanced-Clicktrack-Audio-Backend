class Instrument:
    def __init__(self, name: str, playback_note: str, soundfont_file: str):
        self.name = name
        self.playback_note = playback_note
        self.soundfont_file = soundfont_file


all_instruments: dict = {
    "drum1": Instrument("Generic Drum 1", "F3", "African_Percussion.sf2"),
    "drum2": Instrument("Generic Drum 2", "A2", "African_Percussion.sf2"),
    "drum_metallic": Instrument("Metallic Drum", "C5", "African_Percussion.sf2"),
    "percussive_clap": Instrument("Percussive Clap", "E5", "African_Percussion.sf2"),
    "percussive_stick": Instrument("Percussive Stick", "C7", "African_Percussion.sf2"),
    "finger_snap": Instrument("Finger snap", "C4", "Finger_Snaps.sf2"),
    "woodblock_high": Instrument("High pitched Woodblock", "E7", "Woodblocks.sf2"),
    "woodblock_lower": Instrument("Lower pitched Woodblock", "B6", "Woodblocks.sf2"),
}
