# 🧠 Greeum v0.5.0

<p align="center">
  <a href="../../README.md">🇰🇷 한국어</a> |
  <a href="README_EN.md">🇺🇸 English</a> |
  <a href="README_ZH.md">🇨🇳 中文</a> |
  <a href="README_JP.md">🇯🇵 日本語</a> |
  <a href="README_ES.md">🇪🇸 Español</a> |
  <a href="README_DE.md">🇩🇪 Deutsch</a> |
  <a href="README_FR.md">🇫🇷 Français</a>
</p>

Mehrsprachiges LLM-unabhängiges Gedächtnisverwaltungssystem

## 📌 Überblick

**Greeum** (ausgesprochen: gri-eum) ist ein **universelles Gedächtnismodul**, das mit jedem LLM (Large Language Model) verbunden werden kann und die folgenden Funktionen bietet:
- Langzeitverfolgung von Benutzeräußerungen, Zielen, Emotionen und Absichten
- Abruf von Erinnerungen, die mit dem aktuellen Kontext zusammenhängen
- Erkennung und Verarbeitung von zeitlichen Ausdrücken in mehrsprachigen Umgebungen
- Funktioniert als "KI mit Gedächtnis"

Der Name "Greeum" ist vom koreanischen Wort "그리움" (Sehnsucht/Erinnerung) inspiriert und erfasst perfekt das Wesen des Gedächtnissystems.

## 🔑 Hauptfunktionen

- **Blockchain-ähnliches Langzeitgedächtnis (LTM)**: Blockbasierter Speicher mit Unveränderlichkeit
- **TTL-basiertes Kurzzeitgedächtnis (STM)**: Effiziente Verwaltung vorübergehend wichtiger Informationen
- **Semantische Relevanz**: Stichwort-/Tag-/Vektor-basiertes Erinnerungsabrufsystem
- **Wegpunkt-Cache**: Automatischer Abruf von Erinnerungen, die mit dem aktuellen Kontext zusammenhängen
- **Prompt-Composer**: Automatische Generierung von LLM-Prompts mit relevanten Erinnerungen
- **Temporaler Reasoner**: Fortgeschrittene Erkennung zeitlicher Ausdrücke in mehrsprachigen Umgebungen
- **Mehrsprachige Unterstützung**: Automatische Spracherkennung und -verarbeitung für Koreanisch, Englisch usw.
- **Model Control Protocol**: Unterstützung für die Integration externer Tools wie Cursor, Unity, Discord usw. über das separate [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP)-Paket

## ⚙️ Installation

1. Repository klonen
   ```bash
   git clone https://github.com/DryRainEnt/Greeum.git
   cd Greeum
   ```

2. Abhängigkeiten installieren
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 Verwendung

### Befehlszeilenschnittstelle

```bash
# Langzeitgedächtnis hinzufügen
python cli/memory_cli.py add -c "Ich habe ein neues Projekt gestartet und es ist wirklich aufregend"

# Erinnerungen nach Stichwörtern durchsuchen
python cli/memory_cli.py search -k "Projekt,aufregend"

# Erinnerungen nach zeitlichem Ausdruck durchsuchen
python cli/memory_cli.py search-time -q "Was habe ich vor 3 Tagen gemacht?" -l "de"

# Kurzzeitgedächtnis hinzufügen
python cli/memory_cli.py stm "Das Wetter ist heute schön"

# Kurzzeitgedächtnis abrufen
python cli/memory_cli.py get-stm

# Prompt generieren
python cli/memory_cli.py prompt -i "Wie läuft das Projekt?"
```

### REST-API-Server

```bash
# API-Server ausführen
python api/memory_api.py
```

Webschnittstelle: http://localhost:5000

API-Endpunkte:
- GET `/api/v1/health` - Gesundheitsprüfung
- GET `/api/v1/blocks` - Blöcke auflisten
- POST `/api/v1/blocks` - Block hinzufügen
- GET `/api/v1/search?keywords=keyword1,keyword2` - Suche nach Stichwörtern
- GET `/api/v1/search/time?query=yesterday&language=en` - Suche nach zeitlichem Ausdruck
- GET, POST, DELETE `/api/v1/stm` - Kurzzeitgedächtnis verwalten
- POST `/api/v1/prompt` - Prompt generieren
- GET `/api/v1/verify` - Blockchain-Integrität überprüfen

### Python-Bibliothek

```python
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input
from greeum.temporal_reasoner import TemporalReasoner

# Benutzereingabe verarbeiten
user_input = "Ich habe ein neues Projekt gestartet und es ist wirklich aufregend"
processed = process_user_input(user_input)

# Gedächtnis mit Block-Manager speichern
block_manager = BlockManager()
block = block_manager.add_block(
    context=processed["context"],
    keywords=processed["keywords"],
    tags=processed["tags"],
    embedding=processed["embedding"],
    importance=processed["importance"]
)

# Zeitbasierte Suche (mehrsprachig)
temporal_reasoner = TemporalReasoner(db_manager=block_manager, default_language="auto")
time_query = "Was habe ich vor 3 Tagen gemacht?"
time_results = temporal_reasoner.search_by_time_reference(time_query)

# Prompt generieren
cache_manager = CacheManager(block_manager=block_manager)
prompt_wrapper = PromptWrapper(cache_manager=cache_manager)

user_question = "Wie läuft das Projekt?"
prompt = prompt_wrapper.compose_prompt(user_question)

# An LLM übergeben
# llm_response = call_your_llm(prompt)
```

## 🧱 Architektur

```
greeum/
├── greeum/                # Kernbibliothek
│   ├── block_manager.py    # Langzeitgedächtnisverwaltung
│   ├── stm_manager.py      # Kurzzeitgedächtnisverwaltung
│   ├── cache_manager.py    # Wegpunkt-Cache
│   ├── prompt_wrapper.py   # Prompt-Zusammensetzung
│   ├── text_utils.py       # Textverarbeitungsdienstprogramme
│   ├── temporal_reasoner.py # Zeitliches Schlussfolgern
│   ├── embedding_models.py  # Embedding-Modellintegration
├── api/                   # REST-API-Schnittstelle
├── cli/                   # Befehlszeilentools
├── data/                  # Datenspeicherverzeichnis
├── tests/                 # Testsuite
```

## Branch-Verwaltungsregeln

- **main**: Stabile Release-Version-Branch
- **dev**: Kernfunktionsentwicklungs-Branch (nach Entwicklung und Tests zu main zusammengeführt)
- **test-collect**: Branch für Leistungskennzahlen und A/B-Testdatenerfassung

## 📊 Leistungstests

Greeum führt Leistungstests in den folgenden Bereichen durch:

### T-GEN-001: Steigerungsrate der Antwortspezifität
- Messung der Verbesserung der Antwortqualität bei Verwendung des Greeum-Gedächtnisses
- Bestätigung einer durchschnittlichen Qualitätsverbesserung von 18,6%
- Steigerung der spezifischen Informationseinschlüsse um 4,2

### T-MEM-002: Gedächtnissuchlatenz
- Messung der Suchgeschwindigkeitsverbesserung durch Wegpunkt-Cache
- Bestätigung einer durchschnittlichen Geschwindigkeitsverbesserung um das 5,04-fache
- Bis zu 8,67-fache Geschwindigkeitsverbesserung für mehr als 1.000 Gedächtnisblöcke

### T-API-001: API-Aufrufeffizienz
- Messung der Reduzierungsrate von Rückfragen aufgrund der gedächtnisbasierten Kontextbereitstellung
- Bestätigung einer Reduzierung der Rückfragenotwendigkeit um 78,2%
- Kostenreduzierungseffekt aufgrund verringerter API-Aufrufe

## 📊 Gedächtnisblockstruktur

```json
{
  "block_index": 143,
  "timestamp": "2025-05-08T01:02:33",
  "context": "Ich habe ein neues Projekt gestartet und es ist wirklich aufregend",
  "keywords": ["Projekt", "Start", "aufregend"],
  "tags": ["positiv", "Beginn", "Motivation"],
  "embedding": [0.131, 0.847, ...],
  "importance": 0.91,
  "hash": "...",
  "prev_hash": "..."
}
```

## 🔤 Unterstützte Sprachen

Greeum unterstützt die Erkennung zeitlicher Ausdrücke in den folgenden Sprachen:
- 🇰🇷 Koreanisch: Grundlegende Unterstützung für koreanische zeitliche Ausdrücke (어제, 지난주, 3일 전 usw.)
- 🇺🇸 Englisch: Vollständige Unterstützung für englische Zeitformate (yesterday, 3 days ago usw.)
- 🇩🇪 Deutsch: Unterstützung für deutsche zeitliche Ausdrücke (gestern, vor drei Tagen usw.)
- 🌐 Automatische Erkennung: Erkennt automatisch die Sprache und verarbeitet sie entsprechend

## 🔍 Beispiele für zeitliches Schlussfolgern

```python
# Koreanisch
result = evaluate_temporal_query("3일 전에 뭐 했어?", language="ko")
# Rückgabewert: {detected: True, language: "ko", best_ref: {term: "3일 전"}}

# Englisch
result = evaluate_temporal_query("What did I do 3 days ago?", language="en")
# Rückgabewert: {detected: True, language: "en", best_ref: {term: "3 days ago"}}

# Deutsch
result = evaluate_temporal_query("Was habe ich vor 3 Tagen gemacht?", language="de")
# Rückgabewert: {detected: True, language: "de", best_ref: {term: "vor 3 Tagen"}}

# Automatische Erkennung
result = evaluate_temporal_query("What happened yesterday?")
# Rückgabewert: {detected: True, language: "en", best_ref: {term: "yesterday"}}
```

## 🔧 Projektausbauplan

- **Model Control Protocol**: Weitere Informationen zur MCP-Unterstützung finden Sie im [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP)-Repository - ein separates Paket, das es Greeum ermöglicht, sich mit Tools wie Cursor, Unity, Discord usw. zu verbinden
- **Erweiterte mehrsprachige Unterstützung**: Zusätzliche Sprachunterstützung für Japanisch, Chinesisch, Spanisch usw.
- **Verbesserte Embeddings**: Integration tatsächlicher Embedding-Modelle (z.B. sentence-transformers)
- **Verbesserte Schlüsselwortextraktion**: Implementierung sprachspezifischer Schlüsselwortextraktion
- **Cloud-Integration**: Hinzufügen von Datenbank-Backends (SQLite, MongoDB usw.)
- **Verteilte Verarbeitung**: Implementierung verteilter Verarbeitung für groß angelegte Gedächtnisverwaltung

## 🌐 Website

Besuchen Sie die Website: [greeum.app](https://greeum.app)

## 📄 Lizenz

MIT-Lizenz

## 👥 Beitrag

Alle Beiträge sind willkommen, einschließlich Fehlerberichte, Funktionsvorschläge, Pull-Requests usw.!

## 📱 Kontakt

E-Mail: playtart@play-t.art 