# Apresentação

## 1. Problema

Processos massificados de não reconhecimento de contratação exigem análise documental repetitiva, custosa e pouco padronizada. Isso aumenta o tempo de resposta, reduz a consistência estratégica e dificulta auditoria.

## 2. Solução

A plataforma recebe autos e subsídios, estrutura o caso, aplica a política de acordos V5 e entrega ao advogado:

- leitura resumida do caso;
- red flags e inconsistências;
- recomendação de defesa ou acordo;
- faixa sugerida de valor;
- trilha explicável com regras aplicadas.

## 3. Fluxo da Demo

1. Upload dos PDFs do caso.
2. Extração estruturada e análise dos subsídios.
3. Recomendação jurídica no painel do advogado.
4. Registro do outcome.
5. Consolidação no dashboard do banco.

## 4. Diferenciais

- política auditável e versionada;
- recomendação explicável, não caixa-preta;
- separação entre interface, API e política;
- uso combinado de regras, histórico e LLM.

## 5. Stack

- `src/web`: Next.js, TypeScript, Tailwind, shadcn/ui
- `src/api`: FastAPI, SQLAlchemy, Pydantic
- `src/policy/`: regras e matrizes da política
- `data/`: base histórica, banco local e documentos cadastrados

## 6. Materiais Relacionados

- visão geral: `README.md`
- execução local: `SETUP.md`
- planejamento: `docs/TEAM.md`
- slides navegáveis: `docs/slides/`
