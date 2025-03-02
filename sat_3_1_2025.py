from pyannote.audio import Pipeline
from pyannote.core import Segment
import re
import os
import pylangacq
from timelinereader import ReaderWithTimeline, DataSegment
from itertools import takewhile

from huggingface_hub import notebook_login
#notebook_login()



def getHFToken(forceInput=False):
    hfTokenFilePath = './hftoken'
    if forceInput or not os.path.exists(hfTokenFilePath):
        token = input("Hugging face token missing or invalid.\nEnter hf token")
        with open(hfTokenFilePath, 'w') as f:
            f.write(token.strip())
    else:
        with open(hfTokenFilePath,'r') as f:
            token = f.read()
    return token


# Set your Pyannote API token
PYANNOTE_TOKEN = getHFToken()

def perform_diarization(audio_path):
    """Perform speaker diarization on the audio file."""
    diarization = pipeline(audio_path)
    segments = []

    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            "start": turn.start,
            "end": turn.end,
            "speaker": speaker
        })

    return segments

def get_segment(utterance):
    return Segment(start=utterance.time_marks[0]/1000, end=utterance.time_marks[1]/1000)

def align_diarization(audio_path, transcript_path, yield_status=False):
    diarization_model_name = 'pyannote/speaker-diarization-3.1'

    if yield_status:
        print('yield', 'Attempt', f"Attempting to read transcript: {transcript_path}")
    
    # use our custom reader with timeline to make aligning them easier
    transcript = pylangacq.read_chat(transcript_path, cls=ReaderWithTimeline)
    
    if yield_status:
        print('yield', 'Success', f"Successfully read transcript: {transcript_path}")
        print('yield', 'Attempt', f"Attempting load model: {diarization_model_name}")
    pipeline = Pipeline.from_pretrained(diarization_model_name, use_auth_token=PYANNOTE_TOKEN)
    if yield_status:
        print('yield', 'Success', f"Successfully loaded model: {diarization_model_name}")
        print('yield', 'Attempt', f"Attempting diarization of: {audio_path}")
    diarization = pipeline(audio_path)
    if yield_status:
        print('yield', 'Success', f"Successful diarization of: {audio_path}")
        print('yield', 'Attempt', f"Attempting to align utterances to speakers")
    #dia_iter = diarization.itertracks(yield_label=True)
    #cha_iter = transcript.iter_timeline()
    # o = []
    # for a in diarization.itertracks(yield_label=True):
    #     x = a[0]
    #     n = a[2]
    #     z = []
    #     for b in transcript.utterances():
    #         y = get_segment(b)
    #         # n = b.tiers[b.participant]
    #         if x.overlaps(y.start) or x.overlaps(y.end):
    #             z.append(y)
    #     if z:
    #         o.append((n,x,z))
    # print(o)

    # p = []
    # for a in transcript.utterances():
    #     x = get_segment(a)
    #     n = a.tiers[a.participant]
    #     z = []
    #     for b in diarization.itertracks(yield_label=True):
    #         y = b[0]
    #         # n = b[2]
    #         if x.overlaps(y.start) or x.overlaps(y.end):
    #             z.append(y)
    #     if z:
    #         p.append((n,x,z))
    # print(p)

    # @todo improve runtime performance of this alignment function
    # for now it is just O(len(dia_iter)*len(cha_iter))
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        overlapping = []
        #for utterance in transcript.iter_timeline():
        for utterance in transcript.utterances():
            time_segment = get_segment(utterance)
            if turn.overlaps(time_segment.start) or turn.overlaps(time_segment.end):
                overlapping.append(utterance)
            elif (time_segment.overlaps(turn.start) or time_segment.overlaps(turn.end)):
               overlapping.append(utterance)
        if len(overlapping) == 0:
            print("???")
        elif len(overlapping) == 1:
            # @todo set new participant
            #print(f"set participant to {speaker}")
            utterance = overlapping[0]
            current_participant = utterance.participant
            if speaker != current_participant:
                utterance.tiers[speaker] = utterance.tiers[current_participant]
                del utterance.tiers[current_participant]
                utterance.participant = speaker
        else:
            print("Are these from the same person?\n\t", "\n\t>".join([u.tiers[u.participant] for u in overlapping]))
            

        # elif len(overlapping) == 1:
        #     # @todo set new participant
        #     print(f"set participant to {speaker}")
        #     utterance = overlapping[0]
        #     current_participant = utterance.participant
        #     if speaker != current_participant:
        #         utterance.tiers[speaker] = utterance.tiers[current_participant]
        #         del utterance.tiers[current_participant]
        #         utterance.participant = speaker
        # else:
        #     print("conflicting number of participants in segment, defaulting to unknown for now")
    
    for utterance in transcript.utterances():
        time_segment = get_segment(utterance)
        whospeaksduringthisutterance = set()
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            if time_segment.overlaps(turn.start) or time_segment.overlaps(turn.end):
                whospeaksduringthisutterance.add(speaker)
        if len(whospeaksduringthisutterance) == 0:
            print("???")
        elif len(whospeaksduringthisutterance) == 1:
            # @todo set new participant
            speaker = whospeaksduringthisutterance.pop()
            # print(f"set participant to {speaker}")
            current_participant = utterance.participant
            if speaker != current_participant:
                utterance.tiers[speaker] = utterance.tiers[current_participant]
                del utterance.tiers[current_participant]
                utterance.participant = speaker
        else:
            print(f"Who said this?\n{utterance.tiers[utterance.participant]}\n\t> ", "\n\t> ".join(whospeaksduringthisutterance))
    
    old_participant_list = list(transcript._files[0].header['Participants'])
    for p in transcript.participants():
        # inject the new speakers into the participants list
        if p in transcript._files[0].header['Participants']:
            continue
        else:
            transcript._files[0].header['Participants'][p] = {'name': 'SPEAKER', 'language': 'eng', 'corpus': 'corpus_name', 'age': '', 'sex': '', 'group': '', 'ses': '', 'custom': 'FIXME', 'role': 'Participant', 'education': ''}
    
    toprint = [x.strip() for x in transcript.to_strs(False)]
    if toprint:
        # for some reason @Begin & @End dont go into the printed file? so we fix that here
        toprint = "\n".join(toprint).replace('\r\n','\n').split("\n")
        toprint.insert(toprint.index('@UTF8'),'@Begin')
        toprint.append('@End')
        toprint = '\n'.join(toprint)
        with open(f"{transcript_path.rsplit('.',1)[0]}_fixed.cha",'w',encoding='utf-8') as f:
            f.write(toprint)
        if yield_status:
            print('yield', 'Success', f"Aligned utterances to speakers")
        else:
            print('yield', 'Failure', f'Failed to write to file?!')
    return transcript

if __name__ == "__main__":
    testaudiofile = '.tmp_align/badfriends.mp3'
    transcriptPath='.tmp_align/badfriends.cha'
    fixed = align_diarization(testaudiofile, transcriptPath)
    print(1)