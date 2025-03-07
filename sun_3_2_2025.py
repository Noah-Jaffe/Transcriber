import batchalign as ba
import ffmpeg
import os
from math import log10
from tkinter import END, HORIZONTAL, LEFT, SOLID, Button, Label, Listbox, StringVar, Toplevel, filedialog, messagebox, ttk, Tk
from datetime import datetime
from gooey import Gooey, GooeyParser

TEMP_INP_FILES_DIR = "./.tmp_inp"
TEMP_OUT_FILES_DIR = "./.tmp_out"
try: os.mkdir(TEMP_INP_FILES_DIR)
except: pass
try: os.mkdir(TEMP_OUT_FILES_DIR)
except: pass

MODELS_DIRECTORY="./models" # where to save the models to
EXPECTED_RAW_FILE_TYPE='mp4' # placeholder, this might not be needed
BEST_FILE_TYPE_FOR_TRANSCRIPTION='wav' # placeholder, this might not be needed

@Gooey()
def main():
    # transcribe
    whisper = ba.WhisperEngine(model=None, lang="eng")
    diarization = ba.NemoSpeakerEngine(num_speakers=2)
    disfluency = ba.DisfluencyReplacementEngine()
    retrace = ba.NgramRetraceEngine()
    # morphotag
    morphosyntax = ba.StanzaEngine()
    # align
    utr = ba.WhisperUTREngine()
    fa = ba.Wave2VecFAEngine()


    # create a pipeline
    nlp = ba.BatchalignPipeline(whisper, diarization, disfluency, retrace, morphosyntax, utr, fa)
    doc = ba.Document.new(media_path=".tmp_test/in/clip2.mp3", lang="eng")
    doc = nlp(doc)
    print(1)
    chat = ba.CHATFile(doc=doc)
    chat.write(".tmp_test/out/clip.cha")

if __name__ == "__main__":
    main()