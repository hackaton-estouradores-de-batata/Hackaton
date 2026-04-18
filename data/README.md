# Dados

## Conteudo versionado

- `sentencas_60k.csv`: base historica convertida para analise.
- `processos_exemplo/caso_001/` e `processos_exemplo/caso_002/`: fixtures legados versionados para referencia e smoke tests.

## Conteudo gerado em runtime

- `app.db`: banco SQLite local do backend.
- `processos_cadastrados/case_*/`: casos ingeridos pela rota `POST /api/cases`.

Esses artefatos de runtime nao devem ser versionados.
