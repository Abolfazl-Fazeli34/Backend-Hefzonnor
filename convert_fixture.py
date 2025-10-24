import os
import json

# مسیر پوشه quran_json اصلی و خروجی
input_dir = "quran_json"
output_dir = "quran_fixture"
os.makedirs(output_dir, exist_ok=True)

# ترتیب بارگذاری برای جلوگیری از خطای FK
load_order = [
    "quran_surah.json",
    "quran_versetext.json",
    "quran_verse.json",
    "quran_qari.json",
    "quran_word.json",
    "quran_translator.json",
    "quran_versetranslation.json",
    "quran_wordmeaning.json",
    "quran_root.json",
    "quran_verserootindex.json",
    "quran_tafseer.json",
    "quran_translationaudio.json",
    "quran_unwantedword.json",
    "quran_searchtable.json",
    "quran_tafseeraudio.json",
]

# نام مدل Django برای هر فایل
model_map = {
    "quran_surah.json": "quran.surah",
    "quran_versetext.json": "quran.versetext",
    "quran_verse.json": "quran.verse",
    "quran_qari.json": "quran.qari",
    "quran_word.json": "quran.word",
    "quran_translator.json": "quran.translator",
    "quran_versetranslation.json": "quran.versetranslation",
    "quran_wordmeaning.json": "quran.wordmeaning",
    "quran_root.json": "quran.root",
    "quran_verserootindex.json": "quran.verserootindex",
    "quran_tafseer.json": "quran.tafseer",
    "quran_translationaudio.json": "quran.translationaudio",
    "quran_unwantedword.json": "quran.unwantedword",
    "quran_searchtable.json": "quran.searchtable",
    "quran_tafseeraudio.json": "quran.tafseeraudio",
}

for filename in load_order:
    input_path = os.path.join(input_dir, filename)
    output_path = os.path.join(output_dir, filename.replace(".json", "_fixture.json"))

    if not os.path.exists(input_path):
        print(f"فایل {filename} پیدا نشد، رد می‌کنم.")
        continue

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fixture = []
    for i, row in enumerate(data, 1):
        fixture.append({
            "model": model_map.get(filename, "quran.unknown"),
            "pk": i,
            "fields": row
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fixture, f, ensure_ascii=False, indent=2)

    print(f"{filename} → {output_path} تبدیل شد ✅")
