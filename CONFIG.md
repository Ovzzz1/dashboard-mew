# CONFIG.md — État live du setup Korean Brain

> **Ce fichier = photo de la config *actuellement en service*.** À jour au **2026-07-07**.
> Pas servi par le dashboard (hors `content/`) → invisible sur le web.
> Complément du `HANDOFF.md` (narratif complet + historique des bugs). Ici : le strict « qui tourne, où, quand ».
> **À re-vérifier / mettre à jour** dès qu'on change un plist, le state, ou qu'on modifie du contenu.

---

## 🟢 Ce qui tourne en ce moment

| Brique | Emplacement | Statut |
|--------|-------------|--------|
| **Mailer** | `~/korean-brain/scripts/korean_mailer.py` | actif (dernier run OK, exit `0`) |
| **Planif** | 4 LaunchAgents `~/Library/LaunchAgents/com.mateo.korean.*` | chargés, `plutil -lint OK` |
| **State** | `~/korean-brain/progress/state.json` | source de vérité progression |
| **Env** | `~/.korean_env` (2 lignes `export`) | OK (sinon → `[DRY RUN]`) |
| **Dashboard web** | repo `~/Desktop/Git/dashboard-mew` → GitHub Pages | https://ovzzz1.github.io/dashboard-mew/ |
| **Crontab korean** | — | **vide** (voulu ; cron interdit ici, cf HANDOFF §4) |

## ⏰ Planning (LaunchAgents)

| Agent | Commande | Cadence |
|-------|----------|---------|
| `com.mateo.korean.vocab`    | `korean_mailer.py vocab`      | **tous les jours 22h30** (vocab de demain, 10 mots) |
| `com.mateo.korean.lesson`   | `korean_mailer.py lesson`     | **tous les jours 22h30** (cycle **7 jours**/과 — voir HANDOFF §7) |
| `com.mateo.korean.recap`    | `korean_mailer.py recap_week` | **dimanche 10h00** (lien exo du 과 en cours + tests vocab) |
| `com.mateo.korean.testweek` | `korean_mailer.py test_week`  | **vendredi 20h00** |

⚠️ launchd **ne rattrape pas** si le Mac est éteint à l'heure prévue.

## 📍 Progression actuelle (state.json au 2026-07-07 — reset v3)

- **Vocab** : `4A` · 2과 · word_index **0** (avance 10 mots/j). Reprise volontaire (trou connu sur 4A 1과/2과, cf. HANDOFF §11).
- **Leçon** : `4A` · 2과 · **J1/7** (cycle 7 jours = 1과/semaine, remplace l'ancien cycle 3 jours).
- Reset **décidé par Matéo** après une pause (nouveau taff), pas une resynchronisation automatique — les deux pistes redémarrent volontairement au même point (4A 2과) mais resteront indépendantes ensuite (cf. HANDOFF §2, §9-#9).

## 🔧 Runtime (à respecter sinon ça casse)

- **Python** : `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` **uniquement** (seul avec `edge_tts` pour le MP3). Pas `/usr/bin/python3`.
- **Déps** : `edge_tts` (pip 3.13), `ffmpeg` (`/opt/homebrew/bin/ffmpeg`). **Claude CLI n'est plus une dépendance runtime** du mailer depuis la v3 (les exos sont pré-écrits, pas générés à la volée — voir HANDOFF §7 et skill `exo-coreen`).
- **Contenu** : le mailer lit `~/korean-brain/content/` (copie), **pas** `dashboard-mew/content/` (TCC macOS bloque `~/Desktop` sous launchd). Exception : les **exos** ne sont jamais copiés côté korean-brain, le mailer se contente d'un lien (`exo_url()`) vers le dashboard GitHub Pages.

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

## 🔁 Sync contenu (le piège n°1 à retenir)

Vérité éditoriale = `~/Desktop/Git/dashboard-mew/content/`. Après toute modif vocab/leçon, **re-copier** :
```bash
cp -R ~/Desktop/Git/dashboard-mew/content/{vocab,lessons} ~/korean-brain/content/
```
Sinon le mailer envoie l'ancienne version.

## 🩺 Check-santé express

```bash
launchctl list | grep korean                      # 4 agents, colonne statut = 0
cat ~/korean-brain/progress/state.json            # où on en est
tail -20 ~/korean-brain/progress/cron.log         # derniers envois
crontab -l | grep -i korean                        # doit être VIDE
```

## 📂 Docs liées

- `HANDOFF.md` (ce repo, copie de `~/korean-brain/HANDOFF.md`) — passation complète + historique bugs.
- `~/korean-brain/CLAUDE.md` — rôle prof IA côté korean-brain.
- `CLAUDE.md` (ce repo) — ADN prof (rigueur grammaticale + sources normatives). Interne, non exposé.

---

### Note — « centraliser les scripts dans le dashboard »
**Impossible de faire du dashboard le lieu d'exécution** du mailer : sous launchd, macOS (TCC) **interdit
la lecture de `~/Desktop`** → le script et son contenu *doivent* vivre dans `~/korean-brain/` pour tourner.
Le dashboard reste la **source de vérité éditoriale + l'UI web**, `~/korean-brain/` reste le **runtime**.
Si on veut quand même *versionner* le script ici, on peut y déposer un **miroir de référence** (clairement
étiqueté « pas la copie live ») — au prix d'un sync manuel de plus. Pas fait par défaut pour éviter ce coût.
