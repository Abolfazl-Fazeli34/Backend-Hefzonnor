from typing import Any, List, Dict, Optional, Union
from rest_framework import permissions, generics, viewsets, filters, status
from rest_framework.request import Request
from rest_framework.response import Response
from django.db.models import Prefetch, QuerySet, Subquery, OuterRef
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import ValidationError
from django.db.models import Count, F
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer, BrowsableAPIRenderer, AdminRenderer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie, vary_on_headers
from rest_framework.parsers import JSONParser
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from quran.models import (
    Surah,
      Word,
        Qari,
          Verse,
            VerseTranslation,
              Translator,
                WordMeaning,
                  Tafseer,
                    TranslationAudio,
                      SearchTable,
                        TafseerAudio
    )
from quran.filters import (
    SurahFilter,
      AudioFilter,
        CombinedListFilter,
          VerseTranslationFilter,
            TranslatorFilter,
              WordMeaningFilter,
                TafseerFilter,
                  TranslationAudioFilter,
                    QariFilter,
                      TafseerAudioFilter
    )
from quran.paginations import StandardResultSetPagination, QuranResultPagination, SearchPagination
from quran.serializers import (
    SurahFullSerializer,
      AudioAyahSerializer,
        AudioPageSerializer,
          ListSurahWordSerializer,
            ListJuzSerializer,
              ListPageSerializer,
                AudioWordSerializer,
                  VerseSerializer,
                    VerseTranslationSerializer,
                      TranslatorSerializer,
                        WordMeaningSerializer,
                          TafseerSerializer,
                            TranslationAudioSerializer,
                              AudioSurahSerializer, 
                                QariSerializer,
                                  VerseTextSerializer,
                                    WordSerializer,
                                      SearchTableSerializer,
                                        TafseerAudioSerializer
)

class SurahViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SurahFullSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = QuranResultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SurahFilter
    # renderer_classes = [JSONRenderer]
    # renderer_classes = [AdminRenderer]
    # parser_classes = [JSONParser]
    search_fields = ['verses__text__plain',
    'verses__text__persian_friendly',]
    ordering_fields = ['id', 'name']
    ordering = ['id']


    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', "PATCH", "DELETE"]:
            return [permissions.IsAdminUser]
        return super().get_permissions()
    

    def get_queryset(self) -> QuerySet[Surah]:
        queryset = Surah.objects.annotate(
            pages_count=Count('verses__page_number', distinct=True),
            verse_count=Count('verses__verse_number', distinct=True)).prefetch_related(
            Prefetch(
                'verses',
                queryset=Verse.objects.select_related('text')
                    .prefetch_related(
                        Prefetch('wordsi', queryset=Word.objects.all().order_by('id').distinct(), to_attr='filtered_words')
                    )
                    .order_by('verse_number'),
                to_attr='prefetched_verses'
            )
        ).distinct()

        return queryset
    
    
    
    @method_decorator(cache_page(60 * 60 * 2, key_prefix='cache1'))
    @method_decorator(vary_on_headers('Authorization'), name='list')
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
        
    
        # response = super().list(request, *args, **kwargs)
        # search = request.query_params.get('search')
        # if search:
        #     for surah in response.data['results']:
        #         for page in surah['verses']['results']:
        #             page['items'] = [w for w in page['items'] if search in w['arabic_text']]
        #             page['verses'] = [v for v in page['verses'] if search in v['text']['full_tashkeel']]
        # return response



class SearchTableViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SearchTableSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = SearchPagination

    def get_queryset(self):
        queryset = SearchTable.objects.select_related('surah', 'verse')
        
        # Prefetch translations برای fa و en
        queryset = queryset.prefetch_related(
            Prefetch(
                'verse__translations',
                queryset=VerseTranslation.objects
                    .select_related('translator')  
                    .filter(translator__language__in=['fa', 'en']),
                to_attr='translations_cached'
            )
        )


        search = self.request.query_params.get('search')
        search_type = self.request.query_params.get('type', 'ar') 

        if search:
            query = SearchQuery(search)
            
            if search_type == 'ar':
                vector = (
                    SearchVector('SearchSP', weight='A') +
                    SearchVector('SearchP', weight='C') +
                    SearchVector('SearchA', weight='D')
                )
                queryset = queryset.annotate(rank=SearchRank(vector, query)) \
                                .filter(rank__gte=0.1) \
                                .order_by('-rank', 'surah__id', 'verse__id')
            elif search_type in ['fa', 'en']:
                lang = search_type
                translation_subquery = VerseTranslation.objects.filter(
                    verse=OuterRef('verse_id'),
                    translator__language=lang
                ).values('text')[:1]

                queryset = queryset.annotate(
                    translation_text=Subquery(translation_subquery)
                )

                vector = SearchVector('translation_text', weight='A')
                queryset = queryset.annotate(rank=SearchRank(vector, query)) \
                                .filter(rank__gte=0.1) \
                                .order_by('-rank', 'surah__id', 'verse__id')
        return queryset


# class VersesViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Verse.objects.all().prefetch_related(
#         Prefetch('words', queryset=Word.objects.all().order_by('id'))
#     )
#     serializer_class = VerseSerializer
#     filter_backends = [DjangoFilterBackend]
#     filterset_fields = ['surah', 'verse_number']



class SurahVerseListViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CombinedListFilter
    
    search_fields = [
        'surah__name',
        'surah__arabic_name',
        'surah__english_name',
        'verse__juz',
        'verse__page_number',
    ]
    ordering_fields = ['id', 'surah__arabic_name', 'surah__name']
    ordering = ['id']

    serializer_class = WordSerializer
    TYPE_SURAH = 'surah'
    TYPE_JUZ = 'juz'
    TYPE_PAGE = 'page'

    serializer_map = {
        TYPE_SURAH: ListSurahWordSerializer,
        TYPE_JUZ: ListJuzSerializer,
        TYPE_PAGE: ListPageSerializer,
    }

    @property
    def list_type(self) -> str:
        return self.request.query_params.get('type', self.TYPE_SURAH).lower()

    def get_queryset(self):
        if self.list_type == self.TYPE_SURAH:
            return (
                Word.objects.filter(type=2)
                .select_related("surah")
                .prefetch_related("verse__text")
                .annotate(
                    verse_count=Count("surah__verses", distinct=True)
                )
                .order_by("id")
            )
        return Word.objects.none()

    def get_serializer_class(self):
        return self.serializer_map.get(self.list_type, self.serializer_class)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def list(self, request, *args, **kwargs):
        search = request.query_params.get('search', None)

        if self.list_type == self.TYPE_JUZ:
            queryset = Verse.objects.all()
            if search:
                queryset = queryset.filter(juz=search)
            data = list(
                queryset.values('juz')
                .annotate(verse_count=Count('id'))
                .order_by('juz')
            )
            serializer = self.get_serializer(data, many=True)
            return Response(serializer.data)

        if self.list_type == self.TYPE_PAGE:
            queryset = Verse.objects.all()
            if search:
                queryset = queryset.filter(page_number=search)
            data = list(
                queryset.values(page=F('page_number'))
                .annotate(verse_count=Count('id'))
                .order_by('page')
            )
            serializer = self.get_serializer(data, many=True)
            return Response(serializer.data)

        return super().list(request, *args, **kwargs)



class QariViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = QariSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = QariFilter
    filterset_fields = ['type', 'language']
    search_fields = ['name', 'narrator']
    ordering_fields = ['id', 'name']
    ordering = ['id']

    def get_queryset(self):
        return Qari.objects.all().only('id', 'name', 'path', 'type', 'language', 'narrator').order_by('id')
    
    @method_decorator(cache_page(60 * 60, key_prefix='qari_list'))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class AudioCollectionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes: List[Any] = [permissions.AllowAny]
    queryset = Qari.objects.none()
    serializer_class = AudioWordSerializer
    pagination_class = StandardResultSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AudioFilter
    search_fields = ['arabic_text', 'persian_text', 'english_text']
    ordering_fields = ['id', 'word_number', 'page']
    ordering = ['id']

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        query_params = request.query_params
        qari_id = query_params.get("qari_id")
        surah_id = query_params.get("surah_id")
        ayah_id = query_params.get("ayah_id")
        page_number = query_params.get("page_number")
        word_id = query_params.get("word_id")

        if self._is_ayah_request(qari_id, surah_id, ayah_id):
            return self._get_ayah_audio(qari_id, surah_id, ayah_id)

        if self._is_surah_request(qari_id, surah_id):
            return self._get_surah_audio(qari_id, surah_id)

        if self._is_page_request(qari_id, page_number):
            return self._get_page_audio(qari_id, page_number)

        if self._is_word_request(surah_id, ayah_id, word_id):
            return self._get_word_audio(surah_id, ayah_id, word_id)

        return super().list(request, *args, **kwargs)

    def _is_surah_request(self, qari_id, surah_id) -> bool:
        return qari_id and surah_id

    def _is_ayah_request(self, qari_id, surah_id, ayah_id) -> bool:
        return all([qari_id, surah_id, ayah_id])

    def _is_page_request(self, qari_id, page_number) -> bool:
        return qari_id and page_number

    def _is_word_request(self, surah_id, ayah_id, word_id) -> bool:
        return all([surah_id, ayah_id, word_id])

    def _get_surah_audio(self, qari_id, surah_id) -> Response:
        serializer = AudioSurahSerializer(instance={}, context={"qari_id": qari_id, "surah_id": surah_id})
        return Response(serializer.data)

    def _get_ayah_audio(self, qari_id, surah_id, ayah_id) -> Response:
        pk = f"{int(qari_id):02d}{int(surah_id):03d}{int(ayah_id):03d}"
        serializer = AudioAyahSerializer(instance={}, context={"pk": pk})
        return Response(serializer.data)

    def _get_page_audio(self, qari_id, page_number) -> Response:
        pk = f"{int(qari_id):02d}{int(page_number):03d}"
        serializer = AudioPageSerializer(instance={}, context={"pk": pk})
        return Response(serializer.data)

    def _get_word_audio(self, surah_id, ayah_id, word_id) -> Response:
        pk = f"{int(surah_id):03d}{int(ayah_id):03d}{int(word_id):03d}"
        serializer = AudioWordSerializer(instance={}, context={"pk": pk})
        return Response(serializer.data)



class TranslatorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Translator.objects.all().distinct().reverse()
    serializer_class = TranslatorSerializer
    permission_classes = [permissions.AllowAny]
    # pagination_class = StandardResultSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TranslatorFilter
    search_fields = ['id', 'name', 'language', 'translation_type']
    ordering_fields = ['id', 'name']
    ordering = ['id']

class VerseTranslationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VerseTranslation.objects.all().select_related('verse', 'surah', 'translator').distinct()
    serializer_class = VerseTranslationSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VerseTranslationFilter
    search_fields = ['id', 'text']
    ordering_fields = ['id']
    ordering = ['id']

class WordMeaningViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WordMeaning.objects.all().select_related('surah', 'verse', 'translator').distinct()
    serializer_class = WordMeaningSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = WordMeaningFilter
    search_fields = ['id', 'root_id']
    ordering_fields = ['id']
    ordering = ['id']

class TafseerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tafseer.objects.all().select_related('translator', 'surah').distinct()
    serializer_class = TafseerSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TafseerFilter
    search_fields = ['id']
    ordering_fields = ['id']
    ordering = ['id']

class TranslationAudioViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TranslationAudio.objects.all().select_related('translator', 'surah')
    serializer_class = TranslationAudioSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TranslationAudioFilter
    search_fields = ['id', 'custom_id']
    ordering_fields = ['id', 'custom_id']
    ordering = ['id']

class TafseerAudioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TafseerAudioSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TafseerAudioFilter
    search_fields = ['id', 'custom_id', 'audio_link']
    ordering_fields = ['id', 'custom_id', 'from_aya', 'to_aya']
    ordering = ['id']

    def get_queryset(self):
        queryset = TafseerAudio.objects.select_related('translator', 'surah').order_by('from_aya')

        aya_number = self.request.query_params.get('aya_number')
        surah_id = self.request.query_params.get('surah')

        if aya_number and surah_id:
            queryset = queryset.filter(surah_id=surah_id, from_aya__lte=aya_number, to_aya__gte=aya_number)

        return queryset


# prefetch_related(
    # Prefetch('verse_translations', queryset=VerseTranslation.objects.all().select_related('surah', 'verse')),
    # Prefetch('word_meaning', queryset=WordMeaning.objects.all().select_related("surah", 'verse')),
    # Prefetch('tafseer', queryset=Tafseer.objects.all().select_related('surah')), 
    # Prefetch('translation_audio', queryset=TranslationAudio.objects.all().select_related('surah'))).distinct()



# class TranslatorCombinedViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = Translator.objects.all().distinct()
#     serializer_class = TranslatorSerializer
#     permission_classes = [permissions.AllowAny]
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_class = TranslatorCombinedFilter
#     search_fields = ['name', 'language', 'translation_type']
#     ordering_fields = ['id', 'name']
#     ordering = ['id']

#     def retrieve(self, request, *args, **kwargs):
#         translator = self.get_object()

#         # Prefetch همه داده‌های مرتبط با مترجم
#         translator = Translator.objects.prefetch_related(
#             Prefetch('verse_translations', queryset=VerseTranslation.objects.select_related('verse', 'surah')),
#             Prefetch('word_meaning', queryset=WordMeaning.objects.select_related('verse', 'surah')),
#             Prefetch('tafseer', queryset=Tafseer.objects.select_related('surah')),
#             Prefetch('translation_audio', queryset=TranslationAudio.objects.select_related('surah'))
#         ).get(pk=translator.id)

#         data = {
#             "translator": TranslatorSerializer(translator).data,
#             "verse_translations": VerseTranslationSerializer(translator.verse_translations.all(), many=True).data,
#             "word_meanings": WordMeaningSerializer(translator.word_meaning.all(), many=True).data,
#             "tafseer": TafseerSerializer(translator.tafseer.all(), many=True).data,
#             "translation_audio": TranslationAudioSerializer(translator.translation_audio.all(), many=True).data,
#         }
#         return Response(data)
