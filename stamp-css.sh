#!/usr/bin/env bash
# Restampe les empreintes des feuilles de style dans index.html.
#
# Pourquoi : index.html est revalidé souvent par les navigateurs, mais les
# .css sont mis en cache longtemps (Hostinger + navigateur). Sans ?v=… on se
# retrouve avec le nouveau HTML peint par l'ancienne feuille.
#
#   static/style.css   → <link href="static/style.css?v=…">      (l'app)
#   static/lesson.css  → const LESSON_CSS_V = '…'                (iframe leçon)
#
# À lancer après CHAQUE modification de l'une des deux, avant de commit.
set -euo pipefail
cd "$(dirname "$0")"

changed=0

# ---- 1. static/style.css : attribut href du <link> --------------------------
# On ne cible QUE le href — surtout pas les mentions en commentaire, qui
# seraient corrompues par un remplacement global.
h_app=$(shasum -a 256 static/style.css | cut -c1-8)
before=$(grep -o 'href="static/style\.css[^"]*"' index.html | head -1)
perl -pi -e 's{href="static/style\.css[^"]*"}{href="static/style.css?v='"$h_app"'"}g' index.html
after=$(grep -o 'href="static/style\.css[^"]*"' index.html | head -1)
if [ "$before" != "$after" ]; then
    echo "style.css  : $before → $after"; changed=1
fi

# ---- 2. static/lesson.css : constante JS ------------------------------------
h_les=$(shasum -a 256 static/lesson.css | cut -c1-8)
before=$(grep -o "LESSON_CSS_V = '[a-f0-9]*'" index.html | head -1)
perl -pi -e "s{LESSON_CSS_V = '[a-f0-9]*'}{LESSON_CSS_V = '$h_les'}g" index.html
after=$(grep -o "LESSON_CSS_V = '[a-f0-9]*'" index.html | head -1)
if [ "$before" != "$after" ]; then
    echo "lesson.css : $before → $after"; changed=1
fi

[ "$changed" -eq 0 ] && echo "inchangé (style.css=$h_app, lesson.css=$h_les)"
exit 0
