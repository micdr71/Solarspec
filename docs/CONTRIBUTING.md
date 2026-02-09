# Contribuire a SolarSpec

Grazie per l'interesse a contribuire! 🎉

## Come iniziare

1. **Fork** il repository
2. **Clona** il tuo fork: `git clone https://github.com/YOUR_USERNAME/solarspec.git`
3. **Crea un branch**: `git checkout -b feature/la-mia-funzionalita`
4. **Installa le dipendenze di sviluppo**: `pip install -e ".[dev]"`
5. **Scrivi i test** per le tue modifiche
6. **Esegui i test**: `pytest`
7. **Controlla il codice**: `ruff check .`
8. **Commit e push**: `git commit -m "Descrizione" && git push origin feature/la-mia-funzionalita`
9. **Apri una Pull Request**

## Convenzioni

- **Codice**: seguiamo le regole di `ruff` configurate in `pyproject.toml`
- **Docstring**: formato Google style, in inglese
- **Commit**: messaggi descrittivi in italiano o inglese
- **Test**: ogni nuova funzionalità deve avere test in `tests/`
- **Type hints**: obbligatorie per tutte le funzioni pubbliche

## Aree di contributo prioritarie

- 📊 Database completo zone climatiche per comune (ISTAT)
- 📊 Database completo zone sismiche per comune
- ⚡ Catalogo prodotti fotovoltaici aggiornato
- 📐 Template capitolati per diverse tipologie
- 🌐 Integrazione API catasto
- 🧪 Test di integrazione con PVGIS
- 📄 Generazione PDF via WeasyPrint
- 🤖 Layer AI per narrativa tecnica

## Segnalare bug

Apri una Issue con:
- Descrizione del problema
- Passi per riprodurlo
- Output atteso vs. ottenuto
- Versione Python e OS
