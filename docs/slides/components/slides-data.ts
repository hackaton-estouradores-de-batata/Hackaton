export type Slide =
  | {
      id: string
      type: "cover"
      title: string
      subtitle: string
      tagline: string
      team?: string
    }
  | {
      id: string
      type?: "default"
      eyebrow: string
      title: string
      lead: string
      bullets: string[]
      footer?: string
      status?: "entregue" | "misto" | "visao"
    }

export const slides: Slide[] = [
  {
    id: "cover",
    type: "cover",
    title: "EnterOS para o Banco UFMG",
    subtitle: "Política de Acordos Assistida por IA",
    tagline: "Hackathon UFMG 2026 · Enter AI Challenge",
    team: "17–18 de Abril de 2026",
  },
  {
    id: "problema",
    eyebrow: "01 · Problema",
    title: "Como orientar um advogado diante de 5.000 casos para analisar?",
    lead: "No contencioso massificado, o problema não é só jurídico: é operacional. Com milhares de processos na fila, o advogado precisa de direcionamento rápido para saber onde aprofundar, onde defender e onde considerar acordo.",
    bullets: [
      "Ler autos e subsídios manualmente em milhares de casos consome tempo demais e reduz a capacidade de resposta.",
      "Sem triagem inteligente, casos urgentes e de maior risco disputam a mesma atenção limitada.",
      "A decisão entre defender ou acordar varia muito entre advogados mesmo em situações parecidas.",
      "Quando há 5.000 casos para analisar, a dor principal é falta de orientação e priorização.",
    ],
    footer: "Ponto de partida: transformar volume jurídico em fila priorizada, com orientação objetiva e rastreável para o advogado.",
    status: "misto",
  },
  {
    id: "politica",
    eyebrow: "02 · Política de Acordos",
    title: "A política de acordos traduz experiência jurídica em orientação prática.",
    lead: "Em linguagem simples: o sistema analisa a robustez documental, os sinais do caso e a política definida pelo jurídico para recomendar quando vale defender e quando faz mais sentido acordar.",
    bullets: [
      "Defesa documental forte → recomendação de defesa.",
      "Fragilidade probatória ou maior risco jurídico → recomendação de acordo.",
      "Quando a recomendação é acordo, o sistema sugere uma faixa de valor coerente com o caso.",
      "A decisão vem com justificativa e rastreabilidade para facilitar revisão pelo time jurídico.",
    ],
    footer: "Para o jurídico, o ponto central é: a política vira critério consistente de decisão, não opinião isolada caso a caso.",
    status: "misto",
  },
  {
    id: "solucao",
    eyebrow: "03 · Solução",
    title: "Uma política de acordos assistida por IA, com núcleo auditável.",
    lead: "A plataforma recebe os documentos do caso, estrutura os dados com apoio de LLM e entrega ao advogado uma recomendação objetiva com justificativa e rastreabilidade.",
    bullets: [
      "Entrada: autos + subsídios do banco.",
      "Saída: defesa ou acordo, faixa de valor sugerida, nível de confiança e justificativa.",
      "A IA apoia extração, revisão e explicação — sem virar caixa-preta decisória.",
      "O advogado continua no centro da decisão e o sistema registra o outcome final.",
    ],
    footer: "Mensagem-chave: LLM nas pontas, política e estatística no centro.",
    status: "misto",
  },
  {
    id: "financeiro",
    eyebrow: "04 · Potencial Financeiro",
    title: "O potencial financeiro está em decidir melhor e mais cedo, em escala.",
    lead: "Com base em 60.000 sentenças históricas do Banco UFMG, a lógica econômica é clara: reduzir custo de análise, diminuir decisões inconsistentes e capturar acordos mais eficientes antes que o caso escale.",
    bullets: [
      "Menos tempo gasto pelo advogado em triagem manual de milhares de processos.",
      "Mais consistência para evitar defesa cara em casos com baixa sustentação documental.",
      "Melhor orientação para capturar acordos em faixas mais estratégicas e sustentáveis.",
      "Base para medir aderência, efetividade e impacto econômico ao longo do tempo.",
    ],
    footer: "Tese financeira: orientar melhor a carteira jurídica reduz desperdício operacional e melhora a estratégia econômica dos casos.",
    status: "misto",
  },
  {
    id: "fluxo",
    eyebrow: "05 · Fluxo do Produto",
    title: "Do PDF à recomendação em um ciclo completo.",
    lead: "O valor do projeto não está só em sugerir uma estratégia, mas em fechar o ciclo operacional com decisão humana e métricas.",
    bullets: [
      "Upload dos PDFs do caso (autos e subsídios).",
      "Extração estruturada do conteúdo jurídico e documental via LLM.",
      "Análise de sinais do caso e aplicação do motor de decisão.",
      "Geração da recomendação com justificativa e rastreabilidade.",
      "Registro do outcome do advogado e alimentação do dashboard de monitoramento.",
    ],
    footer: "Fluxo end-to-end: documentos → recomendação → outcome → monitoramento.",
    status: "entregue",
  },
  {
    id: "ux",
    eyebrow: "06 · Experiência do Advogado",
    title: "A experiência do advogado foi pensada para orientar, priorizar e acelerar a decisão.",
    lead: "Em vez de começar do zero em cada processo, o advogado recebe uma visão estruturada do caso, com recomendação objetiva, justificativa e espaço para registrar a decisão final.",
    bullets: [
      "Entrada simples: upload de documentos e dados principais do caso.",
      "Visualização com recomendação já pronta para leitura rápida.",
      "Justificativa e trace para apoiar revisão jurídica com mais segurança.",
      "Registro do outcome para transformar uso em aprendizado operacional.",
    ],
    footer: "A experiência foi desenhada para reduzir atrito na análise e aumentar clareza em ambientes de alto volume.",
    status: "misto",
  },
  {
    id: "ia",
    eyebrow: "07 · Arquitetura Técnica",
    title: "IA como apoio inteligente, não como decisão opaca.",
    lead: "A arquitetura combina extração com LLM, política explícita e versionada, explicação baseada em trace e uma camada de revisão para aumentar confiança e explicabilidade.",
    bullets: [
      "LLM para extração estruturada de autos, subsídios e features relevantes.",
      "Motor de decisão híbrido com política versionada e recomendação orientada por trace.",
      "LLM-as-judge para revisar a recomendação e gerar justificativa auditável.",
      "Camada conversacional sobre os dados do caso para consultas estratégicas.",
    ],
    footer: "Diferencial técnico: usar IA onde ela é forte e manter o núcleo decisório verificável.",
    status: "entregue",
  },
  {
    id: "entregue",
    eyebrow: "08 · MVP Funcional",
    title: "O que já foi entregue no repositório atual.",
    lead: "A base funcional do fluxo jurídico já existe no backend e sustenta uma narrativa real de MVP, não apenas de intenção arquitetural.",
    bullets: [
      "Backend FastAPI funcional com ingestão, extração, recomendação, outcome e métricas.",
      "Modelos de domínio implementados: Case, Recommendation e Outcome.",
      "Pipeline com LLM, embeddings, recommendation pipeline, judge e justifier conectados.",
      "Frontend para advogado e dashboard, servindo como camada visual para a demo.",
    ],
    footer: "Aqui mostramos execução real: o projeto saiu do pitch e virou fluxo operacional rodando.",
    status: "entregue",
  },
  {
    id: "demo",
    eyebrow: "09 · Demo",
    title: "Demo: do caso recebido à decisão registrada.",
    lead: "A melhor forma de apresentar é mostrar o ciclo completo em vez de isolar apenas a recomendação.",
    bullets: [
      "Abrir um caso e mostrar os documentos disponíveis.",
      "Exibir a recomendação: acordo ou defesa, valor, justificativa e confiança.",
      "Destacar sinais como red flags, histórico e revisão do judge.",
      "Registrar a decisão do advogado.",
      "Fechar no dashboard com métricas agregadas de aderência e efetividade.",
    ],
    footer: "Narrativa ideal da demo: entender → recomendar → decidir → medir.",
    status: "misto",
  },
  {
    id: "diferenciais",
    eyebrow: "10 · Diferenciais",
    title: "Mais do que IA com PDF: governança, rastreabilidade e decisão assistida.",
    lead: "A solução se diferencia por transformar IA em ferramenta operacional com política explícita, rastreamento e espaço para governança jurídica.",
    bullets: [
      "Política de acordos versionada e separada do código.",
      "Recomendação explicável, com justificativa e trace em vez de resposta opaca.",
      "Humano no loop: apoio ao advogado, não substituição da decisão humana.",
      "Monitoramento de aderência, aceitação e qualidade da recomendação.",
    ],
    footer: "Mensagem para a banca: o diferencial é operacionalizar IA com governança.",
    status: "misto",
  },
  {
    id: "limitacoes",
    eyebrow: "11 · Limitações Conhecidas",
    title: "MVP honesto: o que ainda é limitação atual.",
    lead: "A apresentação ganha credibilidade quando separa claramente o que já roda do que ainda depende de evolução técnica e de produto.",
    bullets: [
      "Motor de decisão na V5 pode evoluir para versões mais sofisticadas e calibradas.",
      "A solução depende de LLM externo (OpenAI) para partes importantes do fluxo.",
      "Ingestão atual suporta apenas arquivos PDF.",
      "Dashboard pode evoluir em profundidade visual, filtros e governança de uso.",
    ],
    footer: "Preferimos atacar o coração do problema primeiro e crescer com clareza de roadmap e governança.",
    status: "misto",
  },
  {
    id: "visao",
    eyebrow: "12 · Próximos Passos (1 mês)",
    title: "Com mais 1 mês, o MVP ganha profundidade operacional.",
    lead: "O caminho mais natural no curto prazo é fortalecer medição de impacto, governança jurídica e capacidade de operar sobre carteiras maiores.",
    bullets: [
      "Backtest mais forte da política no histórico completo de 60k sentenças.",
      "Dashboard mais robusto, com recortes e impacto econômico.",
      "Fluxo de alçada e aprovação multinível.",
      "Integração com sistemas reais e feedback loop para melhorar a política.",
      "Simulador de cenários para o jurídico testar mudanças antes de publicar regras.",
    ],
    footer: "Fechamento: o MVP já organiza a decisão; a visão é escalar com mais governança e impacto.",
    status: "visao",
  },
  {
    id: "expansao",
    eyebrow: "13 · Escalabilidade e Expansão",
    title: "De recomendador de casos para copiloto jurídico operacional.",
    lead: "A base construída permite expandir para uma camada conversacional e proativa, capaz de cruzar dados, sugerir a melhor estratégia e alertar o jurídico no momento certo.",
    bullets: [
      "Chat relacional sobre dados dos casos para consultas estratégicas em linguagem natural.",
      "Sugestão automática das melhores ações por carteira, perfil de risco e contexto documental.",
      "Notificações proativas por WhatsApp ou e-mail para alertar casos prioritários.",
      "Priorização inteligente da fila com base em risco, urgência e chance de acordo eficiente.",
      "Escalabilidade de caso a caso para visão gerencial de carteiras completas.",
    ],
    footer: "Visão de expansão: sair de um recomendador de casos e evoluir para um copiloto jurídico operacional e escalável.",
    status: "visao",
  },
]
