# Production Deploy

Target domain: `dnatext.ru`

Target server: `217.114.5.4`

## DNS

Create or update DNS records at reg.ru:

```text
@     A     217.114.5.4
www   A     217.114.5.4
```

Wait until DNS resolves to the server before expecting HTTPS to issue.

## First Server Setup

```bash
ssh root@217.114.5.4
bash <(curl -fsSL https://raw.githubusercontent.com/xahinvest-DNA/Lex-Chess/main/deploy/server-bootstrap.sh)
```

Then edit secrets on the server:

```bash
cd /opt/lex-chess
nano deploy/bot.env
nano deploy/site.env
```

Start services:

```bash
docker compose up -d --build
docker compose ps
```

## Updates

```bash
cd /opt/lex-chess
bash deploy/deploy.sh
```

## Logs

```bash
docker compose logs -f web
docker compose logs -f bot
docker compose logs -f caddy
```
