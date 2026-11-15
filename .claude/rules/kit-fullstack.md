<!-- kit: fullstack | version: 21882d784db3 | with: impeccable -->
# Full-stack project rules (kit: fullstack)

## Stack defaults
- Backend: Python + FastAPI, PostgreSQL, Redis when caching/queues are needed, Docker for services.
- Frontend: decide per project; explain the choice. Don't add a framework or library
  just because it is popular: say what problem it solves, whether I could build the
  concept myself first, and whether to adopt it now or later.
- Ask before adding any new dependency.

## Design workflow (every new UI or redesign) - no generic UI
1. Brief first. Before any UI code, agree a short brief with me: who it's for,
   the mood (3 adjectives), 1-2 reference sites or brands, light/dark, density.
2. Design system. Either:
   - pick 1-2 references from Awesome Design MD (list:
     https://github.com/VoltAgent/awesome-design-md/tree/main/design-md, file:
     https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/<name>/DESIGN.md),
   - or generate one with the ui-ux-pro-max skill for the product type.
   Then write the project's OWN DESIGN.md (colors, type, spacing, radius, motion,
   component rules). Adapt references; never copy a brand's identity, logo, or
   exact palette for something I'll publish.
3. Build with frontend-design, following DESIGN.md. Use design tokens (CSS
   variables / Tailwind theme), not one-off values. Avoid default fonts
   (Inter, Roboto, Arial) unless DESIGN.md chooses them on purpose.
4. Critique and polish. If the optional Impeccable plugin is installed, run
   `/impeccable critique`, then `/impeccable polish` (also: typeset, colorize,
   layout, bolder, quieter, animate, harden, audit). Without it, critique the
   screenshots from step 7 against DESIGN.md yourself (hierarchy, spacing,
   contrast, type, states) and list the fixes. Fix what is flagged before
   calling the UI done.
5. Motion (when the brief asks for animation, scroll effects, transitions, or "wow"):
   use the cast skill AFTER the static design follows DESIGN.md. It proposes an
   interaction thesis first; agree it with me before code. Typical stack: GSAP +
   ScrollTrigger, Lenis smooth scroll, Framer Motion in React, Three.js / React
   Three Fiber only where 3D earns its place. Always respect prefers-reduced-motion
   and keep pages fast (compressed assets, lazy-loaded heavy scenes). Ask me for
   real assets (images, illustrations, Lottie/Rive, Spline scenes) instead of
   faking them with gradients. Build one section at a time and check each with
   Playwright screenshots or a short recording. When the motion is in, run the
   review-animations skill and fix what it flags.
6. Visuals that explain (landing-page hero, how-it-works section, README figure):
   consider the anatomy skill for an interactive isometric illustration, or
   diagram-design for clean flat diagrams. Use sparingly; one strong figure beats many.
7. Look at it. Use Playwright CLI (`playwright-cli --help` for commands) to
   open the page, take screenshots at desktop and mobile widths, and click
   through the main flows. Show me the screenshots. Use Chrome DevTools for
   console errors, failed network requests, and performance.
Before calling a screen done:
- Screens that show data (tables, lists, cards, dashboards, forms): run the
  break-ui skill with worst-case data and fix what breaks.
- Anything people will use on a phone: run the mobile-native checks.
Skip steps 1-2, 5 and 6 for tiny UI tweaks that follow an existing DESIGN.md.

## Large codebases (optional graphify)
- If this project has graphify (.claude/skills/graphify exists), query the graph
  (`graphify query`, `graphify explain`, `graphify path`) before broad grep/read
  sweeps, and run `graphify update .` after big changes or a git pull.
- If it doesn't, and the codebase is big (roughly 100+ source files) or you keep
  spending turns finding where things live, suggest once:
  `python3 ~/.claude/kits/kit.py update fullstack --with graphify`.
- Run graphify on code folders; analysing docs, PDFs or images uses model tokens.

## Project structure
- Keep a README.md with: what it does, how to run it locally, env variables (names only).
- Keep .env.example in sync with every env variable the code reads.
- Docker: provide docker-compose.yml for local services (db, redis) once there is more than one.

## Working style
- Plan first for anything bigger than a small fix: list files to touch and how to verify.
- Write or update tests with each feature (pytest for Python). Run them before saying done.
  Delegate test writing to the test-writer agent after a feature or bug fix.
- After edits, check the language server diagnostics (pyright / TypeScript) and fix
  new type errors before moving on.
- Use the code-reviewer agent before commits; security-auditor for auth, payments,
  uploads, webhooks, and before deploys.

## Git (gh CLI)
- Small commits with clear messages (feat:, fix:, refactor:, docs:, test:).
- Never commit to main directly once a project is on GitHub; use a branch + PR via gh.

## Hosting on Netlify (uses the claude.ai Netlify connector)
- Keep build settings in netlify.toml in the repo (build command, publish dir,
  redirects, headers), not only in the dashboard.
- Deploy a preview (draft) deploy first and give me the preview URL. Deploy to
  production only after I say so.
- Environment variables live in Netlify (dashboard, CLI, or connector), never in git.
  Keep .env.example in sync with the names.
- Before a production deploy: build passes locally, no console errors on the
  preview (check with Chrome DevTools).
- Never commit Netlify CLI config files or personal access tokens.
