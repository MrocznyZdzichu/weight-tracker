docker compose stop tracker-test
docker compose rm -f tracker-test
docker compose build tracker-test --no-cache
docker compose up -d tracker-test
