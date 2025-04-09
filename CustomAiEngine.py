from batchalign.document import *
from batchalign.pipelines.base import *
from batchalign.pipelines.asr.utils import *
from batchalign.models import WhisperASRModel, BertUtteranceModel, BertCantoneseUtteranceModel

import pycountry

import logging

from ArbitraryASRModel import ArbatraryASRModel

L = logging.getLogger("batchalign")

from batchalign.utils.utils import correct_timing
from huggingface_hub.hf_api import repo_exists as is_valid_model_id
from batchalign.pipelines.asr.whisper import WhisperEngine
from batchalign.models import resolve

class CustomAiEngine(BatchalignEngine):

    @property
    def tasks(self):
        # if there is no utterance segmentation scheme, we only
        # run ASR
        if self.__engine:
            return [ Task.ASR, Task.UTTERANCE_SEGMENTATION ]
        else:
            return [ Task.ASR ]

    def __init__(self, model=None, lang="eng"):
        if not is_valid_model_id(model):
            raise Exception(f"{model} is not a valid model!")
            model = "talkbank/CHATUtterance-en"
        try:
            language = pycountry.languages.lookup(lang).name
            if language == "Yue Chinese":
                language = "Cantonese"
            if "greek" in language.lower():
                language = "Greek"
        except:
            language = None
        self.__whisper = ArbatraryASRModel(model, language=language)
        self.__lang = lang

        if resolve("utterance", self.__lang or 'eng') != None:
            L.debug("Initializing utterance model...")
            if lang != "yue":
                self.__engine = BertUtteranceModel(resolve("utterance", self.__lang or 'eng'))
            else:
                # we have special inference procedure for cantonese
                self.__engine = BertCantoneseUtteranceModel(resolve("utterance", lang))
            L.debug("Done.")
        else:
            self.__engine = None

    def generate(self, source_path, **kwargs):
        res = self.__whisper(self.__whisper.load(source_path).all())
        # for some reason the lang needs to be set here even if we previously didnt want to use it
        doc = process_generation(res, self.__lang or 'eng', utterance_engine=self.__engine)

        # define media tier
        media = Media(type=MediaType.AUDIO, name=Path(source_path).stem, url=source_path)
        doc.media = media

        return correct_timing(doc)