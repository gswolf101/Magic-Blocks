# Wiki do Magic & Blocks

Site estático (HTML/CSS/JS puro, sem build) — funciona no GitHub Pages e também abrindo o `index.html` direto no navegador.

## Publicar no GitHub Pages

**Opção 1 — repositório do mod inteiro (recomendado):** o workflow `.github/workflows/pages.yml` já publica esta pasta `site`.
1. Envie o projeto para o GitHub (branch `main`).
2. No repositório: **Settings → Pages → Source: GitHub Actions**.
3. A cada push que mexer em `site/`, o site é publicado em `https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/`.

**Opção 2 — repositório só do site:** envie o conteúdo desta pasta (com o `index.html` na raiz) e em
**Settings → Pages → Source: Deploy from a branch → main / (root)**.

## Atualizar o conteúdo

As páginas e os ícones são gerados a partir das receitas e texturas do mod:

```
python gerar_wiki.py
```

Os textos de cada item ficam no próprio `gerar_wiki.py` (listas `RECURSOS`, `BLOCOS`, `MAGICOS`, `ARMAS`).
Precisa do Python com Pillow e de o mod ter sido compilado uma vez (o ForgeGradle baixa as texturas do Minecraft).