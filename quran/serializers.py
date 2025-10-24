from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from quran.paginations import VersePagination, WordPagination, PagePagination
from typing import Any, List, Dict, Optional
from django.db.models import Prefetch
from django.utils.html import escape
from difflib import SequenceMatcher
import re
import unicodedata
from quran.models import (
    Surah,
      Word,
        Verse,
          VerseText,
            Qari,
              VerseTranslation,
                Translator, 
                  WordMeaning,
                    Tafseer,
                      TranslationAudio,
                        SearchTable,
                          TafseerAudio,
    )



class WordSerializer(serializers.ModelSerializer):
    fontPage = serializers.SerializerMethodField()
    fontName = serializers.SerializerMethodField()
    code = serializers.SerializerMethodField()
    # surah_id = serializers.IntegerField(source="surah.id", read_only=True)
    # surah_name = serializers.CharField(source="surah.name", read_only=True)

    class Meta:
        model = Word
        fields = [
            "id", "word_number", "verse_number", "type", "line", "page",
            "arabic_text", "code", "fontPage", "fontName", "aya_index", 'surah_id'
        ]
        read_only_fields = fields

    def get_code(self, obj):
        try:
            return chr(obj.code_ski_word)
        except (TypeError, ValueError):
            return None

    def get_fontPage(self, obj):
        if obj.page:
            return f"/fonts/QCF_P{obj.page:03}.TTF"
        return None

    def get_fontName(self, obj):
        if obj.page:
            return f"QCF_P{obj.page:03}"
        return None

class VerseTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerseText
        fields = [ 'plain', 'full_tashkeel', 'fuzzy']

class VerseSerializer(serializers.ModelSerializer):
    text = VerseTextSerializer()
    words = serializers.SerializerMethodField()
    highlighted_text = serializers.SerializerMethodField()

    class Meta:
        model = Verse
        fields = ['id', 'verse_number', 'text', 'words', 'page_number', 'section_number', 'highlighted_text']

    def get_words(self, obj):
        words = getattr(obj, 'filtered_words', [])
        return WordSerializer(words, many=True).data

    def get_highlighted_text(self, obj):
        request = self.context.get('request')
        search = request.query_params.get('search') if request else None
        if not search:
            return obj.text.full_tashkeel

        text = obj.text.full_tashkeel
        search = search.strip()

        matcher = SequenceMatcher(None, text, search)
        blocks = matcher.get_matching_blocks()
        highlighted = ""
        last_index = 0
        for block in blocks:
            start, _, size = block
            if size == 0:
                continue
            highlighted += text[last_index:start]
            highlighted += f'<span class="highlight">{text[start:start+size]}</span>'
            last_index = start + size
        highlighted += text[last_index:]
        return highlighted

class SurahFullSerializer(serializers.ModelSerializer):
    version = serializers.SerializerMethodField()
    # bismillah = serializers.SerializerMethodField()
    verses = serializers.SerializerMethodField()
    pages_count = serializers.SerializerMethodField()
    verse_count = serializers.SerializerMethodField() 

    class Meta:
        model = Surah
        fields = ['id', 'name', 'pages_count', 'verse_count', 'arabic_name', 'english_name', 'english_meaning', 'verses', 'version' ]

    def get_version(self, object):
        request = self.context.get('request')
        return request.version

    # def get_bismillah(self, obj):
    #     return WordSerializer(self.context["bismillah_cache"], many=True).data

    def get_pages_count(self, obj):
        return getattr(obj, 'pages_count', 0)

    def get_verse_count(self, obj):  
        return getattr(obj, 'verse_count', 0)
        

    def get_verses(self, surah_instance):
        request = self.context.get('request')
        all_verses = getattr(surah_instance, 'prefetched_verses', [])

        # فیلترهای مختلف
        juz_param = request.query_params.get('juz') if request else None
        page_param = request.query_params.get('page_number') if request else None
        verse_param = request.query_params.get('verse_number') if request else None
        verse_page_param = request.query_params.get('verse_page') if request else None

        if juz_param:
            all_verses = [v for v in all_verses if str(v.juz) == str(juz_param)]
        if page_param:
            all_verses = [v for v in all_verses if str(v.page_number) == str(page_param)]
        if verse_param:
            all_verses = [v for v in all_verses if str(v.verse_number) == str(verse_param)]

        all_verses.sort(key=lambda v: v.verse_number)

        pages_grouped_data = {}
        for verse in all_verses:
            current_page = verse.page_number or 0
            if current_page not in pages_grouped_data:
                pages_grouped_data[current_page] = {
                      'words': [],
                      'verses_metadata': []
                    }
            pages_grouped_data[current_page]['words'].extend(getattr(verse, 'filtered_words', []))
            pages_grouped_data[current_page]['verses_metadata'].append({ ## ------------
                "id": verse.id,
                "verse_count": len(all_verses),
                "verse_number": verse.verse_number,
                "text": {"full_tashkeel": verse.text.full_tashkeel if verse.text else None},
                "page_number": verse.page_number,
                "section_number": verse.section_number
            })

        paginated_pages_list = []
        for page_number, page_data in pages_grouped_data.items():
            # حذف تکراری‌ها
            unique_words = list({word.id: word for word in page_data['words']}.values())
            unique_words_serialized = WordSerializer(unique_words, many=True).data

            paginated_pages_list.append({
                'page': page_number,
                'items': unique_words_serialized,
                'verses': page_data['verses_metadata']  ## ------------
            })

        paginator = PagePagination()
        if verse_page_param:
            request._request.GET = request.GET.copy()
            request._request.GET['page'] = verse_page_param

        paginated_page = paginator.paginate_queryset(paginated_pages_list, request)
        response = paginator.get_paginated_response(paginated_page).data

        if response.get('next'):
            response['next'] = response['next'].replace('page=', 'verse_page=')
        if response.get('previous'):
            response['previous'] = response['previous'].replace('page=', 'verse_page=')

        return response


# --- جدول نرمال‌سازی کامل کاراکترها ---
CHAR_REPLACEMENTS = {
    "ي": "ی", "ى": "ی", "ئ": "ی",
    "ك": "ک",
    "ة": "ه", "ۀ": "ه",
    "ؤ": "و",
    "إ": "ا", "أ": "ا", "ٱ": "ا",
    "\u200c": " ",  # نیم‌فاصله
    "\u00A0": " ",  # non-breaking space
    "\u202F": " ",  # narrow no-break space
    "\u2060": "",   # word joiner
}

PUNCTUATION_REPLACEMENTS = {
    "،": ",", "؛": ";", "؟": "?", "“": '"', "”": '"', "‘": "'", "’": "'",
    "«": '"', "»": '"', "…": "...",
}

# --- معادل‌های حروف عربی و فارسی برای regex ---
LETTER_EQUIVALENCE = {
    "ا": "[اإأٱ]",
    "ه": "[هۀة]",
    "ی": "[یيىئ]",
    "ک": "[کك]",
    "و": "[وؤ]",
    "آ": "[آا]",
}

def normalize_arabic(text: str) -> str:
    if not text:
        return text
    text = unicodedata.normalize("NFC", text)
    for src, target in CHAR_REPLACEMENTS.items():
        text = text.replace(src, target)
    for src, target in PUNCTUATION_REPLACEMENTS.items():
        text = text.replace(src, target)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def remove_diacritics_with_map(text: str):
    clean = []
    mapping = []
    for i, c in enumerate(unicodedata.normalize("NFD", text)):
        if unicodedata.category(c) != "Mn":
            mapping.append(i)
            clean.append(c)
    return "".join(clean), mapping

def build_regex_from_word(word: str) -> str:
    pattern = ""
    for char in word:
        pattern += LETTER_EQUIVALENCE.get(char, re.escape(char))
    return pattern


class SearchTableSerializer(serializers.ModelSerializer):
    highlighted_SP = serializers.SerializerMethodField()
    highlighted_P = serializers.SerializerMethodField()
    highlighted_AE = serializers.SerializerMethodField()
    highlighted_SA = serializers.SerializerMethodField()
    highlighted_A = serializers.SerializerMethodField()
    highlighted_AE2 = serializers.SerializerMethodField()
    translation_h_fa = serializers.SerializerMethodField()
    translation_h_en = serializers.SerializerMethodField()
    translation_fa = serializers.SerializerMethodField()
    translation_en = serializers.SerializerMethodField() 

    class Meta:
        model = SearchTable
        fields = [
            "id", "surah", "verse", "verse_number",
            "PageNum", "JozNum", "HezbNum", "positioninpage",
            "SearchSP", "SearchP", "SearchAE", "SearchSA", "SearchA", "SearchAE2",
            "highlighted_SP", "highlighted_P", "highlighted_AE",
            "highlighted_SA", "highlighted_A", "highlighted_AE2",
            "translation_h_fa", "translation_h_en",
            "translation_fa", "translation_en",
        ]

    def _highlight_text(self, text_with_diac: str, search: str) -> str:
        if not text_with_diac or not search:
            return text_with_diac

        text_norm = normalize_arabic(text_with_diac)
        search_norm = normalize_arabic(search)
        clean_text, mapping = remove_diacritics_with_map(text_norm)
        search_clean, _ = remove_diacritics_with_map(search_norm)

        words = [w for w in search_clean.split() if w]
        if not words:
            return text_with_diac

        pattern = "|".join(build_regex_from_word(w) for w in words)
        matches = list(re.finditer(pattern, clean_text, flags=re.IGNORECASE))
        if not matches:
            return text_with_diac

        highlighted_parts = []
        last_index = 0
        for m in matches:
            start, end = m.start(), m.end()
            orig_start = mapping[start]
            orig_end = mapping[end - 1] + 1
            highlighted_parts.append(text_with_diac[last_index:orig_start])
            highlighted_parts.append(f'<span class="highlight">{text_with_diac[orig_start:orig_end]}</span>')
            last_index = orig_end
        highlighted_parts.append(text_with_diac[last_index:])
        return "".join(highlighted_parts)

    def _get_search(self):
        request = self.context.get("request")
        return request.query_params.get("search") if request else None

    def _get_type(self):
        request = self.context.get("request")
        return request.query_params.get("type", "ar") if request else "ar"

    def get_translation_fa(self, obj):
        for t in getattr(obj.verse, 'translations_cached', []):
            if t.translator.language == 'fa':
                return t.text
        return None

    def get_translation_en(self, obj):
        for t in getattr(obj.verse, 'translations_cached', []):
            if t.translator.language == 'en':
                return t.text
        return None


    # هایلایت متن‌های اصلی
    def get_highlighted_SP(self, obj):
        return self._highlight_text(obj.SearchSP, self._get_search())

    def get_highlighted_P(self, obj):
        return self._highlight_text(obj.SearchP, self._get_search())

    def get_highlighted_AE(self, obj):
        return self._highlight_text(obj.SearchAE, self._get_search())

    def get_highlighted_SA(self, obj):
        return self._highlight_text(obj.SearchSA, self._get_search())

    def get_highlighted_A(self, obj):
        return self._highlight_text(obj.SearchA, self._get_search())

    def get_highlighted_AE2(self, obj):
        return self._highlight_text(obj.SearchAE2, self._get_search())

    def get_translation_h_fa(self, obj):
        return self._highlight_text(
            self.get_translation_h_fa_raw(obj) or "",
            self._get_search()
        )

    def get_translation_h_en(self, obj):
        return self._highlight_text(
            self.get_translation_h_en_raw(obj) or "",
            self._get_search()
        )

    def get_translation_h_fa_raw(self, obj):
        for t in getattr(obj.verse, 'translations_cached', []):
            if t.translator.language == 'fa':
                return t.text
        return None

    def get_translation_h_en_raw(self, obj):
        for t in getattr(obj.verse, 'translations_cached', []):
            if t.translator.language == 'en':
                return t.text
        return None



class ListSurahWordSerializer(WordSerializer):
    verse_count = serializers.IntegerField(read_only=True)

    class Meta(WordSerializer.Meta):
        fields = WordSerializer.Meta.fields + ["verse_count"]

class ListJuzSerializer(serializers.Serializer):
    juz = serializers.IntegerField(min_value=1, max_value=30)
    verse_count = serializers.IntegerField(read_only=True)
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return f"جزء" # f"جزء {obj['juz']}"

class ListPageSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, max_value=604)
    verse_count = serializers.IntegerField(read_only=True)
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return f"صفحه" # f"صفحه {obj['page']}"



class QariSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qari
        fields = ['id', 'name', 'path', 'type', 'language', 'narrator']
        # extra_kwargs = {
        #     'name': {'help_text': 'نام قاری'},
        #     'path': {'help_text': 'مسیر ذخیره فایل صوتی'},
        #     'link': {'help_text': 'لینک اینترنتی فایل صوتی'},
        #     'type': {'help_text': 'نوع تلاوت (مثلاً ترتیل، تحقیق)'},
        #     'language': {'help_text': 'زبان فایل صوتی'},
        #     'narrator': {'help_text': 'راوی یا سبک قرائت (مثلاً حفص)'},
        # }
  


class AudioAyahSerializer(serializers.Serializer):
    qari_id = serializers.IntegerField(read_only=True)
    surah_id = serializers.IntegerField(read_only=True)
    ayah_id = serializers.IntegerField(read_only=True)

    qari_name = serializers.CharField(read_only=True)
    surah_name = serializers.CharField(read_only=True)
    audio_url = serializers.CharField(read_only=True)

    def to_representation(self, instance):
        raw_pk = self.context.get('pk')
        if not raw_pk:
            raise serializers.ValidationError("شناسه ورودی ارائه نشده است.")

        try:
            qari_id, surah_id, ayah_id = self._extract_ids_from_pk(raw_pk)
            qari = Qari.objects.get(id=qari_id)
            surah = Surah.objects.only('arabic_name').get(id=surah_id)
        except Qari.DoesNotExist:
            raise serializers.ValidationError("قاری مورد نظر یافت نشد.")
        except Surah.DoesNotExist:
            raise serializers.ValidationError("سوره مورد نظر یافت نشد.")

        audio_filename = f"{surah_id:03d}{ayah_id:03d}.mp3"
        audio_url = f"https://{qari.link}{audio_filename}"
        return {
            "qari_id": qari.id,
            "surah_id": surah.id,
            "ayah_id": ayah_id,
            "qari_name": qari.name,
            "surah_name": surah.arabic_name,
            "audio_url": audio_url,
        }

    def _extract_ids_from_pk(self, pk: str):
        pk = str(pk).zfill(8)
        return int(pk[:2]), int(pk[2:5]), int(pk[5:8])

class AudioPageSerializer(serializers.Serializer):
    page = serializers.IntegerField(read_only=True)
    qari_id = serializers.IntegerField(read_only=True)

    qari_name = serializers.CharField(read_only=True)
    surah_name = serializers.CharField(read_only=True, required=False)
    audio_urls = serializers.ListField(child=serializers.CharField(), read_only=True)

    def to_representation(self, instance):
        raw_pk = self.context.get('pk')
        if not raw_pk:
            raise serializers.ValidationError("شناسه ورودی ارائه نشده است.")

        try:
            qari_id = self._strip_leading_zeros(raw_pk[:2])
            page = self._strip_leading_zeros(raw_pk[2:5])
            qari = Qari.objects.get(id=qari_id)
        except Qari.DoesNotExist:
            raise serializers.ValidationError("قاری مورد نظر یافت نشد.")
        except ValueError:
            raise serializers.ValidationError("فرمت شناسه ورودی نامعتبر است.")

        verses = Verse.objects.filter(page_number=page).order_by("verse_number")
        audio_urls = []

        for verse in verses:
            surah_id = verse.surah_id
            ayah_id = verse.verse_number
            audio_filename = f"{surah_id:03d}{ayah_id:03d}.mp3"
            audio_url = f"https://{qari.link}{audio_filename}"
            audio_urls.append(audio_url)

        return {
            "page": page,
            "qari_id": qari.id,
            "qari_name": qari.name,
            "audio_urls": audio_urls,
        }

    def _strip_leading_zeros(self, value: str) -> int:
        return int(value.lstrip("0") or "0")

class AudioWordSerializer(serializers.Serializer):
    surah_number = serializers.IntegerField(read_only=True)
    ayah_number = serializers.IntegerField(read_only=True)
    word_number = serializers.IntegerField(read_only=True)

    surah_name = serializers.CharField(read_only=True)
    ayah_text = serializers.DictField(read_only=True)
    word_text = serializers.CharField(read_only=True)
    audio_url = serializers.CharField(read_only=True)

    def to_representation(self, instance):
        pk = self.context.get('pk')
        if not pk or len(pk) != 9 or not pk.isdigit():
            raise serializers.ValidationError("کد باید ۹ رقمی و فقط شامل عدد باشد.")

        surah, ayah, word = map(lambda s: int(s.lstrip('0') or '0'), [pk[:3], pk[3:6], pk[6:]])

        try:
            word_obj = Word.objects.select_related('surah', 'verse__text').get(
                surah__id=surah,
                verse__verse_number=ayah,
                word_number=word
            )
        except Word.DoesNotExist:
            raise serializers.ValidationError("کلمه‌ای با این مشخصات یافت نشد.")

        return {
            "surah_number": surah,
            "ayah_number": ayah,
            "word_number": word,
            "surah_name": word_obj.surah.name,
            "ayah_text": VerseTextSerializer(word_obj.verse.text).data if word_obj.verse and word_obj.verse.text else "",
            "word_text": word_obj.arabic_text,
            "audio_url": f"https://dl.hefzonnoor.ir/hifz/audio/wordsAudio/{str(surah)}/"
                         f"{str(surah).zfill(3)}_{str(ayah).zfill(3)}_{str(word).zfill(3)}.mp3"
        }

class AudioSurahSerializer(serializers.Serializer):
    qari_id = serializers.IntegerField(read_only=True)
    surah_id = serializers.IntegerField(read_only=True)
    qari_name = serializers.CharField(read_only=True)
    surah_name = serializers.CharField(read_only=True)
    audio_urls = serializers.ListField(child=serializers.CharField(), read_only=True)

    def to_representation(self, instance):
        qari_id = int(self.context.get("qari_id"))
        surah_id = int(self.context.get("surah_id"))
        try:
            qari = Qari.objects.only("id", "name", "link").get(id=qari_id)
            surah = Surah.objects.only("id", "arabic_name").get(id=surah_id)
        except Qari.DoesNotExist:
            raise serializers.ValidationError("قاری مورد نظر یافت نشد.")
        except Surah.DoesNotExist:
            raise serializers.ValidationError("سوره مورد نظر یافت نشد.")

        # همه آیات اون سوره
        verses = Verse.objects.filter(surah_id=surah_id).only("verse_number").order_by("verse_number")

        # تولید لینک‌ها
        audio_urls = [
            f"https://{qari.link}{surah_id:03d}{verse.verse_number:03d}.mp3"
            for verse in verses
        ]

        return {
            "qari_id": qari.id,
            "surah_id": surah.id,
            "qari_name": qari.name,
            "surah_name": surah.arabic_name,
            "audio_urls": audio_urls,
        }




class VerseTranslationSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerseTranslation
        fields = '__all__'

class TranslatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Translator
        fields = '__all__'

class WordMeaningSerializer(serializers.ModelSerializer):
    class Meta:
        model = WordMeaning
        fields = '__all__'

class TafseerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tafseer
        fields = '__all__'

class TranslationAudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslationAudio
        fields = '__all__'

class TafseerAudioSerializer(serializers.ModelSerializer):
    audio_link = serializers.SerializerMethodField()

    class Meta:
        model = TafseerAudio
        fields = '__all__'

    def get_audio_link(self, obj):
        base_url = ''
        if obj.translator_id == 10:
            base_url = 'https://dl.hefzonnoor.ir/hifz/audio/gharaati_tafsir/'
        elif obj.translator_id == 11:
            base_url = 'https://dl.hefzonnoor.ir/hifz/audio/nasimrahmat_tafsir/'

        if base_url:
            return f'{base_url}{obj.audio_link}.mp3'
        return obj.audio_link


