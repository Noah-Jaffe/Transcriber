import batchalign as ba
from tkinter import messagebox
import os
import sys
import json
from types import FunctionType
from huggingface_hub.hf_api import repo_exists as is_valid_model_id
import pycountry
from CustomAiEngine import CustomAiEngine
import traceback


def transcribe_file(input_file, model_name=None, num_speakers=2, lang="eng"):
    try:
        num_speakers = int(num_speakers)
    except:
        num_speakers = 2
    try:
        lang = pycountry.languages.lookup(lang).alpha_3
    except:
        lang = 'eng'
    # transcribe
    # whisper = CustomAiEngine(model=model_name, lang=lang)
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
        # fa
    ] if action]
    
    n = 0
    output_file = f"{input_file}{'_'+str(n) if n > 0 else ''}.cha"
    while 1:
        output_file = f"{input_file}{'_'+str(n) if n > 0 else ''}.cha"
        if not os.path.exists(output_file):
            break
        n += 1
    doc = ba.Document.new(media_path=input_file, lang=lang)
    for idx, activity in enumerate(pipeline_activity, start=1):
        nlp = ba.BatchalignPipeline(activity)
        try:
            doc = nlp(doc)
            chat = ba.CHATFile(doc=doc)
            chat.write(output_file, write_wor=False)
            with open(output_file,'a',encoding='utf-8') as f:
                f.write(f"@DEBUG Completed step {idx}/{len(pipeline_activity)} - {(type(activity).__name__).replace('Engine','')}\n")
        except Exception as e:
            print(traceback.format_exc(e))
            print(f"{output_file} made it to step: {idx-1}/{len(pipeline_activity)}")
            with open(output_file,'a',encoding='utf-8') as f:
                f.write(f"@DEBUG error during step {idx}/{len(pipeline_activity)} - {(type(activity).__name__).replace('Engine','')}\n")
        
        
    # create a pipeline
    # nlp = ba.BatchalignPipeline(*pipeline_activity)
    # doc = ba.Document.new(media_path=input_file, lang=lang)
    # doc = nlp(doc)
    # chat = ba.CHATFile(doc=doc)
    # n = 0
    # output_file = f"{input_file}{'_'+str(n) if n > 0 else ''}.cha"
    # while 1:
    #     output_file = f"{input_file}{'_'+str(n) if n > 0 else ''}.cha"
    #     if not os.path.exists(output_file):
    #         break
    #     n += 1
    # chat.write(output_file, write_wor=False)
    print(f"Wrote to {output_file}", flush=True)
    # try:
    #     os.startfile(output_file)
    # except:
    #     pass
    # this is process blocking so we dont do it for now
    # return spawn_popup_activity(title="COMPLETED!",message=f"Completed transcription of\n{input_file}\nOutput file can be found here:\n{output_file}\nOpen file now?", yes=lambda: os.startfile(output_file))

def spawn_popup_activity(title, message, yes=None, no=None):
    result = messagebox.askyesno(title=title, message=message)
    if result and yes and type(yes) == FunctionType:
        return yes()
    elif not result and no and type(no) == FunctionType:
        return no()

if __name__ == "__main__":
    sys.argv.append('{"input_file":"D:\\\\Parent-Child Interactions\\\\Parent-Child Interactions\\\\P002_PCI.mp3","num_speakers":3,"lang":"","model_name":"openai/whisper-base.en"}')
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