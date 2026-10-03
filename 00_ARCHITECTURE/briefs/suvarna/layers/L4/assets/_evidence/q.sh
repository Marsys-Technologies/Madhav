#!/bin/zsh
# read-only wrapper: usage q.sh "SQL"
( source ~/.config/suvarna/pgenv.sh >/dev/null 2>&1; /opt/homebrew/bin/psql -X -A -F'|' -c "SET default_transaction_read_only=on; $1" 2>&1 | grep -v '^SET$' )
