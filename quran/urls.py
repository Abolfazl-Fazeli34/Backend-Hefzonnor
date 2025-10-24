# from typing import List
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from rest_framework_nested import routers
# from quran import views

# router = DefaultRouter()
# router.register(r'surahs', views.SurahViewSet, basename='surah')
# router.register(r'translator', views.TranslatorViewSet, basename='translator')

# surah_router = routers.NestedDefaultRouter(router, r'surahs', lookup='surah')
# surah_router.register(r'verses', views.VerseViewSet, basename='surah-verses')
# surah_router.register(r'translations', views.VerseTranslationViewSet, basename='surah-translations')
# surah_router.register(r'word-meanings', views.WordMeaningViewSet, basename='surah-word-meanings')
# surah_router.register(r'tafseer', views.TafseerViewSet, basename='surah-tafseer')
# surah_router.register(r'translation-audio', views.TranslationAudioViewSet, basename='surah-translation-audio')

# router.register(r'surah/verse/list', views.SurahVerseListViewSet, basename='surah_verse-list')
# router.register(r'audio/collection', views.AudioCollectionViewSet, basename='audio_collection')

# urlpatterns: List = [
#     path('', include(router.urls)),
#     path('', include(surah_router.urls)),
# ]

from typing import List
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from quran import views

router = DefaultRouter()
router.register(prefix=r'surahs', viewset=views.SurahViewSet, basename='surah')
router.register(prefix=r'verses', viewset=views.SearchTableViewSet, basename='verse')
router.register(prefix=r'surah/verse/list', viewset=views.SurahVerseListViewSet, basename='surah_verse-list')
router.register(prefix=r'audio/collection', viewset=views.AudioCollectionViewSet, basename='audio_collection')
router.register(prefix=r'qari', viewset=views.QariViewSet, basename='qari_list')
# router.register(r'verses/list', views.VersesViewSet, basename='verses')

router.register(prefix=r'translator', viewset=views.TranslatorViewSet, basename='translator')
router.register(prefix=r'verse/translation', viewset=views.VerseTranslationViewSet, basename='verse_translation')
router.register(prefix=r'word/meaning', viewset=views.WordMeaningViewSet, basename='word_meaning')
router.register(prefix=r'tafseer', viewset=views.TafseerViewSet, basename='tafseer')
router.register(prefix=r'translation/audio', viewset=views.TranslationAudioViewSet, basename='translation_audio')
router.register(r'tafseer-audio', views.TafseerAudioViewSet, basename='tafseer-audio')




urlpatterns: List = [
    path('', include(router.urls)),
] 
