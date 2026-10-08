# LLMForge Frontend

Standalone React + TypeScript + Vite dashboard for the LLMForge experiment results.
It is a static site: no backend, no API calls. Every value is the recorded data from RESULTS.md (see `src/data.ts` and `src/pages.tsx`).

## Theme rules

- Black canvas, neutral chrome.
- **White = OpenAI**, **orange = Anthropic**, in every chart, table and legend.
- Solid fill = current / new version. Hatched fill = before / old version (cache before, V1, GPT-5.6).
- A check mark in a filled circle marks the better side of every row in the comparison tables.

## Run

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Sections also have shareable links: `#baseline`, `#cache`, `#concurrency`, `#models`, `#prompt`.

## Build and deploy

```bash
npm run build
```

Upload the `dist/` folder to any static host (Netlify, Vercel, GitHub Pages, S3). Asset paths are relative, so it also works from a sub-folder. Fonts are bundled, so nothing loads from a CDN.

## Where things live

- `src/data.ts` – chart data
- `src/pages.tsx` – the six pages and their table rows (set `better: "lower" | "higher"` per row to change what counts as a win)
- `src/ui.tsx` – shared components: comparison table, scoreboard, percentile dumbbell, latency race, savings bars
- `src/styles.css` – theme tokens at the top (`--orange`, `--white`, ...)
