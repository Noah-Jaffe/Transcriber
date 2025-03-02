import batchalign as ba
import ffmpeg
import whisper
import subprocess
import os
import traceback

INP_FN=".tmp_align/badfriends.mp3"
OUT_FN=".tmp_align/badfriends.cha"
# ASR
whisper = ba.WhisperEngine(lang="eng")
# retracing and disfluency analysis
retrace = ba.NgramRetraceEngine()
disfluency = ba.DisfluencyReplacementEngine()
# morphosyntax
morphosyntax = ba.StanzaEngine()

# create a pipeline
nlp = ba.BatchalignPipeline(whisper, retrace, disfluency, morphosyntax)
# and run it!
doc = nlp(INP_FN)
chat = ba.CHATFile(doc=doc)
chat.write(OUT_FN)

quit()
nlp = ba.BatchalignPipeline.new("asr,morphosyntax", lang="eng", num_speakers=2)
doc = ba.Document.new(media_path=FN, lang="eng")
doc = nlp(doc) # this is equivalent to nlp("audio.mp3"), we will make the initial doc for you
# pipeline contents
# whisper = ba.WhisperEngine(lang="eng")
# speakers = ba.NemoSpeakerEngine(num_speakers=2)
# morphosyntax = ba.StanzaEngine()

# # create a pipeline
# nlp = ba.BatchalignPipeline(whisper, speakers, morphosyntax)
# # and run it!
# doc = ba.Document.new(media_path="./tmp_inp/audio.wav", lang="eng")
# doc = nlp(doc) # could also do: # doc = nlp("./tmp_inp/audio.wav") 
print(doc)
