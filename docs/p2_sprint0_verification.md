# P2 Sprint 0 Verification

## Scope

- Sprint: `Sprint 0 - P2`
- Goal 1: convert the historical base to `data/sentencas_60k.csv`
- Goal 2: deliver 2 hardcoded mock cases for `caso_001` and `caso_002`
- Constraint respected: no changes were made under `src/api` or `src/web`

## Generated files

- `scripts/convert_sentencas_xlsx_to_csv.py`
- `data/sentencas_60k.csv`
- `data/processos_exemplo/caso_001/mock_case.json`
- `data/processos_exemplo/caso_002/mock_case.json`
- `docs/p2_sprint0_verification.md`

## CSV validation

- Source workbook: `arquivos_adicionais/Hackaton_Enter_Base_Candidatos.xlsx`
- Exported sheet: `Resultados dos processos`
- Output file: `data/sentencas_60k.csv`
- Header columns: 8
- Total lines in CSV: 60001
- Data rows in CSV: 60000

### Preserved header

1. `Numero do processo`
2. `UF`
3. `Assunto`
4. `Sub-assunto`
5. `Resultado macro`
6. `Resultado micro`
7. `Valor da causa`
8. `Valor da condenacao/indenizacao`

Note: the CSV itself preserves the original workbook header spelling. The list above is written in ASCII only for this verification document.

## Mock validation

- `data/processos_exemplo/caso_001/mock_case.json`
  - top-level fields present: `id`, `numero_processo`, `valor_causa`, `autor_nome`, `status`, `pedidos`, `alegacoes`, `subsidios`, `recommendation`
  - recommendation decision: `defesa`
- `data/processos_exemplo/caso_002/mock_case.json`
  - top-level fields present: `id`, `numero_processo`, `valor_causa`, `autor_nome`, `status`, `pedidos`, `alegacoes`, `subsidios`, `recommendation`
  - recommendation decision: `acordo`

## Sprint 0 checklist

- [x] Create the minimum P2 folder structure inside the project root
- [x] Add `scripts/convert_sentencas_xlsx_to_csv.py`
- [x] Run the conversion and generate `data/sentencas_60k.csv`
- [x] Create `mock_case.json` for `caso_001`
- [x] Create `mock_case.json` for `caso_002`
- [x] Validate CSV line count and column count
- [x] Validate the mock recommendation for `caso_001` is `defesa`
- [x] Validate the mock recommendation for `caso_002` is `acordo`

## Status

- Sprint 0 P2: `done`
- Blocking issues: `none`
