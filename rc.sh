docker compose --env-file .env up --scale tm-app=2 --scale tm-audit-app=2  -d 
docker compose exec nginx nginx -s reload
