# Plan: sustituir Grafana por endpoint propio

Documento de trabajo para retomar más tarde. No es documentación final del proyecto.

## Contexto / motivación

Hoy Grafana está siendo overkill para lo que se enseña:
- 8 paneles (totales, % éxito, distribución por status/codec/resolución, últimos 5, top 5 errores).
- Todo deriva de una sola tabla (`transcodings`) en SQLite.
- Se pagan: 2 contenedores extra (`grafana` + `grafana-init` para `chown` UID 472), volumen persistente (`./grafana-data`), puerto 3000 expuesto, plugin `frser-sqlite-datasource`, credenciales que mantener, dos `docker-compose.yml` (con y sin Grafana), 3 docs (`grafana-setup.md`, `grafana-queries.md`, `grafana-dashboard.json` 721 líneas) e imágenes.

Decisión: integrarlo en el propio contenedor del enhancer con un mini-dashboard server-rendered.

## Stack elegido

- **FastAPI** + Uvicorn (descartado Django: ORM/admin/migraciones/auth no se necesitan; ya hay SQLAlchemy y la BD es read-only para el dashboard).
- **Jinja2** para 2 templates (login + dashboard). Sin SPA, sin build, sin JS framework.
- **`starlette.middleware.sessions.SessionMiddleware`** → cookie firmada con HMAC, sin backend de sesiones.
- Reutilizar `infrastructure/db/VideoRepositorySQL` (mismo `DatabaseConnection`).
- Uvicorn arranca en thread/task aparte dentro de `src/main.py`, conviviendo con el bucle `schedule` existente.

## Endpoints

| Método | Ruta          | Auth | Devuelve                                        |
|--------|---------------|------|-------------------------------------------------|
| GET    | `/login`      | No   | Formulario HTML                                 |
| POST   | `/login`      | No   | Valida y redirige a `/` (302)                   |
| GET    | `/logout`     | Sí   | Limpia sesión, redirige a `/login`              |
| GET    | `/`           | Sí   | Dashboard HTML (KPIs + tablas + gráficos)       |
| GET    | `/api/stats`  | Sí   | JSON con las mismas métricas                    |
| GET    | `/healthz`    | No   | `{"status":"ok"}`                               |

Si no hay sesión:
- En rutas HTML → 302 a `/login`.
- En `/api/stats` → 401.

## Auth

- Login por formulario (no Basic Auth del navegador) + cookie de sesión firmada.
- Validación con `secrets.compare_digest` (no `==`) para evitar timing attacks.
- Cookie: `httponly=True`, `samesite="lax"`, `secure` configurable por env (por defecto `False`, porque el setup típico es HTTP detrás del reverse proxy del DSM con TLS terminado allí).
- Sin "recordarme", sin recuperación de password, sin registro. Un único usuario.
- Logging de intentos fallidos (sin rate-limit; lo cubre el reverse proxy si hace falta).
- Si `DASHBOARD_PASSWORD` no está seteada → **fallar al arrancar** (no opt-out: el login se pidió explícitamente).

## Variables `.env` nuevas

```
DASHBOARD_PORT=8080
DASHBOARD_USER=admin
DASHBOARD_PASSWORD=...           # obligatoria
DASHBOARD_SECRET_KEY=...         # firma de cookie (generar aleatoria)
DASHBOARD_COOKIE_SECURE=false    # true si la app sirve directamente HTTPS
```

## Métricas a mostrar (las mismas que hoy en Grafana)

Derivadas todas de `transcodings`:
- Total de vídeos.
- Distribución por `status` (pending / in_progress / completed / not_required / failed).
- % de éxito.
- Distribución por `transcoded_video_codec` (solo `completed`).
- Distribución por `transcoded_video_resolution` (solo `completed`).
- Últimos 5 transcodings.
- Top 5 mensajes de error agrupados (failed + `error_message` no nulo).

Ver `docs/grafana-queries.md` para las queries originales — se traducen a métodos del repositorio.

## Archivos a crear

```
src/
  controllers/
    dashboard_controller.py        # routers FastAPI: dashboard + auth
  application/
    dashboard_stats_use_case.py    # agrega métricas desde el repo
  infrastructure/
    web/
      app.py                       # construye FastAPI app + middleware
      auth.py                      # dependencia de sesión + verify_credentials
      server.py                    # arranca Uvicorn en thread
      templates/
        base.html
        login.html
        dashboard.html
      static/
        style.css
```

## Archivos a modificar

- `src/main.py` → arrancar el servidor web en paralelo al scheduler.
- `src/infrastructure/db/video_repository_sql.py` → métodos de agregación nuevos (o crear `transcoding_stats_repository.py` aparte si se quiere mantener el repo de escritura limpio — decidir al implementar).
- `src/infrastructure/config/config.py` → cargar config nueva del dashboard.
- `requirements.txt` → añadir `fastapi`, `uvicorn[standard]`, `jinja2`, `python-multipart`, `itsdangerous` (este último ya viene transitivo de Starlette para SessionMiddleware).
- `docker-compose.yml` → exponer puerto del dashboard, borrar servicios `grafana` y `grafana-init`, borrar volumen `grafana-data`.
- `env.example` → añadir vars nuevas, quitar las de Grafana.
- `Dockerfile` → revisar si hace falta `EXPOSE`.
- `README.md` → sección de monitoring reescrita.

## Archivos a borrar

- `docker-compose-without-grafana.yml` (ya no hace falta la variante).
- `docs/grafana-setup.md`
- `docs/grafana-queries.md`
- `docs/grafana-dashboard.json`
- `docs/images/grafana_database.png`, `docs/images/full_grafana_dashboard.png` (verificar que no se referencian desde otros sitios).
- Carpeta `./grafana-data` (en runtime de los usuarios; añadir nota de migración al README).

## Tests

- `tests/` ya existe — añadir:
  - Tests del use case de stats (con repo en memoria / fixture SQLite).
  - Tests del controller con `httpx.AsyncClient` o `TestClient` de FastAPI: login OK / login KO / acceso sin sesión → 302 / 401 / `/api/stats` con sesión.
- Respetar `test-discipline` skill: tests estrictos, sin `mock.ANY`, sin `pytest.skip`.

## Tradeoffs aceptados

- Se pierde el ad-hoc querying de Grafana. Aceptable: dataset acotado.
- Se pierden alertas de Grafana. No se usaban.
- Para añadir un panel hay que tocar código en vez de arrastrar widgets. Aceptable a este alcance.

## Estado / próximos pasos

- [ ] Confirmar nombres de archivos y carpetas (¿`infrastructure/web/` o `controllers/web/`?).
- [ ] Decidir si separar `transcoding_stats_repository.py` del repo de escritura.
- [ ] Implementar en una rama (`feat/replace-grafana-with-dashboard`).
- [ ] Probar en local con `docker-compose.yml` actualizado antes de borrar nada de Grafana.
- [ ] Migrar README y docs.
- [ ] PR.

## Notas sueltas

- El reverse proxy del DSM (Control Panel → Login Portal → Advanced → Reverse Proxy) sigue siendo la capa de TLS. La auth de la app es la segunda barrera para que nadie en la LAN entre solo con la IP.
- Considerar añadir `X-Frame-Options: DENY` y `Content-Security-Policy` básicas en respuestas HTML.
- Generación del `DASHBOARD_SECRET_KEY`: documentar `python -c "import secrets; print(secrets.token_urlsafe(32))"` en el README.
