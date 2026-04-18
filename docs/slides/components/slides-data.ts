export type Slide = {
  id: string
  eyebrow: string
  title: string
  lead: string
  bullets: string[]
  footer?: string
  status?: "entregue" | "misto" | "visao"
}

export const slides: Slide[] = [
  {
    id: "problema",
    eyebrow: "01 · Problema",
    title: "Como orientar um advogado diante de 5.000 casos para analisar?",
    lead: "No contencioso massificado, o problema não é só jurídico: é operacional. Com milhares de processos na fila, o advogado precisa de direcionamento rápido para saber onde aprofundar, onde defender e onde considerar acordo.",
    bullets: [
      "Ler autos e subsídios manualmente em milhares de casos consome tempo demais e reduz a capacidade de resposta.",
      "Sem triagem inteligente, casos urgentes e casos de maior risco acabam disputando a mesma atenção limitada.",
      "A decisão entre defender ou acordar pode variar muito entre advogados mesmo em situações parecidas.",
      "Quando há 5.000 casos para analisar, a dor principal deixa de ser só técnica: passa a ser falta de orientação e priorização.",
    ],
    footer: "Ponto de partida: transformar volume jurídico em fila priorizada, com orientação objetiva e rastreável para o advogado.",
    status: "misto",
  },
  {
    id: "solucao",
    eyebrow: "02 · Solução",
    title: "Uma política de acordos assistida por IA, mas com núcleo auditável.",
    lead: "A plataforma recebe os documentos do caso, estrutura os dados com apoio de LLM e entrega ao advogado uma recomendação objetiva com justificativa e rastreabilidade.",
    bullets: [
      "Entrada: autos + subsídios do banco.",
      "Saída: defesa ou acordo, faixa de valor sugerida, confiança e justificativa.",
      "A IA apoia extração, revisão e explicação, sem virar caixa-preta decisória.",
      "O advogado continua no centro da decisão e o sistema registra o outcome final.",
    ],
    footer: "Mensagem-chave: LLM nas pontas, política e estatística no centro.",
    status: "misto",
  },
  {
    id: "fluxo",
    eyebrow: "03 · Fluxo do produto",
    title: "Do PDF à recomendação em um ciclo completo.",
    lead: "O valor do projeto não está só em sugerir uma estratégia, mas em fechar o ciclo operacional com decisão humana e métricas.",
    bullets: [
      "Upload dos PDFs do caso.",
      "Extração estruturada do conteúdo jurídico e documental.",
      "Análise de sinais do caso e busca de contexto histórico semelhante.",
      "Geração da recomendação com justificativa.",
      "Registro do outcome do advogado e alimentação do dashboard.",
    ],
    footer: "Fluxo end-to-end: documentos → recomendação → outcome → monitoramento.",
    status: "entregue",
  },
  {
    id: "ia",
    eyebrow: "04 · Arquitetura e IA",
    title: "IA como apoio inteligente, não como decisão opaca.",
    lead: "A arquitetura combina extração com LLM, retrieval semântico, política versionada e uma segunda camada de revisão para aumentar confiança e explicabilidade.",
    bullets: [
      "LLM para extração estruturada de autos, subsídios e features relevantes.",
      "Embeddings para recuperar casos similares no histórico e dar contexto à decisão.",
      "Motor de decisão híbrido: regras, política, sinais do caso e histórico.",
      "LLM-as-judge para revisar a recomendação e gerar justificativa auditável.",
    ],
    footer: "Diferencial técnico: usar IA onde ela é forte e manter o núcleo decisório verificável.",
    status: "entregue",
  },
  {
    id: "entregue",
    eyebrow: "05 · MVP funcional",
    title: "O que já foi entregue no repositório atual.",
    lead: "A base funcional do fluxo jurídico já existe no backend e sustenta uma narrativa real de MVP, não apenas de intenção arquitetural.",
    bullets: [
      "Backend FastAPI funcional com ingestão, extração, recomendação, outcome e métricas.",
      "Modelos de domínio implementados: Case, Recommendation e Outcome.",
      "Pipeline com LLM, embeddings, recommendation pipeline, judge e justifier já conectados.",
      "Frontend já existe para advogado e dashboard, servindo como camada visual para a demo.",
    ],
    footer: "Aqui mostramos execução real: o projeto saiu do pitch e virou fluxo operacional rodando.",
    status: "entregue",
  },
  {
    id: "demo",
    eyebrow: "06 · Demo",
    title: "Demo sugerida: do caso recebido à decisão registrada.",
    lead: "A melhor forma de apresentar é mostrar o ciclo completo em vez de isolar apenas a recomendação.",
    bullets: [
      "Abrir um caso e mostrar os documentos disponíveis.",
      "Exibir a recomendação: acordo ou defesa, valor, justificativa e confiança.",
      "Destacar sinais como red flags, histórico e revisão do judge.",
      "Registrar a decisão do advogado.",
      "Fechar no dashboard com métricas agregadas.",
    ],
    footer: "Narrativa ideal da demo: entender → recomendar → decidir → medir.",
    status: "misto",
  },
  {
    id: "diferenciais",
    eyebrow: "07 · Diferenciais",
    title: "Mais do que IA com PDF: governança, rastreabilidade e decisão assistida.",
    lead: "A solução se diferencia por transformar IA em ferramenta operacional com política explícita, rastreamento e espaço para governança jurídica.",
    bullets: [
      "Política de acordos versionada e separada do código.",
      "Recomendação explicável, com justificativa em vez de resposta opaca.",
      "Humano no loop: apoio ao advogado, não substituição da decisão humana.",
      "Uso de histórico e similares para calibrar risco e faixa de acordo.",
      "Monitoramento de aderência, aceitação e qualidade da recomendação.",
    ],
    footer: "Mensagem para a banca: o diferencial é operacionalizar IA com governança.",
    status: "misto",
  },
  {
    id: "limitacoes",
    eyebrow: "08 · Limitações",
    title: "MVP honesto: o que ainda é limitação atual.",
    lead: "A apresentação ganha credibilidade quando separa claramente o que já roda do que ainda depende de evolução técnica e produto.",
    bullets: [
      "OCR e documentos escaneados ainda não são o foco principal do MVP atual.",
      "Dashboard pode evoluir em profundidade visual e filtros.",
      "A política atual é uma v1 baseada em heurísticas, sinais e histórico.",
      "Fluxos de alçada/aprovação e integração com sistemas externos ainda são evolução natural.",
    ],
    footer: "Preferimos atacar o coração do problema primeiro e crescer com clareza de roadmap.",
    status: "misto",
  },
  {
    id: "visao",
    eyebrow: "09 · Próximos passos",
    title: "De assistente jurídico para plataforma de decisão orientada por dados.",
    lead: "A próxima fase é ampliar governança, medir impacto econômico com mais profundidade e transformar o MVP em vantagem operacional mensurável.",
    bullets: [
      "Backtest mais forte da política no histórico completo.",
      "Dashboard mais robusto, com recortes e impacto econômico.",
      "Fluxo de alçada e aprovação multinível.",
      "Integração com sistemas reais e feedback loop para melhorar a política.",
      "Simulador de cenários para o jurídico testar mudanças antes de publicar regras.",
    ],
    footer: "Fechamento: o MVP já organiza a decisão; a visão é escalar isso com mais governança e impacto.",
    status: "visao",
  },
]
