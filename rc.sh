docker compose --env-file .env up --scale tm-app=5 --scale tm-audit-app=3  -d --build
