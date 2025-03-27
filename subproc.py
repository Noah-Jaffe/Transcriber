import batchalign as ba
from tkinter import messagebox
import os
import sys
import json
from types import FunctionType

def transcribe_file(input_file, model_name=None, num_speakers=2, lang="eng"):
    try:
        num_speakers = int(num_speakers)
    except:
        num_speakers = 2
    
    # transcribe
    whisper = ba.WhisperEngine(model=model_name, lang=lang)

    # split by speaker
    diarization = ba.NemoSpeakerEngine(num_speakers=num_speakers)

    # recognize pauses
    disfluency = ba.DisfluencyReplacementEngine()

    # tbh uncertain
    retrace = ba.NgramRetraceEngine()
    
    # morphotag to get %mor %gra etc.
    morphosyntax = ba.StanzaEngine()

    # align
    utr = ba.WhisperUTREngine()
    fa = ba.Wave2VecFAEngine()

    pipeline_activity = [action for action in [
        whisper,
        diarization if num_speakers > 1 else None,
        disfluency,
        retrace,  # uncertain how this benifits us
        # morphosyntax,
        utr,
        fa
    ] if action]
    
    # create a pipeline
    nlp = ba.BatchalignPipeline(*pipeline_activity)
    doc = ba.Document.new(media_path=input_file, lang=lang)
    doc = nlp(doc)
    chat = ba.CHATFile(doc=doc)
    n = 0
    output_file = f"{input_file}{'_'+str(n) if n > 0 else ''}.cha"
    while 1:
        output_file = f"{input_file}{'_'+str(n) if n > 0 else ''}.cha"
        if not os.path.exists(output_file):
            break
        n += 1
    chat.write(output_file, write_wor=False)
    print(f"Wrote to {output_file}", flush=True)
    return spawn_popup_activity(title="COMPLETED!",message=f"Completed transcription of\n{input_file}\nOutput file can be found here:\n{output_file}\nOpen file now?", yes=lambda: os.startfile(output_file))

def spawn_popup_activity(title, message, yes=None, no=None):
    result = messagebox.askyesno(title=title, message=message)
    if result and yes and type(yes) == FunctionType:
        return yes()
    elif not result and no and type(no) == FunctionType:
        return no()

if __name__ == "__main__":
    print("Attempting to transcribe for:", sys.argv[1:], flush=True)
    print(sys.argv, flush=True)
    for data in sys.argv[1:]:
        try:
            args = json.loads(data)
        except:
            print(f"Failed to parse input data: {data}")
            continue
        transcribe_file(**args)
    print("Attempt completed for:", sys.argv[1:], flush=True)