from typing import List, Any
import pylangacq
from pyannote.core import Segment

class ReaderWithTimeline(pylangacq.Reader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._timeline: List[Segment] = None
    
    def iter_timeline(self):
        if not self._timeline:
            self._generate_timeline()
        for segment in self._timeline:
            yield segment
    
    def _generate_timeline(self):
        if self._timeline:
            raise RuntimeError('Timeline has already been generated!')
        temp = []
        for utterance in self.utterances():
            # time_marks are in ms, need to convert to seconds
            temp.append(DataSegment(data=utterance, start=utterance.time_marks[0]/1000, end=utterance.time_marks[1]/1000))
        self._timeline = temp

class DataSegment(Segment):
    def __init__(self, data=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data: Any = data
    
    def get_data(self):
        return self.data
    def set_data(self, value):
        prev, self.data = self.data, value
        return prev