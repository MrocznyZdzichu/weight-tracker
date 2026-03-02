docker compose stop tracker
docker compose rm -f tracker
docker compose build tracker --no-cache
docker compose up -d tracker