# HANDOFF — Korean Brain (système de mails quotidiens d'apprentissage du coréen)

> Doc de passation. Dernière mise à jour : **2026-07-07** (v4 — vocab retiré du mailer).
> Objectif : permettre à un autre agent IA de reprendre le système sans contexte préalable.
> Voir aussi `~/korean-brain/CLAUDE.md` (rôle "prof IA" + rappel rapide).

---

## 1. Vue d'ensemble

Système perso d'apprentissage automatisé du coréen pour Matéo (compte `ovisegroupe@gmail.com`).
Deux briques :

1. **Mailer** (`~/korean-brain/scripts/korean_mailer.py`) — envoie 2 types d'emails via LaunchAgents macOS : la **leçon** (cycle 7 jours) et le **récap dimanche**. **Ne gère plus le vocab du tout** (retiré en v4, voir §2 et §9-#11) — pas de TTS/MP3, pas de QCM par mail.
2. **Dashboard web** (repo `~/Desktop/Git/dashboard-mew`, publié sur GitHub Pages : https://ovzzz1.github.io/dashboard-mew/) — vocab (table + **flashcards**), leçons, **exos pré-écrits** (10 par 과), page de **test** interactif (QCM/saisie). Les emails renvoient vers ce dashboard.

C'est **séparé de la flotte SEO** de Matéo (rien à voir avec `~/Desktop/Git/` hors dashboard-mew).

---

## 2. État actuel (2026-07-07)

`~/korean-brain/progress/state.json` — **ne contient plus que la leçon** depuis le retrait du vocab :
```json
{
  "lesson": { "current_level": "4A", "current_과": 2, "day_in_lesson": 1, "last_email_date": "" }
}
```

- **Leçon** : niveau 4A, 2과, jour 1 (J1). Cycle **7 jours/과** (1과 par semaine, voir §7).
- **Vocab** : **plus de tracking serveur du tout.** Étudié en libre-service via les **flashcards** du
  dashboard (`#flashcard/{book}`), auto-pacé, mastery trackée **côté navigateur** (`localStorage`,
  clé par mot). Pour 4A et 4B, chaque 과 est découpé en **exactement 7 lots égaux** (J1..J7,
  ex : 71 mots → 6×10 + 1×11) pour matcher le cycle leçon — voir §7bis. 3A/3B (déjà vus) restent
  sur l'ancien découpage fixe de 10 mots/lot ("Semaine 1, 2...").

---

## 3. Fichiers & arborescence

```
~/korean-brain/
├── CLAUDE.md              # rôle "prof IA" + rappel
├── HANDOFF.md              # ce doc
├── scripts/
│   └── korean_mailer.py   # ~270 lignes (v4) — lesson + recap_week uniquement
├── content/               # sources leçons (voir §6) — plus de vocab/ lu par le mailer
│   ├── vocab/              # ⚠️ legacy, gardé sur disque mais plus lu par korean_mailer.py
│   ├── lessons/{3A,4A,4B}/{LEVEL} 과{N}.html
│   └── manifest.json
└── progress/
    ├── state.json          # progression LEÇON uniquement (plus de clé "vocab")
    ├── state.lock          # verrou fichier (fcntl) — ne pas toucher
    └── cron.log             # log de TOUS les runs (stdout+stderr)
```

`~/.korean_env` (hors repo) :
```
export KOREAN_GMAIL_PW="...(app password Gmail)..."
export GMAIL_APP_PW="...(idem, alias)..."
```

---

## 4. Planification (LaunchAgents macOS)

**2 agents actifs** dans `~/Library/LaunchAgents/` (`plutil -lint OK`) :

| Plist | Commande | Quand |
|-------|----------|-------|
| `com.mateo.korean.lesson`  | `korean_mailer.py lesson`     | tous les jours **22h30** |
| `com.mateo.korean.recap`   | `korean_mailer.py recap_week` | **dimanche 10h** |

**2 agents désactivés** (déplacés dans `~/Library/LaunchAgents/disabled/`, `bootout` fait — ne se
rechargeront pas au reboot) :

| Plist désactivé | Ancienne commande | Raison |
|------------------|--------------------|--------|
| `com.mateo.korean.vocab.plist`     | `korean_mailer.py vocab`     | Vocab passé 100% flashcards dashboard (2026-07-07, décision explicite Matéo — "ça sera à rien") |
| `com.mateo.korean.testweek.plist`  | `korean_mailer.py test_week` | Dépendait de `words_this_week`, alimenté uniquement par le mail vocab → mort par cascade, retiré aussi ("tout couper", confirmé) |

Pour réactiver un jour : `mv ~/Library/LaunchAgents/disabled/com.mateo.korean.vocab.plist ~/Library/LaunchAgents/` puis `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.mateo.korean.vocab.plist` — **mais** le code Python correspondant (`email_vocab`, `email_test_kwa`, `email_test_week`, `parse_vocab`, `generate_audio`, TTS) a été **supprimé** du script (pas juste désactivé), il faudrait le réécrire.

⚠️ **launchd ne rattrape PAS** une tâche si le Mac est éteint à l'heure prévue.
⚠️ **Ne JAMAIS remettre de cron** pour ces jobs (le crontab doit rester vide de toute ligne "korean").

---

## 5. Python & env

- **Toujours** utiliser `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` (ou `python3` en interactif). Depuis le retrait du vocab, ce n'est **plus strictement nécessaire** pour `korean_mailer.py` (plus de TTS/`edge_tts`), mais reste la référence par cohérence.
- `~/.korean_env` **doit** faire `export ...` (sinon `[DRY RUN]`, aucun mail réellement envoyé).
- **Plus de dépendance `edge_tts` / `ffmpeg` / Claude CLI** dans le mailer (v4). Le script n'a plus
  besoin que de la stdlib Python (smtplib, json, re, fcntl...).

---

## 6. Contenu (leçons HTML — le vocab n'est plus lu par le mailer)

- Le mailer lit les leçons depuis `~/korean-brain/content/lessons/` (constante `BASE`).
- **Pourquoi pas depuis dashboard-mew ?** launchd ne peut pas lire `~/Desktop` (protection TCC
  macOS → `PermissionError`). Le contenu a donc été **copié** hors zone protégée.
- **Source de vérité éditoriale = `~/Desktop/Git/dashboard-mew/content/`**.
- 👉 Si on modifie une leçon dans dashboard-mew, **re-copier** :
  ```bash
  cp -R ~/Desktop/Git/dashboard-mew/content/lessons ~/korean-brain/content/
  ```
- **Le vocab CSV (`~/korean-brain/content/vocab/`) n'est plus lu par le mailer** depuis le retrait
  du vocab (v4) — il traîne encore sur disque (legacy) mais n'a plus d'usage. Le **vrai** vocab
  vécu par Matéo, c'est celui du dashboard (`content/vocab/` dans dashboard-mew, lu en frontend
  par les flashcards) — deux copies distinctes qui n'ont plus besoin d'être synchronisées.
- **Les exos ne sont jamais copiés côté korean-brain** — le mailer construit juste un lien
  (`exo_url()`) vers le dashboard GitHub Pages, il ne lit jamais leur contenu localement.

---

## 7. Machine à états — LEÇON uniquement (cycle 7 jours)

`LESSON_DAY_KIND = {1: learning, 2: exo, 3: workbook, 4: exo, 5: workbook, 6: learning, 7: exo}`
- **J1** Learning (lien leçon) · **J2** Exo (lien vers les 10 exos du 과) · **J3** Workbook (lien
  leçon) · **J4** Exo (suite) · **J5** Workbook · **J6** Learning (révision) · **J7** Exo (dernière
  session avant le 과 suivant).
- `day_in_lesson` 1→2→...→7 puis passe au 과 suivant (`day_in_lesson=1`).

### Exos — pré-écrits (skill `exo-coreen`), pas générés à la volée
Les 10 exos d'un 과 sont pré-écrits **en amont** (avant le début de sa semaine) via le skill
`exo-coreen` (`~/.claude/skills/exo-coreen/SKILL.md`), qui lit `content/vocab/` + `content/lessons/`
du repo dashboard-mew et écrit `content/exos/{LEVEL}/{N}과/Exo 1.md` à `Exo 10.md` (+
`content/manifest.json`). Le dashboard les sert via `#exo/{level}/{gwa}/{i}`. Le mailer ne fait
que construire l'URL (`exo_url()`) — zéro appel Claude, zéro pièce jointe.
⚠️ Il faut préparer le batch du 과 suivant **avant** le début de sa semaine, sinon lien mort en J2.

### Recap dimanche
Un seul lien vers les exos du **과 de leçon en cours** (`state["lesson"]`). Plus de liens test
vocab (retirés en v4, cf. §9-#11) — le test reste en libre-service sur le dashboard (`#test/...`).

---

## 7bis. Vocab — 100% dashboard, flashcards en 7 jours (v4, 2026-07-07)

Le vocab n'est **plus du tout géré par le mailer**. Tout se passe sur le dashboard :
- **Table vocab** (`#vocab/{book}/{과}`) — liste brute, filtrable.
- **Flashcards** (`#flashcard/{book}/{과}/{jour}`) — le mode d'étude principal. Pour **4A et 4B**,
  chaque 과 est découpé en **7 lots égaux** (fonction `fcGroups()` dans `index.html`) : au lieu de
  lots fixes de 10 mots ("Semaine 1, 2, 3..."), le nombre total de mots du 과 est réparti sur
  exactement 7 jours (J1..J7), le reste de la division allant sur les **derniers** jours. Exemple :
  71 mots → J1-J6 = 10 mots, J7 = 11 mots. 96 mots → J1-J2 = 13, J3-J7 = 14. Ça aligne le rythme
  vocab sur le cycle leçon (1과 = 1 semaine = 7 jours), sans mail, à son rythme.
- **3A/3B** (déjà vus) restent sur l'ancien découpage fixe de 10 mots/lot ("Semaine N") —
  `fcIsDaily(bookId)` dans `index.html` détermine quel livre utilise quel découpage.
- **Mastery** (maîtrisé / à réviser / à apprendre / non évalué) trackée en `localStorage`
  (`getLvlStore`/`syncLvlStore`), par mot, indépendamment du mailer — aucune donnée serveur.
- **Test** (`#test/{level}/{과}`) — QCM/saisie libre sur le chapitre entier, déjà autonome (ne
  dépendait déjà pas du mailer), reste la façon de se tester quand on veut.

---

## 8. Dashboard web (dashboard-mew)

- Repo : `~/Desktop/Git/dashboard-mew` → push `main` → **GitHub Pages** auto-déploie (~1-2 min).
- Tout est dans **`index.html`** (SPA, routes hash : `#vocab/...`, `#flashcard/...`, `#lesson/...`,
  `#exo/{level}/{gwa}/{i}`, `#exos`, `#test/{level}/{과}`).
- **Page exo** : onglets Exo 1..N, corrections repliables (`<details>`), notes de grammaire —
  syntaxe : une ligne `*texte*` seule → `<p class="exo-note">`, **pas** de blockquote `>` (piège
  rencontré le 2026-07-07, cf. §9-#10).
- **Page test** : `checkAnswer()` fait le matching, cf. §9-#7 pour la logique.
- Après un push, si Matéo voit encore l'ancien comportement → **hard refresh** (`Cmd+Shift+R`).
- **Fichiers internes non servis** (racine du repo, jamais dans `content/`) : `CLAUDE.md` (ADN
  "강인"), `CONFIG.md` (état live), `HANDOFF.md` (copie de ce doc).

---

## 9. Historique des bugs corrigés / changements majeurs

1. **TCC/Desktop** (2026-06) — launchd ne lit pas `~/Desktop` → contenu copié dans `~/korean-brain/content/`.
2. **Mauvais Python** (obsolète depuis v4, plus de TTS) — plists passés sur py3.13 framework (edge_tts).
3. **env non exporté** — `.korean_env` doit faire `export`. (§5)
4. **Doublon cron+launchd** — double-envois ; cron korean supprimé.
5. **Race condition sur state.json** (2026-06-25) — verrou fichier `state_lock` (fcntl) + écriture atomique.
6. **Exercices hors-sujet** (2026-06, obsolète depuis v3) — non-applicable, exos pré-écrits désormais.
7. **Test trop laxiste** (2026-07-07) — `checkAnswer` validait toute sous-chaîne → faux positifs. **Fix** : matching strict + normalisation + tolérance 1 faute FR. Dans `dashboard-mew/index.html`.
8. **Plists XML invalides** (2026-07-07) — `&` non échappés → `plutil` KO. **Fix** : `&amp;`.
9. **Migration v2 → v3** (2026-07-07) — cycle leçon 3j → 7j, exos pré-écrits (skill `exo-coreen`) au lieu de génération Claude à la volée, `recap_week` simplifié, reset état → Vocab 4A 2과 / Leçon 4A 2과.
10. **Note de grammaire mal formatée** (2026-07-07) — syntaxe blockquote (`> *texte*`) non reconnue par `exoBlock()` dans `index.html`, qui attend une ligne entière `*texte*`. **Fix** : suppression du `> ` dans les 5 exos concernés.
11. **Migration v3 → v4 — retrait total du vocab-mail** (2026-07-07) — décision de Matéo : le mail vocab quotidien "ça sera à rien" une fois les flashcards réorganisées en 7 jours/과. Conséquences en cascade assumées ("tout couper", confirmé) : `email_vocab`, `email_test_kwa`, `email_test_week`, `parse_vocab`, `generate_audio` (TTS) et `test_url` supprimés du script (709→272 lignes) ; agents `com.mateo.korean.vocab` et `.testweek` désactivés (déplacés dans `disabled/`) ; `state.json` réduit à la seule clé `lesson` ; `recap_week` perd sa section "tests vocab de la semaine". En parallèle, les flashcards du dashboard (4A/4B) sont redécoupées de lots fixes de 10 mots vers **7 lots égaux par 과** (`fcGroups()`), pour que le vocab s'étudie à son rythme mais dans la même logique hebdomadaire que la leçon (cf. §7bis).

---

## 10. Commandes utiles (debug / manuel)

```bash
# Lancer un envoi à la main :
cd ~/korean-brain/scripts && . ~/.korean_env
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 korean_mailer.py lesson   # ou recap_week

# Voir l'état :
cat ~/korean-brain/progress/state.json

# Voir les derniers runs :
tail -40 ~/korean-brain/progress/cron.log

# Vérifier quels agents korean tournent :
launchctl list | grep korean   # doit afficher exactement 2 : lesson, recap
```

- Un envoi qui affiche `[DRY RUN]` = `KOREAN_GMAIL_PW` absent → sourcer `.korean_env` (avec `export`).
- Seules les commandes `lesson` et `recap_week` existent depuis la v4 (`vocab`, `test_kwa`,
  `test_week`, `pregenerate` ont tous été retirés au fil des versions).

---

## 11. Caveats / points ouverts

- **Trou de vocab historique** (avant v4) : Matéo n'a jamais reçu 4A 1과 (51→83) ni 2과 (1→60) par
  mail — non pertinent maintenant que le vocab est en libre-service flashcards (il peut y revenir
  quand il veut, sans notion de "trou").
- **Dépendance au Mac allumé à 22h30** pour la leçon (pas de rattrapage launchd).
- **Batch d'exos à préparer à l'avance** : écrire les 10 exos d'un 과 avant le début de sa semaine
  (idéalement le dimanche précédent), sinon lien mort en J2.
- **Vocab CSV dupliqué** (`~/korean-brain/content/vocab/` vs `dashboard-mew/content/vocab/`) : la
  copie korean-brain est **legacy et inutilisée**, plus besoin de la maintenir à jour. Pourrait
  être supprimée un jour pour éviter la confusion (pas fait, pas prioritaire).

---

## 12. Rôle "prof IA" (quand Matéo parle depuis ~/korean-brain)

Voir `CLAUDE.md`. En résumé : lire `progress/state.json` (ne contient plus que `lesson`) pour
connaître le 과 de leçon en cours, faire pratiquer un point de grammaire, ou converser en coréen.
Niveau intermédiaire (4A), corriger sans édulcorer. Pour le vocab, plus de state à consulter — il
vit uniquement côté dashboard (flashcards, mastery en localStorage). Pour préparer les exos d'un
과, utiliser le skill `exo-coreen` depuis une session sur `dashboard-mew` (pas depuis
`~/korean-brain`, cf. §6).
