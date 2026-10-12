# TCC: análise em dashboard x análise por IA generativa em linguagem natural

Briefing para continuar o trabalho em outra conversa. Estado em 11 out. 2026.

---

## 1. Identificação

- **Instituição:** Centro Universitário Unidade de Ensino Superior Dom Bosco (UNDB), São Luís.
- **Curso:** Engenharia de Software (bacharelado).
- **Tipo:** monografia, no template TEMPLATE_TCC_2 da UNDB.
- **Autor e orientador:** ainda não preenchidos no documento.
- **Versão mais recente do documento:** `tcc_undb_20261011_1857.docx`.

## 2. Tema, recorte e problema

- **Tema:** IA generativa e Business Intelligence (BI): substituição ou complemento na análise de dados.
- **Recorte:** comparar duas formas de análise sobre os **mesmos dados** e as **mesmas perguntas de negócio**:
  - **Solução A, dashboard:** construído no Power BI e consultado pelo usuário com filtros e gráficos. O Power BI é só a ferramenta de construção.
  - **Solução B, IA generativa:** o usuário faz a pergunta em linguagem natural; um LLM gera SQL (e, se preciso, gráfico) sobre o mesmo banco e devolve a resposta.
- **Fora do escopo:** os recursos de linguagem natural do próprio Power BI (Q&A e Copilot).
- **Pergunta de pesquisa:** em quais cenários a análise feita por IA generativa em linguagem natural pode substituir ou complementar a análise em dashboards de BI?
- **Hipótese (versão de trabalho):** a IA responde mais rápido a perguntas exploratórias e não previstas; o dashboard é mais confiável para indicadores recorrentes e decisões que exigem precisão e rastreabilidade. Tendência esperada: complemento, não substituição.
  - A banca simulada pediu definição operacional de "exploratória" e de "confiável". Ver seção 6.
- **Objetivo geral:** comparar as duas abordagens para identificar em quais cenários cada uma é mais adequada.
- **Produto final:** uma **matriz de decisão** ("quando usar cada abordagem"), cruzando tipos de pergunta com dimensões de comparação.

## 3. Estrutura do trabalho

| Capítulo | Situação | O que contém |
|---|---|---|
| 1 Introdução | Escrita (pp. 15-21) | Contexto, problema, pergunta, hipótese, objetivos, justificativa, estrutura |
| 2 Referencial teórico | Escrito (pp. 22-34) | 2.1 BI e data warehouse; 2.2 Dashboards; 2.3 IA generativa e LLMs; 2.4 Interfaces em linguagem natural (Text-to-SQL, Text-to-Vis, benchmarks e métricas); 2.5 Estado da arte (Quadro 1); 2.6 Síntese (Quadro 2: dimensões de comparação) |
| 3 Metodologia | A escrever | Desenho do estudo: fases 1 a 7 abaixo |
| 4 Desenvolvimento | A escrever | Construção das duas soluções (fases 1 a 3) |
| 5 Resultados e discussão | A escrever | Avaliação técnica, estudo com usuários, matriz de decisão |
| 6 Conclusão | A escrever | Resposta à pergunta, limitações, trabalhos futuros |

O documento ainda mostra a estrutura de exemplo do template a partir do capítulo 3. Capa, folha de rosto, resumo, abstract e lista de siglas também ainda são texto do template.

## 4. Dimensões de comparação (vêm do Quadro 2 do referencial)

| Dimensão | Dashboard | IA generativa em linguagem natural |
|---|---|---|
| Origem das perguntas | Antecipadas no projeto | Formuladas no momento |
| Flexibilidade | Limitada ao que foi modelado e exibido | Ampla, mas sujeita a ambiguidade e à complexidade do esquema |
| Reprodutibilidade | Determinística | Estocástica (o mesmo prompt pode variar) |
| Correção e verificação | Depende da qualidade dos dados e do modelo, validados antes | Sujeita a alucinação; SQL correto na sintaxe e errado no sentido |
| Esforço técnico | Concentrado na construção (ETL, modelagem, visual) | Concentrado na preparação do esquema, prompt e validação |
| Custo e tempo | Implantação custosa | Custo por consulta (tokens) e latência |
| Cenário complexo | Restrito ao que foi exibido | Queda acentuada em bancos corporativos |

Essas dimensões viram as métricas do experimento.

---

## 5. Desenho do experimento: fases

Princípio geral: medir de **duas formas complementares** (avaliação técnica sem usuários e estudo com usuários), **congelar o dashboard antes de criar as perguntas** e **classificar as perguntas por tipo**. A conclusão deve dizer qual abordagem é melhor *para cada tipo de pergunta*.

### Fase 1: Base de dados
- Escolher uma base pública de vendas com **várias tabelas relacionadas**. Uma tabela única favoreceria a IA e enfraqueceria a validade.
- Candidata: *Brazilian E-Commerce Public Dataset by Olist* (Kaggle). **A conferir:** licença, número de tabelas e conteúdo.
- Carregar num banco único (SQLite ou PostgreSQL), usado pelas duas soluções.
- Documentar tabelas, colunas, linhas e toda limpeza feita.
- **Aparece no TCC em:** cap. 3 (descrição da base) e cap. 4 (preparação).

### Fase 2: Dashboard (Solução A)
1. Escrever um *briefing* de requisitos com os KPIs que um gestor pediria: faturamento, ticket médio, pedidos por estado, prazo de entrega, nota média etc.
2. Construir no Power BI com boas práticas: modelo em estrela e medidas validadas.
3. Registrar as horas gastas por etapa (modelagem, medidas, visual). É a medida de **esforço técnico**.
4. **Congelar a versão** antes de criar o banco de perguntas.
- **Aparece no TCC em:** cap. 4 (prints, modelo de dados, medidas) e cap. 5 (esforço).

### Fase 3: Sistema em linguagem natural (Solução B)
- Fluxo: pergunta, LLM gera SQL, SQL executado no mesmo banco, resposta mostrada com o SQL gerado e gráfico opcional.
- Fixar e documentar: modelo e versão, temperatura, prompt completo, e o que é enviado ao modelo (só esquema e descrição das colunas, sem dados, por privacidade e LGPD).
- Registrar em log: pergunta, SQL, resultado, tempo de resposta e tokens (custo).
- Registrar as horas de desenvolvimento, para comparar com o dashboard.
- **Pendente:** escolher o LLM e definir quem paga a API.
- **Aparece no TCC em:** cap. 4 (arquitetura, prompt, telas) e cap. 5 (custo e tempo).

### Fase 4: Banco de perguntas com gabarito
De 16 a 20 perguntas, distribuídas em quatro tipos:

| Tipo | Exemplo | O que testa |
|---|---|---|
| A. Prevista | "Qual foi o faturamento de 2017?" | Responde direto no dashboard |
| B. Variação | "E só em SP, no 2º semestre?" | Exige filtros e interação |
| C. Não prevista | "Vendedores com nota abaixo de 3 atrasam mais?" | Cruzamento que o painel não modelou |
| D. Ambígua ou sem resposta | "Qual o lucro?" (a base não tem custo) | Se a IA alucina ou avisa |

- **Gabarito:** calculado em SQL e conferido por outra pessoa (idealmente o orientador).
- **Critério de acerto definido antes:**
  - número: igual ao gabarito, com tolerância declarada;
  - lista: os mesmos itens;
  - resposta descritiva: rubrica.
- Pedir a alguém de fora para revisar as perguntas do tipo C.
- **Aparece no TCC em:** cap. 3 (critérios) e apêndice (lista completa com gabarito).

### Fase 5: Avaliação técnica (sem usuários)
- **IA:** rodar cada pergunta **5 vezes** e medir:
  - acurácia em relação ao gabarito;
  - consistência entre execuções;
  - tempo;
  - custo.
- **Dashboard:** para cada pergunta, registrar:
  - se responde (sim, parcial ou não);
  - número de passos ou cliques;
  - esforço para adaptar o painel quando não responde.
- Totalmente reprodutível. Sozinha, já sustenta uma matriz de decisão.
- **Aparece no TCC em:** cap. 5.

### Fase 6: Estudo com usuários
- **Participantes:** 10 a 20 pessoas que trabalham com dados. Se possível, incluir usuários de negócio (gestores) para comparar perfis.
- **Desenho intrassujeito:** cada pessoa usa as duas ferramentas.
  - Metade começa pelo dashboard e metade pela IA.
  - Cada ferramenta recebe um conjunto diferente, mas equivalente, de perguntas, para evitar efeito de aprendizado.
- **Sessões acompanhadas** de 30 a 45 minutos, presenciais ou por chamada com tela compartilhada. Uma ficha preenchida sozinho não mede tempo nem acerto com confiabilidade.
- Fazer antes um **piloto com 2 pessoas**.
- **Métricas por pergunta:** tempo; acerto em relação ao gabarito; confiança (escala de 1 a 5); se tentou conferir a resposta.
- **Métricas por ferramenta:** SUS (usabilidade) e, opcionalmente, NASA-TLX (carga de trabalho).
- **Fim da sessão:** preferência por tipo de pergunta e comentários abertos.
- **Métrica-chave:** quantas vezes o participante aceitou **com confiança** uma resposta **errada** da IA (viés de automação, como em Gu et al., 2024).
- **Análise:** estatística descritiva; teste de Wilcoxon pareado se a amostra permitir; categorização das respostas abertas.
- **Ética (decidir antes de recrutar):** pesquisa com pessoas pode exigir aprovação de Comitê de Ética em Pesquisa (CEP) via Plataforma Brasil. Há dispensas para certas pesquisas de opinião sem identificação (Resolução CNS 510/2016). **A verificar com o orientador e a coordenação.** Usar termo de consentimento (TCLE) e anonimizar os dados em qualquer caso.
- **Aparece no TCC em:** cap. 3 (protocolo), cap. 5 (resultados) e apêndices (roteiro, formulário, TCLE).

### Fase 7: Análise e matriz de decisão
- Cruzar os **tipos de pergunta (A a D)** com as **dimensões** (acerto, tempo, reprodutibilidade, custo, esforço, confiança).
- A conclusão sai da matriz. Exemplo de formato, não de resultado: "nas perguntas do tipo C, a IA acertou X% e o dashboard não respondeu; nas do tipo D, a IA inventou valores em Y% das execuções".
- **Ameaças à validade:**
  - interna: o autor constrói e avalia;
  - externa: uma base e um modelo só;
  - de construto: gabarito e métricas representam "boa análise"?;
  - de conclusão: tamanho da amostra.
- Definir as métricas e a análise **antes** de coletar dados e relatar também o que contrariar a hipótese.
- **Aparece no TCC em:** cap. 5 (matriz) e cap. 6 (conclusão e limitações).

### Versões possíveis
- **Mínima defensável:** fases 1 a 5 e 7, com estudo exploratório pequeno (6 a 8 pessoas).
- **Completa:** todas as fases.
- Em qualquer versão, a lacuna da seção 2.5 deve ser reescrita para corresponder exatamente ao que for feito.

---

## 6. Problemas apontados na banca simulada (a resolver)

1. **Lacuna x experimento:** a seção 2.5 aponta falta de estudos com usuários de negócio. Se o experimento não tiver usuários, a lacuna precisa ser reescrita.
2. **Tempo:** definir se "tempo" do dashboard inclui a construção ou só a consulta.
3. **Amostra e não determinismo:** repetir as perguntas na IA e medir a variação.
4. **Base simples demais:** usar várias tabelas ou declarar a limitação.
5. **Hipótese:** operacionalizar "exploratória" (tipos B e C) e "confiável" (acerto e consistência).
6. **Introdução longa e repetida com o cap. 2:** enxugar e concentrar os números no referencial.
7. **Referencial descritivo:** aumentar a síntese crítica entre as fontes.
8. **Estado da arte frágil:** busca sem contagem por base; poucos trabalhos de BI. Artigo do SBSI 2025 sobre Text-to-SQL em português ainda não lido.
9. **Assimetria do Quadro 2:** fortalecer as fontes sobre limitações do dashboard.
10. **Temas a acrescentar ao referencial:** LGPD; ISO/IEC 25010 (vínculo com Engenharia de Software); SUS e NASA-TLX, se houver usuários; método experimental ou GQM (Basili); camada semântica e medidas no Power BI.
11. **Formais:**
    - pré-textuais do template (capa com "NOME COMPLETO" e "2020");
    - lista de siglas do template;
    - cap. 3 do template com Quadro 1 duplicado;
    - datas [201-] e [2013?];
    - preprints que podem ser trocados pela versão publicada.
12. **Uso de IA:** verificar a política da UNDB e declarar o uso.

## 7. Decisões pendentes (levar ao orientador)

- Haverá estudo com usuários? Qual o posicionamento sobre CEP?
- Base de dados (Olist ou outra).
- LLM e linguagem (SQL, Python ou ambos); custo da API.
- Recuo de parágrafo (1,25 ou 2 cm) e tamanho da fonte da paginação.
- Fonte 10 dentro dos quadros.

## 8. Regras do projeto (resumo, valem em qualquer conversa)

**Fontes**
- Só citar fonte aberta e **lida na íntegra**. Trecho de busca ou resumo de ferramenta não conta.
- Fonte paga ou que não abre: não citar; pedir o PDF ou sugerir substituta aberta.
- Nada de dado bibliográfico de memória. Elemento não visto no documento é omitido.
- Números na formulação da fonte, sem arredondar.
- Fonte promocional: atribuir no texto e sinalizar.

**Normas ABNT (sempre a edição mais recente)**
- NBR 6023:2025 (referências)
- NBR 10520:2023 (citações autor-data, autor em caixa baixa entre parênteses, *et al.* em itálico)
- NBR 14724:2024 (trabalhos acadêmicos)
- NBR 6028:2021 (resumo)
- NBR 6027:2012 (sumário)
- NBR 6024:2012 (numeração progressiva)

**Escrita**
- Registro acadêmico formal e impessoal, sem primeira pessoa.
- Sem travessão.
- Evitar "vale ressaltar", "é importante destacar" e trios forçados.
- Aplicar o *humanizer* só ao texto corrido, sem alterar fatos, números, nomes ou citações.

**Formatação**
- A4; margens de 3 cm (esquerda e superior) e 2 cm (direita e inferior).
- Times New Roman 12, espaçamento 1,5, recuo de 1,25 cm.
- Legendas de ilustrações em fonte 11, acima: **Quadro 1** - Nome.
- Fonte das ilustrações em tamanho 10, abaixo.

**Entrega**
- Sempre um .docx `tcc_undb_{timestamp}`, editado a partir do mais recente (sem reconstruir do zero).
- Converter em PDF, conferir visualmente e informar as páginas de cada seção alterada.
- Ao final de cada entrega, listar: (1) o que foi aberto e lido, com data; (2) o que não abriu e por quê; (3) o que foi usado de memória.

## 9. Fontes já lidas na íntegra (podem ser citadas)

- **BI e dados:**
  - Chaudhuri e Dayal (1997)
  - Chaudhuri, Dayal e Narasayya (2011)
  - Kimball Group ([2013?], material de consultoria)
  - Schinaider, Lee e Servare Junior (2022)
- **Dashboards:**
  - Few (2006, white paper patrocinado)
  - Sarikaya et al. ([201-], versão dos autores)
  - Bach et al. (2022)
- **IA generativa e LLMs:**
  - Feuerriegel et al. (2024)
  - Raiaan et al. (2024)
  - Vaswani et al. (2023, arXiv v7)
  - Wei et al. (2022)
  - Lewis et al. (2021)
  - Huang et al. (2024)
- **Linguagem natural para dados:**
  - Hong et al. (2025)
  - Liu et al. (2025)
  - Zhang et al. (2024)
  - Kanburoğlu e Tek (2024)
  - Lima, Vasconcelos e Gadelha (2025)
  - Shen et al. (2022)
  - Kavaz, Puig e Rodríguez (2023)
  - Yu et al. (2018, Spider)
  - Li et al. (2023, BIRD)
  - Lei et al. (2025, Spider 2.0)
  - Fonseca et al. (2026)
  - Carvalho, S. Júnior e Oliveira (2025)
- **Sistemas e estudos com analistas:**
  - Maddigan e Susnjak (2023, Chat2VIS)
  - Dibia (2023, LIDA)
  - Cheng, Li e Bing (2023)
  - Gu et al. (2024)
  - Seabra et al. (2025)

**Ainda sem fonte lida** (exigem PDF antes de entrar no texto): LGPD, ISO/IEC 25010, SUS, NASA-TLX, GQM, Resolução CNS 510/2016 e o artigo do SBSI 2025.

## 10. Próximos passos sugeridos

1. Levar as decisões da seção 7 ao orientador.
2. Escrever o capítulo 3 (Metodologia) com o desenho da seção 5.
3. Escolher a base e montar o banco de perguntas com gabarito.
4. Desenvolver o protótipo da Solução B e construir e congelar a Solução A.
5. Preparar roteiro de sessão, formulário (SUS, confiança) e TCLE.
6. Rodar a avaliação técnica, depois o piloto, depois o estudo com usuários.
7. Escrever os capítulos 4, 5 e 6 e revisar a introdução e a seção 2.5.
