# Frontend: Next.js with TypeScript

This Next.js application provides a user interface for uploading transaction
files, communicating with the FastAPI backend, and displaying results.

## Key components

- **Next.js** – React framework with file‑based routing and server rendering.
- **TypeScript** – ensures type safety across the application.
- **Axios** – for making HTTP requests to the FastAPI backend.

## Project structure

```
frontend/
├── package.json           # package configuration
├── tsconfig.json          # TypeScript compiler settings
├── next.config.js         # Next.js configuration
├── pages/                 # File‑based routing
│   ├── _app.tsx           # Custom App component
│   └── index.tsx          # Home page
├── components/            # Reusable React components
│   ├── FileUpload.tsx     # Upload form for CSV/Excel files
│   └── Layout.tsx         # Simple layout wrapper
├── services/              # API client abstractions
│   └── api.ts             # Functions for calling backend endpoints
├── styles/                # Global and modular CSS (Tailwind enabled)
│   ├── globals.css        # includes @tailwind directives
│   └── Home.module.css
└── public/                # Static assets (e.g. favicon)
```

## Development

This project uses pnpm (via Corepack).

- Install deps: `pnpm install`
- Run dev server: `pnpm dev`
- Lint: `pnpm lint`
- Build: `pnpm build`
- Start: `pnpm start`

Ensure the FastAPI backend is running on `localhost:8000` or update the base URL
via the `NEXT_PUBLIC_API_BASE_URL` env or in `services/api.ts` accordingly.