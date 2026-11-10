# Frontend

React 18, Amplify JS v6/UI, React Router and Plaid Link, built as a static SPA with Vite 8. Use Node 24 LTS (`nvm use`). No Amplify CLI initialization is required.

```sh
npm ci
cp .env.example .env.local
# Fill .env.local with public stack outputs, or run the export helper from the repo root.
npm start
```

Open `http://localhost:3000`. `npm run build` emits `dist/`; `npm run preview` previews it. `npm test` runs offline configuration checks. Missing configuration produces a visible setup message. All `VITE_` variables are public: never include Plaid or AWS secrets.

Amplify Hosting uses the SAM template's monorepo build specification (`appRoot: frontend`, Node 24, `dist/`). `frontend/amplify.yml` documents the same settings. See the root [README](../README.md) for infrastructure deployment, OAuth and the Sandbox acceptance check.
