import os
import re

class CHTFile():
    _PARTICIPANTS_HEADER_PREFIX = '@participants:\t'

    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def fromFile(filePath):
        with open(filePath, 'r', encoding='utf-8') as f:
            transcriptLines = f.read().replace('\r\n','\n').split('\n')


        i = 0
        participants = {}
        while i < len(transcriptLines):
            if transcriptLines[i].lower().startswith(CHTFile._PARTICIPANTS_HEADER_PREFIX):
                lineParticipants = re.split(r',\s*', transcriptLines[i][len(CHTFile._PARTICIPANTS_HEADER_PREFIX):], 0, re.IGNORECASE)
                for p in lineParticipants:
                    part = p.split(' ',1)
                    participants[part[0].upper()] = part[-1]
            i+=1
        return participants