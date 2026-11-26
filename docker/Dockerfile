FROM node:22-bookworm-slim AS frontend-build
WORKDIR /frontend
COPY frontend/ ./
RUN npm install --no-audit --no-fund && npm run build

# Runtime versions match the trusted CI environment.
FROM golang:1.27.3 AS gno-build
RUN git clone --depth 1 --branch v1.8.0 https://github.com/gnolang/gno.git /opt/gno \
 && cd /opt/gno && test "$(git rev-parse HEAD)" = fc79041f4cd1a7b3ed4b316dc5ac14162eb78730 \
 && CGO_ENABLED=0 go build -o /usr/local/bin/gno ./gnovm/cmd/gno
COPY tools/sourceparser/main.go /tmp/sourceparser.go
RUN CGO_ENABLED=0 go build -o /usr/local/bin/realmproof-source-parser /tmp/sourceparser.go

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV GNOROOT=/opt/gno
COPY --from=gno-build /opt/gno /opt/gno
COPY --from=gno-build /usr/local/bin/gno /usr/local/bin/gno
COPY --from=gno-build /usr/local/bin/realmproof-source-parser /usr/local/bin/realmproof-source-parser
WORKDIR /app
RUN useradd --create-home --uid 10001 app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=frontend-build /studio/static/studio/react/ studio/static/studio/react/
RUN DJANGO_SECRET_KEY=build-only-not-for-runtime DATABASE_URL=postgresql://build:build@localhost:5432/build python manage.py collectstatic --noinput
USER app
EXPOSE 8000
CMD ["gunicorn", "realmproof.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
