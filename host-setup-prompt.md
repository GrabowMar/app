# Frontend Container Setup

The `docker-compose.local.yml` has been updated with a `frontend` service that runs the SvelteKit dev server. The `API_TARGET` environment variable is set so the Vite proxy routes API requests to the Django container.

## Steps

1. **Build and start the frontend container:**

```bash
cd /app
docker compose -f docker-compose.local.yml up -d --build frontend
```

2. **Verify it's running:**

```bash
docker compose -f docker-compose.local.yml ps frontend
```

3. **Test it responds:**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
```

4. **If the build fails, check logs:**

```bash
docker compose -f docker-compose.local.yml logs frontend
```

## Expected Result

- Frontend container running and serving on **http://localhost:8080**
- API requests (`/api`, `/_allauth`, `/admin`, `/media`) proxied to Django on port 8000 via Docker networking
