# CONFIG.md — État live du setup Korean Brain

> **Ce fichier = photo de la config *actuellement en service*.** À jour au **2026-07-07** (v4 — vocab retiré du mailer).
> Pas servi par le dashboard (hors `content/`) → invisible sur le web.
> Complément du `HANDOFF.md` (narratif complet + historique des bugs). Ici : le strict « qui tourne, où, quand ».
> **À re-vérifier / mettre à jour** dès qu'on change un plist, le state, ou qu'on modifie du contenu.

---

## 🟢 Ce qui tourne en ce moment

| Brique | Emplacement | Statut |
|--------|-------------|--------|
| **Mailer** | `~/korean-brain/scripts/korean_mailer.py` (~270 lignes, v4) | actif (dernier run OK, exit `0`) |
| **Planif** | 2 LaunchAgents actifs `com.mateo.korean.{lesson,recap}` | chargés, `plutil -lint OK` |
| **Planif désactivée** | 2 plists dans `~/Library/LaunchAgents/disabled/` (`vocab`, `testweek`) | `bootout` fait, ne se rechargent pas au reboot |
| **State** | `~/korean-brain/progress/state.json` | ne contient plus que `lesson` (vocab retiré) |
| **Env** | `~/.korean_env` (2 lignes `export`) | OK (sinon → `[DRY RUN]`) |
| **Dashboard web** | repo `~/Desktop/Git/dashboard-mew` → GitHub Pages | https://ovzzz1.github.io/dashboard-mew/ |
| **Vocab** | 100% dashboard (flashcards), plus de tracking serveur | voir §Vocab ci-dessous |
| **Crontab korean** | — | **vide** (voulu ; cron interdit ici, cf HANDOFF §4) |

## ⏰ Planning (LaunchAgents actifs)

| Agent | Commande | Cadence |
|-------|----------|---------|
| `com.mateo.korean.lesson`   | `korean_mailer.py lesson`     | **tous les jours 22h30** (cycle **7 jours**/과 — voir HANDOFF §7) |
| `com.mateo.korean.recap`    | `korean_mailer.py recap_week` | **dimanche 10h00** (lien exo du 과 de leçon en cours) |

⚠️ launchd **ne rattrape pas** si le Mac est éteint à l'heure prévue.

**Désactivés le 2026-07-07** (décision explicite Matéo — "arrête les mails vocab, ça sera à
rien") : `com.mateo.korean.vocab` (mail vocab quotidien) et `com.mateo.korean.testweek` (QCM
vendredi, dépendait du mail vocab pour ses données → coupé aussi, "tout couper" confirmé). Code
Python correspondant **supprimé** du script, pas juste désactivé — voir HANDOFF §9-#11.

## 📍 Progression actuelle (state.json au 2026-07-07)

- **Leçon** : `4A` · 2과 · **J1/7** (cycle 7 jours = 1과/semaine).
- **Vocab** : plus de progression serveur. Étudié en libre-service sur les flashcards du
  dashboard, mastery en localStorage — voir §Vocab.

## 🔤 Vocab — flashcards 7 jours/과 (4A/4B), plus de mail (v4)

- Découpage : pour **4A et 4B**, chaque 과 est réparti en **7 lots égaux** au lieu de lots fixes
  de 10 (`fcGroups()` dans `index.html`) — le reste de la division va sur les **derniers** jours.
  Ex : 2과 (71 mots) → J1-J6 = 10, J7 = 11. 3과 (96 mots) → J1-J2 = 13, J3-J7 = 14.
- **3A/3B** (déjà vus) restent sur l'ancien découpage fixe "Semaine 1, 2..." (10 mots/lot) —
  `fcIsDaily(bookId)` détermine quel système s'applique à quel livre.
- Labels UI : "J{n}" pour 4A/4B (aligné sur le cycle leçon), "S{n}"/"Semaine {n}" pour 3A/3B.
- Mastery (maîtrisé/à réviser/à apprendre/non évalué) trackée en `localStorage`, par mot — aucune
  dépendance serveur, aucun risque de régression si le mailer change.
- Le test (`#test/{level}/{과}`) reste disponible en libre-service, indépendant du mailer (l'était
  déjà avant ce changement).

## 🔧 Runtime (à respecter sinon ça casse)

- **Python** : `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` reste la référence, mais n'est **plus strictement requis** pour le mailer depuis le retrait du TTS (v4) — plus de dépendance `edge_tts`/`ffmpeg`.
- **Claude CLI** : plus une dépendance runtime du mailer (les exos sont pré-écrits, pas générés à la volée — voir HANDOFF §7 et skill `exo-coreen`).
- **Contenu** : le mailer lit `~/korean-brain/content/lessons/` (copie, TCC macOS bloque `~/Desktop` sous launchd). `content/vocab/` côté korean-brain est **legacy inutilisé** — le mailer ne le lit plus. Les **exos** ne sont jamais copiés côté korean-brain, juste linkés (`exo_url()`).

## ✏️ Exos pré-écrits (batch d'avance à maintenir)

Statut au 2026-07-07 : **4A 2과 prêt** (10 exos dans `content/exos/4A/2과/`, déclarés dans
`content/manifest.json`). C'est le seul 과 couvert pour l'instant.

⚠️ Il faut préparer le batch du **과 suivant avant le début de sa semaine** (idéalement le
dimanche précédent), sinon le lien envoyé en J2 pointe vers une page vide. Utiliser le skill
`exo-coreen` (`~/.claude/skills/exo-coreen/SKILL.md`) — il lit directement `content/vocab/` et
`content/lessons/` du repo, pas besoin de lui fournir les fichiers.

⚠️ **Les exos doivent être poussés sur `main` (push GitHub) pour être en ligne** — GitHub Pages
sert le dashboard, ~1-2 min de délai après push. Un exo écrit localement mais non poussé = lien
mort dans l'email envoyé à cette heure-là.

## 🔁 Sync contenu leçons (le piège n°1 à retenir)

Vérité éditoriale = `~/Desktop/Git/dashboard-mew/content/`. Après toute modif de leçon, **re-copier** :
```bash
cp -R ~/Desktop/Git/dashboard-mew/content/lessons ~/korean-brain/content/
```
Sinon le mailer envoie l'ancienne version. **Le vocab n'a plus besoin d'être sync** (plus lu par le mailer).

## 🩺 Check-santé express

```bash
launchctl list | grep korean                      # 2 agents actifs : lesson, recap
cat ~/korean-brain/progress/state.json            # où on en est (leçon uniquement)
tail -20 ~/korean-brain/progress/cron.log         # derniers envois
crontab -l | grep -i korean                        # doit être VIDE
ls ~/Library/LaunchAgents/disabled/                # vocab.plist + testweek.plist désactivés
```

## 📂 Docs liées

- `HANDOFF.md` (ce repo, copie de `~/korean-brain/HANDOFF.md`) — passation complète + historique bugs.
- `~/korean-brain/CLAUDE.md` — rôle prof IA côté korean-brain.
- `CLAUDE.md` (ce repo) — ADN prof (rigueur grammaticale + sources normatives). Interne, non exposé.
- `~/.claude/skills/exo-coreen/SKILL.md` — génère les exos pré-écrits d'un 과.

---

### Note — « centraliser les scripts dans le dashboard »
**Impossible de faire du dashboard le lieu d'exécution** du mailer : sous launchd, macOS (TCC) **interdit
la lecture de `~/Desktop`** → le script et son contenu *doivent* vivre dans `~/korean-brain/` pour tourner.
Le dashboard reste la **source de vérité éditoriale + l'UI web**, `~/korean-brain/` reste le **runtime**.
