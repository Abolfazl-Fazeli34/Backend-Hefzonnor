from .base import BaseSubtypeDispatcher
from ..generators.subtype_16_hard_verse_beginning_generators import VerseFirstWordHardGenerator
from ..generators.subtype_17_hard_verse_ending_generators import VerseLastWordHardGenerator
from ..generators.subtype_1_verse_beginning_generators import VerseFirstWordGenerator
from ..generators.subtype_2_verse_ending_generator import VerseLastWordGenerator
from ..generators.subtype_3_translation_generators import VerseToTranslationGenerator, TranslationToVerseGenerator
from ..generators.subtype_4_verse_details import VerseDetailsGenerator
from ..generators.subtype_5_before_after import VerseBeforeAfterGenerator, VerseRelativeWordGenerator, \
    VerseOrderGenerator
from ..providers.db_extra_translations_provider import DatabaseExtraTranslationProvider
from ..providers.db_extra_verse_provider import DatabaseExtraVerseDetailsProvider, DatabaseExtraVerseProvider
from ..providers.db_extra_words_provider import DatabaseExtraWordsProvider, HardStartWordProvider, HardEndWordProvider


class VerseBeginningSubtypeDispatcher(BaseSubtypeDispatcher):
    def __init__(self):
        generator_map = {
            10: lambda: VerseFirstWordGenerator(
                extra_words_provider=DatabaseExtraWordsProvider,
                ask_from_number=False,
            ),
        }
        super().__init__(generator_map)


class VerseEndingSubtypeDispatcher(BaseSubtypeDispatcher):
    def __init__(self):
        generator_map = {
            20: lambda: VerseLastWordGenerator(
                extra_words_provider=DatabaseExtraWordsProvider,
                ask_from_number=False,
            ),
        }
        super().__init__(generator_map)


class VerseTranslationSubtypeDispatcher(BaseSubtypeDispatcher):
    def __init__(self):
        generator_map = {
            30: lambda: VerseToTranslationGenerator(
                extra_translations_provider=DatabaseExtraTranslationProvider,
                ask_from_number=False,
            ),
            31: lambda: TranslationToVerseGenerator(
                options_from_number=False,
            )
        }
        super().__init__(generator_map)


class VerseDetailSubtypeDispatcher(BaseSubtypeDispatcher):
    def __init__(self):
        generator_map = {
            40: lambda: VerseDetailsGenerator(
                extra_verse_provider=DatabaseExtraVerseDetailsProvider,
                ask_from_number=False,
            ),
            41: lambda: TranslationToVerseGenerator(
                options_from_number=True
            ),
            42: lambda: VerseToTranslationGenerator(
                extra_translations_provider=DatabaseExtraTranslationProvider,
                ask_from_number=True,
            ),
            43: lambda: VerseLastWordGenerator(
                extra_words_provider=DatabaseExtraWordsProvider,
                ask_from_number=True,
            ),
            44: lambda: VerseFirstWordGenerator(
                extra_words_provider=DatabaseExtraWordsProvider,
                ask_from_number=True,
            ),
            45: lambda: VerseDetailsGenerator(
                extra_verse_provider=DatabaseExtraVerseDetailsProvider,
                ask_from_number=True,
            )
        }
        super().__init__(generator_map)


class VerseBeforeAfterSubtypeDispatcher(BaseSubtypeDispatcher):
    def __init__(self):
        generator_map = {
            54: lambda: VerseBeforeAfterGenerator(
                extra_verse_provider=DatabaseExtraVerseProvider(),
                direction='after',
            ),
            53: lambda: VerseBeforeAfterGenerator(
                extra_verse_provider=DatabaseExtraVerseProvider(),
                direction='before',
            ),
            52: lambda: VerseOrderGenerator(),
            51: lambda: VerseRelativeWordGenerator(
                extra_words_provider=DatabaseExtraWordsProvider(),
                direction='before',
            ),
            50: lambda: VerseRelativeWordGenerator(
                extra_words_provider=DatabaseExtraWordsProvider(),
                direction='after',
            )

        }

        super().__init__(generator_map)


class VerseHardBeginningSubtypeDispatcher(BaseSubtypeDispatcher):
    def __init__(self):
        generator_map = {
            161: lambda: VerseFirstWordHardGenerator(
                hard_start_provider=HardStartWordProvider
            )
        }
        super().__init__(generator_map)


class VerseHardEndingSubtypeDispatcher(BaseSubtypeDispatcher):
    def __init__(self):
        generator_map = {
            171: lambda: VerseLastWordHardGenerator(
                hard_end_provider=HardEndWordProvider
            )
        }
        super().__init__(generator_map)
