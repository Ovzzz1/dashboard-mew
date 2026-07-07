# HANDOFF — Korean Brain (système de mails quotidiens d'apprentissage du coréen)

> Doc de passation. Dernière mise à jour : **2026-07-07**.
> Objectif : permettre à un autre agent IA de reprendre le système sans contexte préalable.
> Voir aussi `~/korean-brain/CLAUDE.md` (rôle "prof IA" + rappel rapide).

---

## 1. Vue d'ensemble

Système perso d'apprentissage automatisé du coréen pour Matéo (compte `ovisegroupe@gmail.com`).
Deux briques :

1. **Mailer automatique** (`~/korean-brain/scripts/korean_mailer.py`) — envoie chaque jour des emails (vocab, leçon, tests) via des LaunchAgents macOS. Génère du **MP3 bilingue** (TTS) et des **exercices** (via Claude CLI).
2. **Dashboard web** (repo `~/Desktop/Git/dashboard-mew`, publié sur GitHub Pages : https://ovzzz1.github.io/dashboard-mew/) — flashcards + page de **test** interactif (QCM/saisie). Les emails renvoient vers ce dashboard.

C'est **séparé de la flotte SEO** de Matéo (rien à voir avec `~/Desktop/Git/` hors dashboard-mew).

---

## 2. État actuel (2026-07-07)

`~/korean-brain/progress/state.json` :

```json
{
  "vocab":  { "current_level": "4A", "current_과": 3, "word_index": 80, "last_email_date": "2026-07-06", ... },
  "lesson": { "current_level": "4B", "current_과": 2, "day_in_lesson": 2, "last_email_date": "2026-07-06" }
}
```

- **Vocab** : niveau 4A, 3과, ~mot 80. Avance de **10 mots/jour**.
- **Leçon** : niveau 4B, 2과, jour 2 (J2). Avance d'**un jour de leçon/jour**.
- ⚠️ **Vocab et leçon sont deux pistes INDÉPENDANTES à cadences différentes** : un 과 = **3 jours** côté leçon (J1/J2/J3) mais **~9 jours** côté vocab (car un 과 fait 66–114 mots). Donc la leçon "double" le vocab et prend de l'avance (elle est déjà en 4B, le vocab encore en 4A). **C'est normal, ne pas essayer de les resynchroniser.**

---

## 3. Fichiers & arborescence

```
~/korean-brain/
├── CLAUDE.md              # rôle "prof IA" + rappel
├── HANDOFF.md             # ce doc
├── scripts/
│   └── korean_mailer.py   # LE script principal (tout est là)
├── content/               # sources rapatriées (voir §6)
│   ├── vocab/Vocab 3A.csv, 3B.csv, 4A.csv, 4B.csv
│   ├── lessons/{3A,4A,4B}/{LEVEL} 과{N}.html
│   └── manifest.json
└── progress/
    ├── state.json         # progression (source de vérité)
    ├── state.lock         # verrou fichier (fcntl) — ne pas toucher
    ├── cron.log           # log de TOUS les runs (stdout+stderr)
    └── exercises_cache/{LEVEL}_{N}.json  # exercices pré-générés par Claude
```

`~/.korean_env` (hors repo) :
```
export KOREAN_GMAIL_PW="...(app password Gmail)..."
export GMAIL_APP_PW="...(idem, alias)..."
```

---

## 4. Planification (LaunchAgents macOS)

4 agents dans `~/Library/LaunchAgents/`, tous rechargés & **valides** (`plutil -lint OK`) :

| Plist | Commande | Quand |
|-------|----------|-------|
| `com.mateo.korean.vocab`   | `korean_mailer.py vocab`      | tous les jours **22h30** |
| `com.mateo.korean.lesson`  | `korean_mailer.py lesson`     | tous les jours **22h30** |
| `com.mateo.korean.recap`   | `korean_mailer.py recap_week` | **dimanche 10h** |
| `com.mateo.korean.testweek`| `korean_mailer.py test_week`  | **vendredi 20h** |

Chaque plist fait : `. $HOME/.korean_env && /Library/Frameworks/Python.framework/Versions/3.13/bin/python3 .../korean_mailer.py <cmd> >> .../cron.log 2>&1`

Recharger un agent après modif :
```bash
UID=$(id -u); L=com.mateo.korean.vocab
launchctl bootout   gui/$UID/$L 2>/dev/null
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/$L.plist
```

⚠️ **launchd ne rattrape PAS** une tâche si le Mac est éteint à l'heure prévue (seulement au réveil s'il était en veille). Si Matéo dit "j'ai rien reçu", vérifier d'abord si le Mac était allumé à 22h30.

⚠️ **Ne JAMAIS remettre de cron** pour ces jobs. Il y avait un doublon cron+launchd qui causait des double-envois — supprimé. Le crontab ne doit contenir aucune ligne "korean".

---

## 5. Python & env — PIÈGES CRITIQUES

- **Toujours** utiliser `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` (ou `python3` en interactif). C'est le **seul** Python qui a `edge_tts` (indispensable au MP3). **Pas** `/usr/bin/python3` (3.9, sans edge_tts → MP3 silencieusement absent).
- `~/.korean_env` **doit** faire `export ...` (sinon la variable n'est pas héritée par le process → mode `[DRY RUN]`, aucun mail réellement envoyé).
- Dépendances externes : `edge_tts` (pip, py3.13), `ffmpeg` (`/opt/homebrew/bin/ffmpeg`), Claude CLI (`~/.local/bin/claude`, pour générer les exercices).

---

## 6. Contenu (vocab CSV + leçons HTML)

- Le mailer lit le contenu depuis `~/korean-brain/content/` (constante `BASE` dans le script).
- **Pourquoi pas depuis dashboard-mew ?** launchd ne peut pas lire `~/Desktop` (protection TCC macOS → `PermissionError`). Le contenu a donc été **copié** hors zone protégée.
- **Source de vérité éditoriale = `~/Desktop/Git/dashboard-mew/content/`** (ce que voit le dashboard web).
- 👉 **Si on modifie le vocab ou une leçon dans dashboard-mew, il FAUT re-copier vers `~/korean-brain/content/`** sinon le mailer utilise l'ancienne version. Ex :
  ```bash
  cp -R ~/Desktop/Git/dashboard-mew/content/{vocab,lessons} ~/korean-brain/content/
  ```

Format vocab CSV : colonnes `한글, French, Example, Translated, Explanation`. Les lignes `N과` (ex `1과`) marquent le début d'un 과. Voir `parse_vocab()`.

---

## 7. Machine à états (comment ça avance)

### Piste VOCAB (`email_vocab`)
- Envoie `words[word_index : word_index+10]` du 과 courant, puis `word_index += 10`.
- Libellé "vocab de demain" : envoyé le soir (22h30) pour étude le lendemain.
- Quand `word_index >= nb_mots_du_과` → **jour TEST** : envoie le QCM de fin de 과 (`email_test_kwa`), passe au 과 suivant, `word_index=0`. Le test **consomme un jour** (pas de fournée ce jour-là).
- Fin de 8과 d'un niveau → niveau suivant (`LEVEL_ORDER = ["3A","3B","4A","4B"]`).
- Anti-doublon : si `last_email_date == aujourd'hui`, skip.

### Piste LEÇON (`email_lesson`)
- 3 jours par 과 : **J1** = lien "Learning" + pré-génération des exercices J2 en arrière-plan ; **J2** = fichier `.md` d'exercices (traduction Fr→Ko) en pièce jointe ; **J3** = lien "Workbook".
- `day_in_lesson` 1→2→3 puis passe au 과 suivant.

### Exercices (Claude CLI)
- Générés par `generate_exercises()` : **1 appel `claude -p` par point de grammaire** (H2 du HTML de la leçon).
- Le prompt inclut le **détail complet de la section de grammaire** (`extract_grammar_sections`) pour que les phrases respectent vraiment la structure enseignée (fix de juin, cf §9).
- Cache dans `progress/exercises_cache/{LEVEL}_{N}.json`.

### Recap dimanche / Test vendredi
- `recap_week` : récap des 과 vus dans la semaine (exercices + liens test). `test_week` : QCM sur `words_this_week`.

---

## 8. Dashboard web (dashboard-mew)

- Repo : `~/Desktop/Git/dashboard-mew` → push `main` → **GitHub Pages** auto-déploie (branche `main`, racine) sur https://ovzzz1.github.io/dashboard-mew/ (~1-2 min de délai).
- Tout est dans **`index.html`** (SPA, routes par hash : `#vocab/...`, `#lesson/...`, `#test/{level}/{과}`).
- **Page test** : saisie libre, correction par `checkAnswer()` (voir §9 pour la logique de matching). Si Matéo dit "le test valide/refuse à tort", c'est là qu'il faut regarder.
- Après un push, si Matéo voit encore l'ancien comportement → **hard refresh** (`Cmd+Shift+R`), c'est du cache navigateur.

---

## 9. Historique des bugs corrigés (contexte important)

Tous corrigés, mais à connaître car ils peuvent réapparaître :

1. **TCC/Desktop** (2026-06) — launchd ne lit pas `~/Desktop` → contenu copié dans `~/korean-brain/content/`. (§6)
2. **Mauvais Python** — plists passés sur py3.13 framework (edge_tts). (§5)
3. **env non exporté** — `.korean_env` doit faire `export`. (§5)
4. **Doublon cron+launchd** — double-envois ; cron korean supprimé. (§4)
5. **Race condition sur state.json** (2026-06-25) — vocab ET lesson à 22h30 faisaient chacun load→modify→save de TOUT le fichier ; la lesson (plus lente) écrasait la progression du vocab → vocab gelé 2 semaines (renvoyait 41-50 en boucle). **Fix** : verrou fichier `state_lock` (fcntl) sérialisant vocab/lesson/recap/tests + écriture atomique (temp+rename) dans `save_state`. `pregenerate` est **exclu** du verrou (n'écrit que le cache, lancé en background par lesson → sinon deadlock).
6. **Exercices hors-sujet** (2026-06) — la génération n'envoyait que le *titre* du point de grammaire à Claude → phrases ne respectant pas la structure (ex : -다가 -아/어서 -게 되다). **Fix** : injecter le détail de la section (`extract_grammar_sections`) + règles strictes dans le prompt.
7. **Test trop laxiste** (2026-07-07) — `checkAnswer` validait toute sous-chaîne de la bonne réponse (`seg.includes(gn)`) → faux positifs. **Fix** : matching strict par segment + normalisation (accents, articles, ponctuation, espaces coréens) + tolérance 1 faute de frappe en français uniquement. Dans `dashboard-mew/index.html`.
8. **Plists XML invalides** (2026-07-07) — `&&` non échappés (`&` brut) → `plutil` KO, risque au reboot. **Fix** : `&` → `&amp;`, tous `plutil -lint OK`.

---

## 10. Commandes utiles (debug / manuel)

```bash
# Lancer un envoi à la main (charge bien l'env d'abord) :
cd ~/korean-brain/scripts && . ~/.korean_env
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 korean_mailer.py vocab   # ou lesson / recap_week / test_week / test_kwa

# Voir l'état :
cat ~/korean-brain/progress/state.json

# Voir les derniers runs :
tail -40 ~/korean-brain/progress/cron.log

# Pré-générer les exercices d'un 과 (ex 4B 3과) :
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 korean_mailer.py pregenerate 4B 3
```

- Un envoi qui affiche `[DRY RUN]` = `KOREAN_GMAIL_PW` absent → sourcer `.korean_env` (avec `export`).
- Modifier `state.json` à la main est OK (le script relit à chaque run) — mais respecter la structure et ne pas tourner en parallèle d'un job (le verrou protège, mais éviter).

---

## 11. Caveats / points ouverts

- **Trou de vocab** : suite au gel (bug #5), Matéo n'a jamais reçu le vocab 4A **1과 (51→83)** ni **2과 (1→60)**. On a re-calé le pointeur au bon endroit calendaire sans renvoyer ces mots. Si besoin, on peut lui renvoyer un récap groupé de ces plages (option évoquée, pas faite).
- **Vocab 1 seul mot en fin de 과** : quand un 과 finit sur une fournée incomplète (ex mot 71/71), l'email ne contient qu'1 mot. Normal, pas un bug.
- **Dépendance au Mac allumé à 22h30** (pas de rattrapage launchd). Migration possible vers un serveur 24/7 / GitHub Actions un jour, mais compliquée par edge_tts+ffmpeg (audio). Non fait.
- **Test dashboard plus strict** depuis le fix #7 : si un mot a des traductions alternatives légitimes absentes du CSV (pas séparées par `,`), elles seront comptées fausses → compléter le CSV le cas échéant.

---

## 12. Rôle "prof IA" (quand Matéo parle depuis ~/korean-brain)

Voir `CLAUDE.md`. En résumé : lire `progress/state.json` pour connaître le niveau/과 exact, corriger les traductions du `.md` reçu par mail phrase par phrase (✅/❌ + explication), faire pratiquer un point de grammaire, ou converser en coréen. Niveau intermédiaire (4A/4B), corriger sans édulcorer.
