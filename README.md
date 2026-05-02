# Korean Dashboard - Mew

Dashboard FastAPI pour apprendre le coréen. Les cours et le vocab sont versionnés directement dans ce repo — un LLM connecté à ce GitHub peut les lire, les enrichir, et mettre à jour le dashboard.

## Structure

```
content/
  vocab/        → CSV par livre (3A, 3B, 4A, 4B) : hangul, traduction, exemples
  lessons/      → HTML par niveau et par cours (과)
templates/      → UI Jinja2
static/         → CSS + assets
main.py         → Serveur FastAPI (port 8181)
```

## Lancer le dashboard

```bash
pip install -r requirements.txt
python main.py
# → http://localhost:8181
```

## Ajouter du contenu

- **Vocab** : déposer un fichier `Vocab XX.csv` dans `content/vocab/` (format : hangul, fr, exemple, traduction, explication + marqueurs de chapitre `N과`)
- **Lessons** : déposer un fichier HTML dans `content/lessons/<NIVEAU>/` (ex: `content/lessons/4B/4B 과1.html`)

Le dashboard les détecte automatiquement au prochain rechargement.
