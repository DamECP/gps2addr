# gps2addr 📍

> **Convert GPS coordinates (DMS format) into a human-readable postal address — straight from your terminal.**
>
> *Convertit des coordonnées GPS au format DMS en adresse postale lisible — directement depuis votre terminal.*

---

> 🤖 **This project was written entirely without manual coding.**
> The script was generated through a conversation with [Claude](https://claude.ai) (Anthropic), using natural language instructions only — no code was written by hand.
>
> 🤖 **Ce projet a été écrit entièrement sans coder manuellement.**
> Le script a été généré via une conversation avec [Claude](https://claude.ai) (Anthropic), en utilisant uniquement des instructions en langage naturel — aucune ligne de code n'a été écrite à la main.

---

## 🇬🇧 English

### What it does

`gps2addr` takes a GPS coordinate in **DMS format** (Degrees, Minutes, Seconds) — the format output by tools like **ExifTool** — and returns the corresponding human-readable address using the [OpenStreetMap Nominatim API](https://nominatim.org/).

If the coordinate is ambiguous (missing N/S or E/W hemisphere reference, which happens when EXIF metadata is incomplete), the tool automatically queries **all 4 possible locations** and displays them side by side with color coding, so you can identify the correct one from context.

### Features

- ✅ Parses DMS format as output by ExifTool (`26 deg 12' 14.76", 28 deg 2' 50.28"`)
- ✅ Handles missing hemisphere references with an **ambiguity mode** (4 hypotheses displayed)
- ✅ Parallel geocoding of all 4 quadrants for fast results
- ✅ Returns street, neighbourhood, city, postcode, region, country
- ✅ Color-coded terminal output with ASCII banner
- ✅ Accepts decimal coordinates (`--lat` / `--lon`)
- ✅ Pipe-friendly (works with ExifTool output directly)
- ✅ Raw JSON output mode (`--json`)
- ✅ No external dependencies — pure Python 3 stdlib only
- ✅ No API key required

### Requirements

- Python 3.10+
- Internet access (calls the Nominatim public API)

### Installation

No installation needed. Just download the script:

```bash
wget https://raw.githubusercontent.com/damECP/gps2addr/main/gps2addr.py
chmod +x gps2addr.py
```

### Usage

```bash
# Basic DMS string (ambiguous — no N/S/E/W)
python3 gps2addr.py "26 deg 12' 14.76\", 28 deg 2' 50.28\""

# DMS with hemisphere references (unambiguous)
python3 gps2addr.py "26 deg 12' 14.76\" S, 28 deg 2' 50.28\" E"

# Force hemisphere manually after identifying the correct quadrant
python3 gps2addr.py "26 deg 12' 14.76\", 28 deg 2' 50.28\"" --lat-ref S --lon-ref E

# Decimal degrees
python3 gps2addr.py --lat 26.2041 --lon 28.0473 --lat-ref S --lon-ref E

# Pipe directly from ExifTool
exiftool -p '$GPSLatitude, $GPSLongitude' photo.jpg | python3 gps2addr.py

# Raw JSON response
python3 gps2addr.py "26 deg 12' 14.76\", 28 deg 2' 50.28\"" --json

# Disable colors (for logging or non-TTY output)
python3 gps2addr.py "26 deg 12' 14.76\", 28 deg 2' 50.28\"" --no-color

# Change output language
python3 gps2addr.py "26 deg 12' 14.76\", 28 deg 2' 50.28\"" --lang fr
```

### Options

| Option | Description |
|---|---|
| `coords` | DMS coordinate string (positional argument) |
| `--lat` | Latitude in decimal degrees |
| `--lon` | Longitude in decimal degrees |
| `--lat-ref N\|S` | Force North or South hemisphere |
| `--lon-ref E\|W` | Force East or West hemisphere |
| `--lang` | Language for address output (default: `en`) |
| `--json` | Print raw Nominatim JSON response |
| `--no-color` | Disable ANSI color output |

### Color coding

| Color | Meaning |
|---|---|
| **Gray** | Structural / metadata (labels, separators, raw coordinates) |
| **White** | Data values (street, city, postcode) |
| **Green** | Positive result — address found, country name |
| **Red** | Negative result — no address, ocean, unmapped area |
| **Cyan** | Place type (residential, attraction, highway…) |
| **Yellow** | Ambiguity warning block |

In ambiguity mode, each quadrant has its own color for quick visual scanning:

| Quadrant | Color |
|---|---|
| NE | Cyan |
| NW | Blue |
| SE | Yellow |
| SW | Magenta |

### Why are coordinates sometimes ambiguous?

When a photo is edited by certain apps (social media, photo editors), the EXIF metadata fields `GPS Latitude Ref` and `GPS Longitude Ref` (which carry the N/S and E/W indicators) are stripped or never written. What remains are only the **absolute values** of latitude and longitude — which map to 4 different points on Earth.

`gps2addr` detects this situation automatically and presents all 4 hypotheses, letting you use the photo's visual context (landscape, architecture, vegetation, language on signs) to identify the correct location.

### Example output — ambiguous coordinates

```
  ⚠  AMBIGUOUS COORDINATES — N/S and E/W references are missing
  All four possible locations are shown below.

  ┌─[ NE ]  North / East   ✔  +26.204100°,  +28.047300°
  │  Type            Desert road
  │  Region          Matruh Governorate
  │  Country         Egypt (EG)
  └──────────────────────────────────────────────────────────

  ┌─[ SE ]  South / East   ✔  -26.204100°,  +28.047300°
  │  Type            Residential
  │  Street          14 Hendrik Potgieter Street
  │  City            2092 Johannesburg
  │  Region          Gauteng
  │  Country         South Africa (ZA)
  └──────────────────────────────────────────────────────────

  ┌─[ NW ]  North / West   ✘  +26.204100°,  -28.047300°
  │  (no address — likely ocean or unmapped territory)
  └──────────────────────────────────────────────────────────

  ┌─[ SW ]  South / West   ✘  -26.204100°,  -28.047300°
  │  (no address — likely ocean or unmapped territory)
  └──────────────────────────────────────────────────────────

  Tip: re-run with --lat-ref N|S  --lon-ref E|W to lock in a hemisphere.
```

### API & privacy

This tool uses the [Nominatim API](https://nominatim.org/) provided by OpenStreetMap. No coordinates are stored. Please respect the [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/) — this tool is intended for personal/occasional use, not bulk geocoding.

---

## 🇫🇷 Français

### Ce que ça fait

`gps2addr` prend une coordonnée GPS au **format DMS** (Degrés, Minutes, Secondes) — le format utilisé par des outils comme **ExifTool** — et retourne l'adresse postale correspondante via l'[API Nominatim d'OpenStreetMap](https://nominatim.org/).

Si la coordonnée est ambiguë (absence de référence N/S ou E/W, ce qui arrive quand les métadonnées EXIF sont incomplètes), l'outil interroge automatiquement les **4 localisations possibles** et les affiche côte à côte avec un code couleur, pour que vous puissiez identifier la bonne en vous aidant du contexte de la photo.

### Fonctionnalités

- ✅ Analyse le format DMS tel que produit par ExifTool (`26 deg 12' 14.76", 28 deg 2' 50.28"`)
- ✅ Gère les références d'hémisphère manquantes avec un **mode ambiguïté** (4 hypothèses affichées)
- ✅ Géocodage parallèle des 4 quadrants pour un résultat rapide
- ✅ Retourne rue, quartier, ville, code postal, région, pays
- ✅ Sortie terminal colorée avec bannière ASCII
- ✅ Accepte des coordonnées décimales (`--lat` / `--lon`)
- ✅ Compatible avec les pipes (fonctionne directement avec la sortie d'ExifTool)
- ✅ Mode sortie JSON brut (`--json`)
- ✅ Aucune dépendance externe — Python 3 stdlib uniquement
- ✅ Aucune clé API requise

### Prérequis

- Python 3.10+
- Accès internet (appels à l'API publique Nominatim)

### Installation

Aucune installation requise. Il suffit de télécharger le script :

```bash
wget https://raw.githubusercontent.com/DamECP/gps2addr/main/gps2addr.py
chmod +x gps2addr.py
```

### Utilisation

```bash
# Chaîne DMS basique (ambiguë — sans N/S/E/W)
python3 gps2addr.py "26 deg 12' 14.76\", 28 deg 2' 50.28\""

# DMS avec références d'hémisphère (non ambigu)
python3 gps2addr.py "26 deg 12' 14.76\" S, 28 deg 2' 50.28\" E"

# Forcer l'hémisphère manuellement après avoir identifié le bon quadrant
python3 gps2addr.py "26 deg 12' 14.76\", 28 deg 2' 50.28\"" --lat-ref S --lon-ref E

# Degrés décimaux
python3 gps2addr.py --lat 26.2041 --lon 28.0473 --lat-ref S --lon-ref E

# Pipe directement depuis ExifTool
exiftool -p '$GPSLatitude, $GPSLongitude' photo.jpg | python3 gps2addr.py

# Réponse JSON brute
python3 gps2addr.py "26 deg 12' 14.76\", 28 deg 2' 50.28\"" --json

# Désactiver les couleurs (pour les logs ou sorties non-TTY)
python3 gps2addr.py "26 deg 12' 14.76\", 28 deg 2' 50.28\"" --no-color

# Changer la langue de sortie
python3 gps2addr.py "26 deg 12' 14.76\", 28 deg 2' 50.28\"" --lang fr
```

### Options

| Option | Description |
|---|---|
| `coords` | Chaîne de coordonnées DMS (argument positionnel) |
| `--lat` | Latitude en degrés décimaux |
| `--lon` | Longitude en degrés décimaux |
| `--lat-ref N\|S` | Forcer l'hémisphère Nord ou Sud |
| `--lon-ref E\|W` | Forcer l'hémisphère Est ou Ouest |
| `--lang` | Langue de la sortie adresse (défaut : `en`) |
| `--json` | Afficher la réponse JSON brute de Nominatim |
| `--no-color` | Désactiver les couleurs ANSI |

### Code couleur

| Couleur | Signification |
|---|---|
| **Gris** | Structurel / métadonnées (labels, séparateurs, coordonnées brutes) |
| **Blanc** | Valeurs de données (rue, ville, code postal) |
| **Vert** | Résultat positif — adresse trouvée, nom du pays |
| **Rouge** | Résultat négatif — aucune adresse, océan, zone non cartographiée |
| **Cyan** | Type de lieu (résidentiel, attraction, route…) |
| **Jaune** | Bloc d'avertissement d'ambiguïté |

En mode ambiguïté, chaque quadrant a sa propre couleur pour une lecture rapide :

| Quadrant | Couleur |
|---|---|
| NE | Cyan |
| NO | Bleu |
| SE | Jaune |
| SO | Magenta |

### Pourquoi les coordonnées sont-elles parfois ambiguës ?

Quand une photo est éditée par certaines applications (réseaux sociaux, éditeurs photo), les champs EXIF `GPS Latitude Ref` et `GPS Longitude Ref` (qui indiquent N/S et E/W) sont supprimés ou jamais écrits. Il ne reste que les **valeurs absolues** de latitude et longitude — qui correspondent à 4 points différents sur le globe.

`gps2addr` détecte cette situation automatiquement et présente les 4 hypothèses, vous laissant utiliser le contexte visuel de la photo (paysage, architecture, végétation, langue des enseignes) pour identifier le bon emplacement.

### API & confidentialité

Cet outil utilise l'[API Nominatim](https://nominatim.org/) fournie par OpenStreetMap. Aucune coordonnée n'est stockée. Veuillez respecter la [politique d'utilisation de Nominatim](https://operations.osmfoundation.org/policies/nominatim/) — cet outil est destiné à un usage personnel et occasionnel, pas au géocodage en masse.

---

## License

MIT — do whatever you want with it.

---

*Made with [Claude](https://claude.ai) · No code was written by hand*
