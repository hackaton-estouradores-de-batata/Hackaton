# Skeleton Alignment Check

## Objetivo

Verificar se o estado atual do repositorio esta coerente com o `PROJECT_SKELETON.md`, com foco em estrutura, arquitetura e entregas da Sprint 0 ja presentes nesta branch.

## Alinhado

- O projeto usa a raiz do repositorio como base da arvore principal, coerente com o skeleton.
- As pastas-raiz previstas no skeleton existem: `src/`, `data/`, `docs/`, `policy/`, `scripts/`.
- Os diretorios locais esperados para os dados de exemplo e para o frontend tambem foram preparados:
  - `data/subsidios/`
  - `data/processos_exemplo/caso_001/autos/`
  - `data/processos_exemplo/caso_001/subsidios/`
  - `data/processos_exemplo/caso_002/autos/`
  - `data/processos_exemplo/caso_002/subsidios/`
  - `src/web/`
- A frente P2 da Sprint 0 agora esta nos caminhos corretos da raiz:
  - `scripts/convert_sentencas_xlsx_to_csv.py`
  - `data/sentencas_60k.csv`
  - `data/processos_exemplo/caso_001/mock_case.json`
  - `data/processos_exemplo/caso_002/mock_case.json`
  - `docs/p2_sprint0_verification.md`
- O `README.md` foi ajustado para referenciar `src/web` e `src/api`, em linha com o skeleton.
- O `README.md` nao aponta mais para caminhos absolutos quebrados de outra maquina.

## Limpeza realizada

- Remocao da pasta paralela `hackathon-ufmg-2026/`, que estava fora da arvore principal do projeto.
- Remocao dos arquivos `implementation_plan.md` e `project_analysis.md`, que eram artefatos de trabalho e nao faziam parte do skeleton.
- Remocao da pasta vazia `data/mocks`, que nao fazia parte da estrutura planejada.

## Pendencias fora da frente P2

Os itens abaixo ainda nao estao presentes nesta branch, mas pertencem a outras frentes do Sprint 0 ou a etapas seguintes do skeleton:

- `SETUP.md`
- `.env.example`
- `.gitignore`
- conteudo do frontend em `src/web/`

Essas ausencias nao bloqueiam a entrega da Sprint 0 da P2, mas impedem dizer que o repositorio inteiro ja esta completo em relacao ao skeleton final.

## Conclusao

- P2 Sprint 0: alinhada com o skeleton e pronta para merge.
- Repositorio completo: parcialmente alinhado, aguardando a uniao dos commits das outras frentes do Sprint 0.
