# Deploy Ascension to rastacamp.com

## GitHub (source of truth)

Latest code is on **`main`** at:

https://github.com/RastaCamp/ascension-cards

Your friend (or you) should pull that repo and deploy the **repo root** static files:

- `index.html`
- `cards/`
- `audio/`

Do **not** deploy the `android/` folder to the website.

## Live sites today

| URL | Status |
|-----|--------|
| `ascension.rastacamp.com` | Old build (keyboard shortcuts still in help) — likely your friend’s Cloudflare account |
| `ascensions.rastacamp.com` | **Not in DNS yet** — use this for your deploy |

## Cloudflare Pages (recommended)

1. Create an API token: [Cloudflare API tokens](https://dash.cloudflare.com/profile/api-tokens)  
   - Template: **Edit Cloudflare Workers** or custom with **Account → Cloudflare Pages → Edit**
2. Copy `.env.example` → `.env` (never commit `.env`):

   ```
   CLOUDFLARE_API_TOKEN=your_token_here
   CLOUDFLARE_ACCOUNT_ID=0f42c247e489dce80771116c30c57c3e
   ```

3. From this folder:

   ```powershell
   .\Deploy-AscensionSite.ps1
   ```

   First time only, create the project in the dashboard or:

   ```powershell
   npx wrangler pages project create ascensions --production-branch=main
   ```

4. **Custom domain** (dashboard): Pages → project **ascensions** → Custom domains → add `ascensions.rastacamp.com`

5. **DNS** (zone `rastacamp.com`): add a CNAME record when Cloudflare prompts you (usually `ascensions` → `<project>.pages.dev`).

## GitHub Actions (optional)

Repo secrets on `RastaCamp/ascension-cards`:

- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID` = `0f42c247e489dce80771116c30c57c3e`

Push to `main` runs `.github/workflows/deploy-pages.yml`.

## Tell your friend

If they host `ascension.rastacamp.com` on **their** Cloudflare account, you cannot overwrite it from yours. They should:

```bash
git clone https://github.com/RastaCamp/ascension-cards.git
cd ascension-cards
# deploy index.html + cards/ + audio/ to their existing Pages project
```

Or you use **`ascensions.rastacamp.com`** on your account (no conflict).
