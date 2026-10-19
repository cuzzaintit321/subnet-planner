#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
gh auth status
gh auth setup-git
if [[ -e .git ]]; then echo 'Git checkout exists; inspect before publishing manually.'; exit 1; fi
if gh repo view cuzzaintit321/subnet-planner >/dev/null 2>&1; then
    echo 'Repository exists; inspect before publishing manually.'; exit 1
fi
git init -b main
git add .
git -c user.name='Jason Edwards' \
    -c user.email='228125969+cuzzaintit321@users.noreply.github.com' \
    commit -m 'Add Python systems tool with tests, documentation, and CI'
gh repo create cuzzaintit321/subnet-planner --public --source . --remote origin --push \
    --description 'Offline Python IPv4 and IPv6 subnet planner with address ranges, subnet splitting, overlap checks, and JSON reports.'
