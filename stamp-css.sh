#!/usr/bin/env bash
# Restampe l'empreinte de static/style.css dans le <link> d'index.html.
#
# Pourquoi : index.html est revalidé souvent par les navigateurs, mais
# static/style.css est mis en cache longtemps (Hostinger + navigateur).
# Sans ?v=… on se retrouve avec le nouveau HTML peint par l'ancienne CSS.
#
# À lancer après CHAQUE modification de static/style.css, avant de déployer.
set -euo pipefail
cd "$(dirname "$0")"

hash=$(shasum -a 256 static/style.css | cut -c1-8)

# On ne cible QUE l'attribut href du <link> — surtout pas les mentions de
# « style.css » en commentaire, qui seraient corrompues par un remplacement global.
before=$(grep -o 'href="static/style\.css[^"]*"' index.html | head -1)
perl -pi -e 's{href="static/style\.css[^"]*"}{href="static/style.css?v='"$hash"'"}g' index.html
after=$(grep -o 'href="static/style\.css[^"]*"' index.html | head -1)

if [ "$before" = "$after" ]; then
    echo "inchangé : $after"
else
    echo "restampé : $before → $after"
fi
