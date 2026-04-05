# Plan migracji: Streamlit → LangServe + Vite/React

## Struktura repo po zmianach

```
chess-analysis-agent/
├── agent/                  ← bez zmian
├── frontend/               ← NOWE (Vite + React)
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── BoardPanel.tsx
│   │   │   ├── AnalysisPanel.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── server.py               ← NOWE (FastAPI + LangServe)
├── app.py                  ← zostaje lub usuwamy (Streamlit)
└── pyproject.toml          ← dodajemy langserve, fastapi, uvicorn
```

---

## ✅ Krok 1 — Backend: `server.py` z LangServe

- ✅ Dodać `langserve`, `fastapi`, `uvicorn` do `pyproject.toml`
- ✅ Stworzyć `server.py`:
  - ✅ `FastAPI` app z CORS (potrzebne dla przeglądarki)
  - ✅ `add_routes(app, graph, path="/analyze")` → automatycznie `/analyze/invoke`, `/analyze/stream`
- ✅ Dodać skrypt `serve` do `[tool.uv.scripts]` (`uv run serve`)

## ✅ Krok 2 — Frontend: Vite + React

- ✅ `npm create vite@latest frontend -- --template react-ts`
- ✅ Dodać zależności:
  - ✅ `react-chessboard` — interaktywna szachownica
  - ✅ `chess.js` — manipulacja pozycją po stronie frontendu
- ✅ Skonfigurować proxy w `vite.config.ts` → `/analyze` → `localhost:8000`

## ✅ Krok 3 — Komponenty React

- ✅ **`BoardPanel`** — szachownica (320px), input FEN, slider depth, przyciski tury, przeciąganie figur
- ✅ **`AnalysisPanel`** — material, Stockfish eval, taktyki
- ✅ Integracja z LangServe przez `fetch /analyze/invoke`

## ✅ Krok 4 — Uruchamianie dev

```bash
# terminal 1
uv run serve

# terminal 2
cd frontend && npm run dev
```

## Krok 5 — Sprzątanie

- Usunąć `streamlit` z `pyproject.toml`
- Usunąć `app.py` i `agent/run.py` (lub zostawić jako fallback)

---

## Krok 6 — Aktualizacja dokumentacji

- Zaktualizować `README.md`:
  - Nowe instrukcje uruchamiania (`uv run serve` + `npm run dev`)
  - Usunąć wzmianki o Streamlit
  - Dodać opis struktury repo (monorepo Python + frontend)
  - Zaktualizować sekcję zależności (Node.js jako nowy wymóg)

---

## Kolejność pracy

~~Krok 1~~ ✅ → ~~Krok 2~~ ✅ → ~~Krok 3~~ ✅ → ~~weryfikacja~~ ✅ → Krok 5 → 6
