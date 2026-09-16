# Web application

React + TypeScript + Leaflet client for exploring spatiotemporal pedestrian collision risk in Metropolitan Lima.

## Run locally

With the API available at `http://localhost:8000`:

```bash
cd apps/web
npm install
npm run dev
```

The API URL defaults to `http://localhost:8000`. Override it with:

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

On Windows, an `apps/web/.env.local` file can be used:

```text
VITE_API_BASE_URL=http://localhost:8000
```

## Main interactions

- select a period;
- explore scores on the map;
- inspect an area;
- compare two areas for the same period.
