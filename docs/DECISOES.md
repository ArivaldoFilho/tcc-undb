# Decisões do projeto

Registro vivo das decisões técnicas e metodológicas, para usar na escrita do
TCC. Cada item diz o que foi decidido, por quê e em que capítulo entra.
Atualizado a cada decisão nova; as mais recentes ficam no fim de cada seção.

**Legenda:** ✅ decidido · ⏳ pendente · ⚠️ ameaça à validade ou limitação, que vai para o cap. 5 ou 6

---

## Pendências abertas

| # | Pendência | Com quem | Desde |
|---|---|---|---|
| P1 | O estudo com usuários precisa de aprovação do CEP (Plataforma Brasil) ou é dispensado? | Orientador e coordenação | 12/10/2026 |
| P2 | Versão mínima (sem usuários) ou completa (com usuários)? | Orientador | 12/10/2026 |
| P3 | Como medir o esforço de construção do dashboard, já que ele foi gerado com apoio de IA (ver D2.1)? | Orientador | 12/10/2026 |
| P4 | Qual é a política da UNDB para uso de IA, e como declarar esse uso? | Coordenação | 12/10/2026 |
| P5 | Remover o segmentador de Semestre do dashboard antes de congelar (ver D2.6)? | Autor | 12/10/2026 |
| P6 | Congelar o dashboard e registrar a data | Autor | 12/10/2026 |
| P8 | Conferência dos gabaritos pelo orientador; revisão das perguntas do tipo C por uma pessoa de fora | Orientador e revisor externo | 12/10/2026 |
| P9 | Conferir a licença da base Olist no Kaggle | Autor | 12/10/2026 |
| P10 | Ler a adaptação brasileira do SUS e ajustar os itens da página do estudo | Autor | 12/10/2026 |
| P11 | Preencher e revisar o termo de consentimento (`config/estudo.json`, `static/estudo.html`) | Autor e orientador | 12/10/2026 |
| P12 | Como o Power BI foi conectado ao Supabase: certificado raiz instalado ou criptografia desligada? Registrar a escolha | Autor | 12/10/2026 |
| P13 | Cenários já escritos (D6.20). Falta escolher as perguntas do estudo depois da Fase 5, priorizando as que a IA às vezes erra | Autor | 12/10/2026 |
| P15 | Medir o esforço técnico como esforço de adaptação: para cada pergunta C, o que o painel precisaria mudar (medida, visual, modelo) e o que o Indaga precisaria mudar | Autor e orientador | 12/10/2026 |
| P16 | Limite de gasto no console da Anthropic antes de divulgar o link (qualquer sessão nova pode gerar até 32 consultas, cerca de US$ 1) | Autor | 12/10/2026 |
| P17 | Conferência das medidas: os 6 cartões da Visão geral já conferem com o SQL (print de 12/10/2026); faltam Frete, Entregues, Atrasados, Prazo médio, Avaliações e Faturamento 2017 | Autor | 12/10/2026 |

---

## Fase 1: Base de dados

- ✅ **D1.1 Base:** *Brazilian E-Commerce Public Dataset by Olist* (Kaggle), com 9 tabelas relacionadas. **Motivo:** uma base com várias tabelas evita favorecer a IA, como uma tabela única faria (plano, seção 5, Fase 1). **Cap. 3.**
- ✅ **D1.2 Banco:** PostgreSQL 17 no Supabase (região us-east-1), um único banco para as duas soluções. **Cap. 3 e 4.**
- ✅ **D1.3 Sem limpeza:** os CSVs foram carregados como estão, com conferência de cabeçalho e de tipos antes da carga. Nenhum valor foi alterado ou removido. **Cap. 4.**
- ✅ **D1.4 Linhas por tabela** (carga de 12/10/2026): customers 99.441 · sellers 3.095 · products 32.951 · product_category_name_translation 71 · orders 99.441 · order_items 112.650 · order_payments 103.886 · order_reviews 99.224 · geolocation 1.000.163. **Cap. 3.**
- ✅ **D1.5 Chaves:** 8 tabelas com chave primária. Em `order_reviews`, a chave é o par (review_id, order_id), porque review_id se repete 814 vezes e o par não se repete. `geolocation` ficou sem chave primária, porque o prefixo de CEP se repete. As 6 chaves estrangeiras foram criadas sem nenhuma violação. **Cap. 4.**
- ✅ **D1.6 Peculiaridades encontradas na base**, que entram na descrição da base:
  - 8 pedidos válidos não têm nenhum item;
  - 6 pedidos cancelados ou indisponíveis têm data de entrega;
  - 2 categorias não têm tradução (`pc_gamer` e `portateis_cozinha_e_preparadores_de_alimentos`), e há produtos sem categoria;
  - o período vai de 04/09/2016 a 17/10/2018, mas o **período efetivo é de jan. 2017 a ago. 2018**: 2016 tem 296 pedidos válidos (quase todos em out.), set. 2018 tem 1 e out. 2018 nenhum (só cancelados). Isso afeta qualquer análise "do último período" (ver B7) e os totais anuais de 2016 e 2018.

  **Cap. 3.**
- ✅ **D1.7 Usuários do banco:**
  - `indaga_app`: dono dos schemas, usado na carga e no log;
  - `indaga_leitor`: somente leitura, com transação read-only e timeout de 20 s. É quem executa o SQL gerado pela IA e quem o Power BI usa.

  **Motivo:** menor privilégio. A senha do usuário `postgres` não foi usada. **Cap. 4** (arquitetura e segurança).

## Definições de métrica (compartilhadas pelas duas soluções)

- ✅ **D0.1 Uma única fonte de definições:** `config/descricoes.json`. As medidas DAX do dashboard reproduzem o mesmo texto. **Motivo:** se as definições diferissem, a comparação mediria definições diferentes, e não abordagens diferentes. **Cap. 3.**
- ✅ **D0.2 Três definições deixadas explícitas** em 12/10/2026, porque o dashboard precisou escolher uma leitura:
  - **Prazo de entrega:** diferença entre as datas, sem a hora.
  - **Nota média:** o período é o da compra do pedido avaliado.
  - **Clientes únicos:** contados só entre os clientes com pedidos válidos.

  **Motivo:** sem isso, o Indaga e o dashboard poderiam calcular números diferentes para a mesma métrica. Por exemplo, o prazo calculado com a hora dá 21,70 dias em B3, contra 21,63 pela definição. **Cap. 3.**
- ✅ **D0.3 Métricas de entrega** (entregue, atrasado e prazo) **não filtram pedido válido.** **Motivo:** a definição não pede esse filtro. Os 6 cancelados com data de entrega contam como entregues. **Cap. 3.**

## Fase 2: Dashboard (Solução A)

- ⚠️ **D2.1 O dashboard foi gerado com apoio de IA** (Claude), como projeto PBIP. As horas de construção não representam o esforço de um desenvolvedor humano. **Ver P3.** **Cap. 3 e 5.**
- ✅ **D2.2 Modelo em estrela:**
  - 3 fatos, uma por grão: fItens (item), fPedidos (pedido) e fAvaliacoes (avaliação);
  - 4 dimensões: dCalendario, dCliente, dProduto e dVendedor;
  - as fatos não se ligam entre si.

  **Motivo:** juntar fatos de grãos diferentes produz resultados incorretos (Kimball Group, [2013?]). **Cap. 4.**
- ✅ **D2.3 As regras de negócio ficam no SQL de cada fato** ("pedido válido", "entregue", "atrasado" e "prazo"). As medidas DAX só somam, contam e dividem. Os SQLs estão em `dashboard/sql/`. **Cap. 4.**
- ✅ **D2.4 Medida "Pedidos" com dois caminhos:** sem filtro de produto ou vendedor, ela conta os pedidos de fPedidos; com esse filtro, conta os de fItens. **Motivo:** fazer o ticket médio por categoria funcionar. Por causa dos 8 pedidos sem item (D1.6), as duas contagens diferem no total. **Cap. 4.**
- ✅ **D2.5 O segmentador de categoria só existe na página Vendas.** **Motivo:** entrega, atraso e nota não reagem ao filtro de produto. **Cap. 4.**
- ⚠️ **D2.6 Viés na construção:** o dashboard foi montado depois de existirem 6 perguntas de exemplo, e o segmentador de Semestre coincide com a pergunta B1. **Ver P5.** **Cap. 5** (validade interna).
- ✅ **D2.7 Modo de importação**, com 3 páginas: Visão geral, Vendas e Entrega e satisfação. A conferência das 12 medidas contra o SQL está em `dashboard/README.md`. **Cap. 4.**
- ✅ **D2.8 Publicação pelo "Publicar na Web" do Power BI.** O link é público, o que não é problema porque a base é pública. **Motivo:** o estudo com usuários é online (D6.1). **Cap. 4.**
- ✅ **D2.9 Navegação lateral** (12/10/2026, antes do congelamento): um Navegador de página vertical na coluna esquerda de cada página (as páginas passaram de 1280 para 1420 px de largura). **Motivo:** no "Publicar na Web", as abas de página ficam pouco visíveis no rodapé, e o participante do estudo pode não perceber as outras páginas. Isso prejudicaria o painel por um motivo de interface, e não de abordagem. **Cap. 4.**

## Fase 3: Indaga (Solução B)

As escolhas originais estão no `README.md`, na tabela "Escolhas para o experimento":
- modelo `claude-opus-5-5` com esforço `medium`;
- temperatura não enviada;
- sem cache, sem few-shot, sem retry automático e sem fallback de modelo;
- esquema inteiro no prompt;
- `config_hash` gravado em cada execução.

**Cap. 4.**

- ✅ **D3.1 O que o modelo recebe:** na decisão e na geração do SQL, só a estrutura, as descrições e as definições, sem nenhuma linha de dados. Na explicação, até 50 linhas do resultado. **Cap. 4**, com a discussão de LGPD.
- ✅ **D3.2 Três barreiras de segurança:** um guardrail que aceita só um SELECT, a transação read-only e o usuário sem permissão de escrita. **Cap. 4.**

## Fase 4: Banco de perguntas

- ✅ **D4.1 Os tipos são definidos em relação ao dashboard congelado**, e não pela dificuldade da pergunta:
  - **A:** um visual responde, com no máximo um segmentador;
  - **B:** o painel responde, mas com 2 ou mais filtros;
  - **C:** nenhum visual responde;
  - **D:** o dado não existe na base, ou a pergunta é ambígua.

  "Exploratória" equivale aos tipos B e C. **Motivo:** a banca simulada pediu uma definição operacional. **Cap. 3.**
- ✅ **D4.2 26 perguntas candidatas** (6 A, 6 B, 7 C e 7 D), com gabarito em SQL rodado no banco em 12/10/2026. Estão em `avaliacao/perguntas.csv` e `avaliacao/BANCO_DE_PERGUNTAS.md`. **Ver P7 e P8.** **Cap. 3 e apêndice.**
- ✅ **D4.3 Critérios de acerto**, definidos antes da coleta: numero, percentual, lista, recusa e rubrica. **Tolerâncias:**
  - 0,01 em valores em reais e em médias;
  - 0,05 dia no prazo;
  - 0,1 ponto percentual nos percentuais;
  - zero nas contagens.

  **Cap. 3.**
- ✅ **D4.4 Critério "percentual" criado** em 12/10/2026, antes de qualquer coleta. Ele aceita a resposta em pontos (6,63) ou em fração (0,0663). **Motivo:** as duas formas estão certas, e o critério "numero" marcaria a fração como erro. **Cap. 3.**
- ✅ **D4.5 Perguntas sensíveis às definições,** para separar quem segue as definições de quem não segue:
  - **A2:** contar os cancelados dá 54.011 pedidos, contra 53.532 pela definição;
  - **B5:** contar customer_id dá 23.599 clientes, contra 23.051 por customer_unique_id;
  - **C5:** o 5º e o 6º vendedores diferem em apenas R$ 517.

  **Cap. 5** (discussão dos erros).
- ⚠️ **D4.6 O mesmo agente (o autor, com apoio de IA) construiu as duas soluções e escreveu as perguntas.** A revisão pelo orientador e por uma pessoa de fora (P8) atenua isso. **Cap. 5** (validade interna).
- ✅ **D4.7 Versão do dashboard usada na classificação:** hash `650a8b665c17` dos arquivos de `dashboard/`. **Cap. 3.**
- ✅ **D4.8 Critério "recusa" com revisão manual** (12/10/2026, auditoria antes da coleta). Se a IA recusa (sem_dados ou esclarecimento), a resposta conta como correta. Se a IA executa o SQL e escreve a explicação, a resposta vai para `pendente_manual`, e não para incorreto. **Motivo:** no teste, a D2 ("Quanto vendemos ontem?") devolveu R$ 0,00, mas a explicação dizia que a base termina em 2018 e que a pergunta não pode ser respondida. Essa é a resposta desejada, e a regra anterior a marcava como erro. **Cap. 3.**
- ✅ **D4.9 Seis perguntas-armadilha** (B7, B8, C8, C9, C10, C11; 12/10/2026): qualidade de dados, conhecimento de domínio, fan trap, mudança de definição, várias etapas e granularidade. Não foram testadas na IA antes de entrar. **Motivo:** reduzir o risco de efeito teto (D9.3) sem viés de seleção; cada uma se justifica pela literatura (Kimball Group, [2013?]; Liu et al., 2025; Li et al., 2023) e pelo realismo. **Cap. 3.**
- ✅ **D4.10 Seleção final de 20 perguntas:** A1, A2, A5, A6 | B1, B3, B4, B5, B7, B8 | C1, C3, C4, C8, C9, C11 | D1, D2, D3, D5. Critérios: pelo menos 4 por tipo; mais B e C porque são os tipos exploratórios; evitar repetição e perguntas adivinháveis; limitar a correção manual (3 rubricas). As 32 candidatas ficam em `avaliacao/perguntas_candidatas.csv`. Falta a conferência do orientador (P8) antes do congelamento. **Cap. 3 e apêndice.**

## Fase 6: Estudo com usuários

- ✅ **D6.1 Estudo online e assíncrono, em vez de sessões acompanhadas** (12/10/2026). O participante recebe um link e faz tudo pelo navegador, com as duas ferramentas embutidas na página. **Motivo:** simplificar a coleta com participantes de fora, sem agendamento e sem acesso ao computador do autor. **Cap. 3.**
- ⚠️ **D6.2 Limitações do formato online:**
  - não há observação direta;
  - "conferiu a resposta" é declarado pela pessoa;
  - os cliques no Power BI não são registrados, porque o painel embutido é da Microsoft;
  - o ambiente de cada participante varia (máquina e internet).

  **Cap. 5 e 6.**
- ✅ **D6.3 Desenho intrassujeito com contrabalanceamento:** 4 grupos que cruzam a ordem das ferramentas com o conjunto de perguntas. Cada participante entra no grupo menos preenchido. **Cap. 3.**
- ✅ **D6.4 Dois conjuntos de 4 perguntas**, um de cada tipo, em pares: X = A1, B1, C4, D1 e Y = A2, B4, C3, D3. **Motivo:** com 8 perguntas, o estudo leva uns 30 minutos. **Cap. 3.**
- ⚠️ **D6.5 O par C não é perfeitamente equivalente:** C4 (recompra) é mais difícil que C3 (parcelas). **Cap. 5.**
- ✅ **D6.6 Tempo da tarefa:** vai do carregamento da ferramenta até o envio da resposta, e continua de onde estava se a pessoa reabrir a página. **Motivo:** a demora para carregar o Power BI não deve pesar contra o painel. **Cap. 3.**
- ✅ **D6.7 Métricas:**
  - **por pergunta:** tempo, resposta, acerto, confiança de 1 a 5, se conferiu, "os dados não permitem" ou "não consegui";
  - **só no Indaga:** número de consultas, se a última resposta da IA estava certa, se abriu o SQL;
  - **por ferramenta:** SUS;
  - **no fim:** preferência por tipo de pergunta e em qual confiou mais.

  **Cap. 3.**
- ✅ **D6.8 Tolerância para respostas digitadas:** a maior entre a tolerância do gabarito e 0,5% do valor. **Motivo:** os cartões do Power BI mostram valores abreviados ("6,11 Mi"). **Cap. 3.**
- ✅ **D6.9 Viés de automação:** a última resposta da IA estava errada, o participante respondeu errado e declarou confiança 4 ou 5. Segue Gu et al. (2024). **Cap. 3 e 5.**
- ✅ **D6.10 Limite de custo:** no máximo 8 consultas à IA por pergunta, aceitas só para a pergunta em andamento. Mais um limite de gasto no console da Anthropic. **Cap. 4.**
- ✅ **D6.11 Dados mínimos:** sem nome, e-mail ou documento. O participante é identificado por um código (P001...), e o piloto usa outro (T001...), que fica fora da análise. O termo avisa que as perguntas digitadas são processadas por um serviço de terceiros (Anthropic). **Cap. 3**, com a discussão de LGPD e ética.
- ✅ **D6.12 Hospedagem na Vercel** (12/10/2026; antes estava previsto o Render). O FastAPI roda como função serverless, com tempo máximo de 300 s (`vercel.json`) e Python 3.12. Cada push no `main` gera um deploy novo, então o `main` fica congelado durante a coleta. **Motivo:** preferência do autor e integração com o GitHub. **Cap. 4.**
- ✅ **D6.15 Link único para os participantes:** a raiz do site (https://tcc-undb.vercel.app) abre o estudo. A interface livre do Indaga fica em `/indaga`, protegida por senha (12/10/2026). **Motivo:** o participante não deve cair na ferramenta antes do termo e do sorteio do grupo. **Cap. 4.**
- ✅ **D6.16 Correção das respostas digitadas, revista depois do teste do autor** (12/10/2026, antes de qualquer participante real):
  - "M" passa a valer como milhão;
  - uma resposta sem unidade ("6.11") também é testada como mil e como milhão, e a correção fica `correto_escala_inferida`, contada como acerto mas identificável na análise;
  - "a informação não existe" numa pergunta que tem dado (tipos A a C) conta como `nao_respondeu`, e não como erro, porque a pessoa não chegou a um valor. No tipo C, no painel, essa é a resposta esperada.

  **Motivo:** o teste mostrou acertos marcados como erro (`6.11` em vez de "6,11 Mi") e a falta de uma distinção entre "o painel não responde" e "a pessoa errou". **Cap. 3.**
- ✅ **D6.17 Opções de resposta reescritas:** "A informação necessária não existe nos dados" e "Não consegui chegar à resposta nesta ferramenta". A tela também pede a unidade (Mi, mil, %). **Motivo:** separar a pergunta sem dado (tipo D) da falha da ferramenta ou da pessoa. **Cap. 3.**
- ✅ **D6.18 O teste do autor foi registrado como piloto** (T001). Ele entrou sem `?piloto=1` e foi reclassificado, para não desequilibrar o sorteio dos grupos. **Achado do piloto:** na B1, o painel levou a um erro real (R$ 2,19 Mi, que é SP no ano inteiro, contra R$ 1,46 Mi no 2º semestre). O filtro de semestre só existe na página Vendas. **Cap. 5** (exemplo qualitativo).
- ⚠️ **D6.19 Pergunta literal favorece o Indaga** (achado do teste do autor, 12/10/2026). Com o enunciado na tela, a tarefa no Indaga vira copiar e colar: o acerto do participante repetiu o da IA (4 de 4), e a formulação, que é a parte difícil da linguagem natural, ficou com o pesquisador. No painel, a pessoa precisa traduzir a pergunta em filtros. Além disso, sem erros da IA, o viés de automação não pode ser observado. **Proposta (P13):** enunciados como cenários de negócio, iguais para as duas ferramentas, em linguagem de gestor; perguntas escolhidas depois da Fase 5, priorizando as que a IA às vezes erra. **Cap. 3 e 5.**
- ✅ **D6.20 Enunciados do estudo como cenários de negócio** (12/10/2026). O participante vê uma situação com motivo de negócio, em linguagem de gestor e sem nomes internos ("beleza e saúde" em vez de `beleza_saude`), igual para as duas ferramentas. No Indaga, a instrução pede que ele escreva a pergunta com as próprias palavras. Os cenários estão em `config/estudo.json` (`cenarios`); o gabarito não muda. A Fase 5 continua com as perguntas literais. **Motivo:** D6.19. A Fase 5 mede a ferramenta com a pergunta bem formulada; a Fase 6 mede o humano no circuito, formulando, verificando e confiando. O piloto T001 foi feito com as perguntas literais. **Cap. 3.**
- ✅ **D6.21 Colar o cenário no Indaga é permitido e registrado** (12/10/2026). Colar um pedido de negócio no chat é o uso real do LLM; proibir tornaria o estudo menos realista. Mesmo colado, o cenário em linguagem de gestor obriga a IA a interpretar ("clientes paulistas" → SP; "segunda metade" → jul a dez; "clientes fiéis" → customer_unique_id com mais de um pedido). A análise marca cada tarefa como "colou" (primeira consulta com similaridade ≥ 0,8 com o cenário) ou "reformulou", e compara o acerto das duas estratégias. A assimetria com o painel, onde não há o que colar e a pessoa precisa traduzir a pergunta em filtros, é declarada como parte do fenômeno estudado: a diferença na barreira de entrada. **Cap. 3 e 5.**
- ⏳ **D6.13 Itens do SUS:** por enquanto é uma tradução de trabalho. **Ver P10.**
- ⏳ **D6.14 Termo de consentimento:** é um rascunho. **Ver P1 e P11.**

## Uso de IA no desenvolvimento

- ⚠️ **D9.1 Partes desenvolvidas com apoio de IA (Claude, Anthropic):**
  - o código do Indaga;
  - o projeto do dashboard;
  - os scripts de carga e de avaliação;
  - a página do estudo;
  - o rascunho do banco de perguntas.

  Precisa ser declarado conforme a política da UNDB. **Ver P4.** **Cap. 3** (ou uma seção de declaração).

- ✅ **D9.2 Repositório público** em https://github.com/ArivaldoFilho/tcc-undb (12/10/2026). Ficam fora do Git: `.env` (segredos), `dados/` (CSVs do Kaggle), o `.docx` do TCC (texto não publicado) e o `.pbix` (gerado a partir do PBIP). **Motivo:** reprodutibilidade, com o código, os SQLs, os gabaritos e os critérios abertos para a banca. **Cap. 3** (disponibilidade do material).

- ⚠️ **D9.3 Auditoria de 12/10/2026: risco de efeito teto.** No teste da Fase 5 (5 perguntas, 1 repetição), a IA acertou todas as perguntas corrigíveis automaticamente, inclusive a armadilha de customer_unique_id (B5), e respondeu bem à C1 e à D2. Se a IA acertar quase tudo, a matriz de decisão fica pobre e o viés de automação não aparece. **Mitigação:** perguntas-armadilha (D4.9). **Cap. 5.**
