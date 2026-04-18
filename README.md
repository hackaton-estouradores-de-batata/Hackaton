# Hackathon UFMG 2026

Política de acordos automatizada para o Banco UFMG em casos de nao reconhecimento de contratacao de emprestimo.

## Visao Geral

Este projeto propoe uma plataforma web para apoiar a tomada de decisao juridica em processos nos quais o cliente alega nao reconhecer a contratacao de um emprestimo. A solucao recebe os autos e os subsidios do banco, estrutura os dados do caso com apoio de LLM, aplica uma politica de acordos baseada em regras juridicas e sinais de robustez documental, e devolve ao advogado uma recomendacao objetiva:

- seguir com defesa;
- oferecer acordo;
- sugerir faixa de valor;
- registrar justificativa e rastreabilidade da decisao.

O objetivo e transformar uma analise hoje manual, lenta e heterogenea em um fluxo auditavel, escalavel e orientado por dados.

## Acesso Rapido

- Execucao local: [SETUP.md](SETUP.md)
- Arquitetura atual: [docs/architecture.md](docs/architecture.md)
- Guia detalhado: [docs/guides/PROJECT_SKELETON.md](docs/guides/PROJECT_SKELETON.md)
- Planejamento: [docs/guides/TEAM.md](docs/guides/TEAM.md)
- Video demo: [docs/demo_video.mp4](docs/demo_video.mp4)
- Slides: [docs/slides/README.md](docs/slides/README.md)

## Problema

Em litigios massificados, o custo de analisar cada processo em profundidade e alto. Isso gera:

- gasto excessivo com defesa e condenacoes;
- dificuldade de padronizar estrategia juridica;
- baixa rastreabilidade sobre por que um acordo foi ou nao foi oferecido;
- perda de eficiencia operacional para bancos e escritorios parceiros.

## Solucao Proposta

A plataforma atua como uma camada de triagem e recomendacao juridica. Ela combina:

- extracao estruturada de informacoes dos autos e subsidios;
- politica de acordos versionada e separada do codigo;
- motor de decisao com regras e score de robustez;
- estimativa de valor sugerido com base em historico e contexto do caso;
- dashboard para monitorar aderencia e efetividade.

## Fluxo End-to-End

```text
[Advogado] -> upload/visualiza processo -> [Backend]
    |
    v
[Pipeline de Analise]
  1. Ingestao de PDFs (autos + subsidios)
  2. Extracao estruturada (LLM) -> JSON normalizado
  3. Motor de Decisao (regras + score) -> acordo ou defesa
  4. Calculadora de Valor (historico + LLM) -> faixa sugerida
    |
    v
[Recomendacao] -> advogado decide -> registra outcome
    |
    v
[Dashboard Banco] -> aderencia + efetividade
```

## Como a Plataforma Decide

O nucleo do projeto e a politica de acordos. A ideia central e separar a regra juridica da implementacao tecnica para permitir revisao rapida pelo time de negocio e juridico.

Exemplos de sinais relevantes:

- existencia de contrato;
- comprovante de credito;
- dossier documental;
- validacao de assinatura;
- canal de contratacao;
- robustez geral dos subsidios.

Com isso, o sistema pode classificar casos com perfil de:

- defesa forte, quando a documentacao sustenta a tese do banco;
- acordo prioritario, quando ha fragilidade probatoria ou alto risco de condenacao;
- zona cinzenta, quando a recomendacao depende de score, contexto e historico.

## Arquitetura Atual

### Frontend

- Next.js 16
- TypeScript
- Tailwind CSS
- shadcn/ui

Interfaces previstas:

- inbox do advogado para triagem de casos;
- tela detalhada do caso com recomendacao e justificativa;
- dashboard do banco com metricas operacionais e juridicas.

### Backend

- FastAPI
- Python
- SQLAlchemy
- Pydantic

Responsabilidades principais:

- ingestao dos arquivos;
- extracao estruturada via LLM;
- aplicacao da politica;
- geracao da recomendacao;
- persistencia de casos, recomendacoes e outcomes;
- exposicao de APIs REST.

### IA e Analiticos

- OpenAI para extracao e decisao assistida;
- Pandas + DuckDB para explorar historico de sentencas;
- motor hibrido de regras + score + LLM.

### Dados e Persistencia

- SQLite no desenvolvimento;
- Postgres em producao;
- armazenamento local de arquivos no MVP;
- possibilidade de evolucao para S3-compatible.

## Estrutura Atual do Projeto

```text
hackathon-ufmg-2026-grupoN/
├── README.md
├── SETUP.md
├── .env.example
├── src/
│   ├── web/
│   ├── api/
│   ├── policy/
│   └── scripts/
├── data/
├── docs/
│   ├── architecture.md
│   ├── demo_video.mp4
│   ├── guides/
│   └── slides/
```

Organizacao conceitual:

- `src/web`: experiencia do advogado e dashboard do banco;
- `src/api`: pipeline, regras, servicos e APIs;
- `src/policy/`: politica versionada de acordos;
- `data/`: banco local, documentos cadastrados e base historica;
- `docs/`: arquitetura, video demo, guias e apresentacao;
- `docs/slides/`: app isolada da apresentacao;
- `src/scripts/`: seed, analise historica e avaliacao da politica.

## Modelo de Dominio

As entidades centrais da solucao sao:

- `Case`: representa o processo judicial analisado;
- `Subsidios`: consolida a robustez documental da defesa;
- `Recommendation`: registra a recomendacao gerada pelo pipeline;
- `Outcome`: captura a decisao final do advogado e o desfecho do caso.

Esse desenho permite rastrear:

- o que entrou no sistema;
- quais regras foram aplicadas;
- qual recomendacao foi emitida;
- se o advogado seguiu a sugestao;
- qual foi o resultado final.

## Diferenciais da Solucao

- politica auditavel e editavel sem alterar codigo;
- recomendacao explicavel, nao apenas um output opaco de IA;
- apoio direto ao advogado, sem retirar a decisao humana;
- uso de historico para calibrar risco e faixa de acordo;
- monitoramento de aderencia e efetividade ao longo do tempo.

## Casos de Uso

### 1. Triagem juridica

O advogado recebe o caso ja estruturado, com leitura acelerada dos principais fatos, pedidos e subsidios.

### 2. Recomendacao de estrategia

O sistema sugere se vale defender ou propor acordo, com justificativa baseada em regras e sinais do caso.

### 3. Sugestao de valor

Quando houver acordo, a plataforma sugere uma faixa de valor coerente com o historico e com a robustez da defesa.

### 4. Aprendizado operacional

O banco acompanha metricas de aderencia a recomendacao, taxa de acordo, efetividade e impacto economico.

## Status do Repositorio

No estado atual, este repositorio contem um MVP funcional com:

- `src/web/`: inbox do advogado, tela de caso e dashboard do banco
- `src/api/`: ingestao, recomendacao, outcomes e analytics
- `src/policy/`: politica e materiais correlatos
- `src/scripts/analyze_historical.py`
- `src/scripts/build_embeddings.py`
- `src/scripts/eval_policy.py`
- `data/sentencas_60k.csv`
- `docs/architecture.md`
- `docs/demo_video.mp4`
- `docs/slides/`
- `docs/guides/`

A estrutura acima representa o estado atual do projeto e os materiais de entrega já organizados.

## Proximos Passos

1. Consolidar a documentacao em `docs/architecture.md` e `docs/guides/`.
2. Evoluir a politica e o backtest economico da V5.
3. Refinar analytics e cortes financeiros do dashboard.
4. Preparar a transicao de SQLite/local storage para stack de producao.

## Referencia

Este README resume o estado atual do MVP. Para detalhes tecnicos e de execucao, use `SETUP.md`, `docs/architecture.md` e os arquivos em `docs/guides/`.
