#!/bin/bash

set -e

echo "🔄 Synchronisation avec upstream..."

# Sync main
echo "📌 Synchronisation de 'main'..."
git checkout main
git fetch upstream
git rebase upstream/main
git push origin main --force-with-lease

# Sync arm64-minimal
echo "📌 Synchronisation de 'arm64-minimal'..."
git checkout arm64-minimal
git rebase main

# Gérer les conflits
if git status | grep -q "both modified"; then
    echo "⚠️  Conflits détectés dans arm64-minimal"
    echo "Résolvez les conflits puis lancez : git rebase --continue"
    exit 1
fi

git push origin arm64-minimal --force-with-lease

echo "✅ Synchronisation terminée!"
echo ""
echo "Branches up-to-date :"
git branch -v
