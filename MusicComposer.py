"""A program for composing music with synthesized sounds."""
from enum import Enum
import math
import time
import pyaudio

PI = math.pi
TWO_PI = 2*PI


class Tone(Enum):
    """Represents the tone of a note."""

    C = 0
    D = 2
    E = 4
    F = 5
    G = 7
    A = 9
    B = 11


class Sign(Enum):
    """Represents the sign of a note."""

    DoubleFlat = -2
    Flat = -1
    HalfFlat = -0.5
    HalfSharp = 0.5
    Sharp = 1
    DoubleSharp = 2


class Pitch:
    """Represents the pitch of a note."""

    def __init__(self, tone, octave, sign=0):
        """Initializer."""
        self.tone = tone
        self.octave = octave
        self.sign = sign


class Dynamic(Enum):
    """Represents the dynamics of a note."""

    ppp = 16
    pp = 33
    p = 49
    mp = 64
    mf = 80
    f = 96
    ff = 112
    fff = 126


class Note:
    """Represents a musical note."""

    def __init__(self, duration, tone=None, octave=0, sign=0,
                 dynamic=Dynamic.mf):
        """Initializer."""
        self.duration = float(duration)
        self.tone = tone
        self.octave = int(octave)
        self.sign = sign
        self.dynamic = dynamic

    def frequency(self):
        """Return the frequency if the note has a pitch, otherwise None."""
        if self.tone is not None:
            octaves = (self.octave*12+self.tone+self.sign)/12.0
            return 440*math.pow(2, octaves)


class Bar:
    """Represents a bar in a composition."""

    # TODO: Implement dots for durations.
    def __init__(self, notes, numberOfBeats, divisor):
        """Initializer."""
        self.numberOfBeats = numberOfBeats
        self.divisor = divisor

        self.notes = []
        barTotalDuration = float(numberOfBeats)/divisor
        notesTotalDuration = 0
        for note in notes:
            if notesTotalDuration+note.duration > barTotalDuration:
                clippedNote = Note(barTotalDuration-notesTotalDuration,
                                   note.pitch, note.dynamic)
                if clippedNote.duration > 0:
                    self.notes.append(clippedNote)
                    notesTotalDuration += clippedNote.duration
                break
            self.notes.append(note)
            notesTotalDuration += note.duration
        if notesTotalDuration < barTotalDuration:
            self.notes.append(Note(barTotalDuration-notesTotalDuration))


class Composition:
    """Represents a musical composition."""

    def __init__(self, bars, bpm):
        """Initializer."""
        self.bars = bars
        self.bpm = float(bpm)

    def convertToWaveData(self, bitRate=44100):
        """Convert composition to waveform data."""
        # TODO: Implement dots for durations.
        bps = self.bpm/60
        waveData = []
        for bar in self.bars:
            for note in bar.notes:
                chunk = ""
                duration = bar.divisor*note.duration/bps
                frequency = note.frequency()
                amplitude = note.dynamic
                numberOfFrames = int(bitRate*duration)

                if frequency is None:
                    for x in xrange(numberOfFrames):
                        chunk += chr(128)
                else:
                    fadingFrames = int(0.01*bitRate)
                    if fadingFrames > numberOfFrames:
                        fadingFrames = numberOfFrames
                    fadeInFrames = fadingFrames/2
                    fadeOutFrames = (fadingFrames+1)/2

                    for x in xrange(numberOfFrames):
                        x_f = float(x)
                        frame = math.sin(x_f/bitRate*frequency*TWO_PI)
                        if x < fadeInFrames:
                            frame *= x_f/fadeInFrames*amplitude
                        elif x >= numberOfFrames-fadeOutFrames:
                            x_f -= numberOfFrames-fadeOutFrames
                            frame *= (1-x_f/fadeOutFrames)*amplitude
                        else:
                            frame *= amplitude
                        frame += 128
                        chunk += chr(int(frame))
                waveData.append(chunk)
        return waveData


def main():
    """Main program."""
    bitRate = 44100

    d = 1.0/16
    r =   Note(duration=d)
    a =   Note(duration=d, tone=Tone.A, octave=-1,         dynamic=Dynamic.f  )
    a_s = Note(duration=d, tone=Tone.A, octave=-1, sign=1, dynamic=Dynamic.f  )
    b =   Note(duration=d, tone=Tone.B, octave=-1,         dynamic=Dynamic.f  )
    c =   Note(duration=d, tone=Tone.C,                    dynamic=Dynamic.f  )
    d_s = Note(duration=d, tone=Tone.D,            sign=1, dynamic=Dynamic.p  )
    g =   Note(duration=d, tone=Tone.G,                    dynamic=Dynamic.p  )
    bar1 = Bar([c, d_s, g, d_s, c, d_s, g, d_s,
                c, d_s, g, d_s, c, d_s, g, d_s], 4, 4)
    bar2 = Bar([b, d_s, g, d_s, b, d_s, g, d_s,
                b, d_s, g, d_s, b, d_s, g, d_s], 4, 4)
    bar3 = Bar([a_s, d_s, g, d_s, a_s, d_s, g, d_s,
                a_s, d_s, g, d_s, a_s, d_s, g, d_s],
               4, 4)
    bar4 = Bar([a, d_s, g, d_s, a, d_s, g, d_s,
                a, d_s, g, d_s, c, b, a, b], 4, 4)
    composition = Composition([bar1, bar2, bar3, bar4],
                              120)

    p = pyaudio.PyAudio()
    waveData = composition.convertToWaveData()
    stream = p.open(format=p.get_format_from_width(1), channels=1,
                    rate=bitRate, output=True)
    stream.start_stream()
    while True:
        for chunk in waveData:
            stream.write(chunk)
    stream.stop_stream()
    stream.close()
    p.terminate()


if __name__ == "__main__":
    main()
