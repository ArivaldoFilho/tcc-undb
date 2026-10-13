# Decisões do projeto

Registro vivo das decisões técnicas e metodológicas, para usar na escrita do
TCC. Cada item diz o que foi decidido, por quê e em que capítulo entra.
Atualizado a cada decisão nova; as mais recentes ficam no fim de cada seção.
O fluxo vigente de coleta está em [AVALIACAO.md](AVALIACAO.md).

**Legenda:** ✅ decidido · ⏳ pendente · ⚠️ ameaça à validade ou limitação, que vai para o cap. 5 ou 6

---

## Pendências abertas

| # | Pendência | Com quem | Desde |
|---|---|---|---|
| P1 | O questionário precisa de aprovação do CEP (Plataforma Brasil) ou é dispensado? | Orientador e coordenação | 12/10/2026 |
| P5 | Remover o segmentador de Semestre do dashboard antes de congelar (ver D2.6)? | Autor | 12/10/2026 |
| P6 | Congelar o dashboard e registrar a data | Autor | 12/10/2026 |
| P8 | Conferência dos gabaritos das 20 perguntas pelo orientador | Orientador | 12/10/2026 |
| P9 | Conferir a licença da base Olist no Kaggle | Autor | 12/10/2026 |
| P12 | Como o Power BI foi conectado ao Supabase: certificado raiz instalado ou criptografia desligada? | Autor | 12/10/2026 |
| P16 | Teto de gasto na chave da API (console da Anthropic, Settings > Limits) | Autor | 12/10/2026 |
| P17 | Conferência das medidas: a Visão geral confere com o SQL; faltam os cartões de Vendas e de Entrega e satisfação | Autor | 12/10/2026 |
| P18 | Escolher o segundo avaliador (A5) e o segundo classificador (C3) | Autor e orientador | 13/10/2026 |
| P19 | Congelar a configuração do Indaga e anotar o `config_hash` (hoje `0bf3b7d7bed6b8ac`) | Autor | 13/10/2026 |
| P20 | Montar o formulário com o termo de consentimento; registrar a data de abertura e os canais de divulgação | Autor e orientador | 13/10/2026 |
| P21 | Apagar do Supabase as tabelas do estudo descontinuado (`indaga.estudo_*`) e as 4 execuções de teste com `origem = 'estudo'`? | Autor | 13/10/2026 |

---

## Fase 1: Base de dados

- ✅ **D1.1 Base:** *Brazilian E-Commerce Public Dataset by Olist* (Kaggle), com 9 tabelas relacionadas. **Motivo:** uma base com várias tabelas evita favorecer a IA, como uma tabela única faria. **Cap. 3.**
- ✅ **D1.2 Banco:** PostgreSQL 17 no Supabase (região us-east-1), um único banco para as duas soluções. **Cap. 3 e 4.**
- ✅ **D1.3 Sem limpeza:** os CSVs foram carregados como estão, com conferência de cabeçalho e de tipos antes da carga. Nenhum valor foi alterado ou removido. **Cap. 4.**
- ✅ **D1.4 Linhas por tabela** (carga de 12/10/2026, conferida em `avaliacao/resultados/contagem_antes.csv`): customers 99.441 · sellers 3.095 · products 32.951 · product_category_name_translation 71 · orders 99.441 · order_items 112.650 · order_payments 103.886 · order_reviews 99.224 · geolocation 1.000.163. **Cap. 3.**
- ✅ **D1.5 Chaves:** 8 tabelas com chave primária. Em `order_reviews`, a chave é o par (review_id, order_id), porque review_id se repete 814 vezes e o par não se repete. `geolocation` ficou sem chave primária, porque o prefixo de CEP se repete. As 6 chaves estrangeiras foram criadas sem nenhuma violação. **Cap. 4.**
- ✅ **D1.6 Peculiaridades da base**, que entram na descrição:
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

- ✅ **D2.1 O dashboard foi construído pelo autor** como projeto PBIP. As horas de construção dependem da experiência de quem constrói e não servem como medida de esforço; por isso o esforço é medido como esforço de adaptação (D10.6). **Cap. 3 e 5.**
- ✅ **D2.2 Modelo em estrela:**
  - 3 fatos, uma por grão: fItens (item), fPedidos (pedido) e fAvaliacoes (avaliação);
  - 4 dimensões: dCalendario, dCliente, dProduto e dVendedor;
  - as fatos não se ligam entre si.

  **Motivo:** juntar fatos de grãos diferentes produz resultados incorretos (Kimball Group, [2013?]). **Cap. 4.**
- ✅ **D2.3 As regras de negócio ficam no SQL de cada fato** ("pedido válido", "entregue", "atrasado" e "prazo"). As medidas DAX só somam, contam e dividem. Os SQLs estão em `dashboard/sql/`. **Cap. 4.**
- ✅ **D2.4 Medida "Pedidos" com dois caminhos:** sem filtro de produto ou vendedor, ela conta os pedidos de fPedidos; com esse filtro, conta os de fItens. **Motivo:** fazer o ticket médio por categoria funcionar. Por causa dos 8 pedidos sem item (D1.6), as duas contagens diferem no total. **Cap. 4.**
- ✅ **D2.5 O segmentador de categoria só existe na página Vendas.** **Motivo:** entrega, atraso e nota não reagem ao filtro de produto. **Cap. 4.**
- ⚠️ **D2.6 Viés na construção:** o dashboard foi montado depois de existirem 6 perguntas de exemplo, e o segmentador de Semestre coincide com a pergunta B1. **Ver P5.** **Cap. 5** (validade interna).
- ✅ **D2.7 Modo de importação**, com 3 páginas: Visão geral, Vendas e Entrega e satisfação. A conferência das medidas contra o SQL está em `dashboard/README.md`. **Cap. 4.**
- ✅ **D2.8 Publicação pelo "Publicar na Web" do Power BI.** O link é público, o que não é problema porque a base é pública. **Motivo:** dar acesso ao painel congelado sem instalar o Power BI. **Cap. 4.**
- ✅ **D2.9 Navegação lateral** (12/10/2026, antes do congelamento): um Navegador de página vertical na coluna esquerda de cada página (as páginas passaram de 1280 para 1420 px de largura). **Motivo:** no "Publicar na Web", as abas de página ficam pouco visíveis no rodapé. **Cap. 4.**

## Fase 3: Indaga (Solução B)

Escolhas de base (ver `README.md`):
- modelo `claude-opus-5-5` com esforço `medium`;
- temperatura não enviada;
- sem cache, sem few-shot e sem fallback de modelo;
- sem retry automático do SDK, com uma nova tentativa explícita no `rodar.py` (D10.3);
- esquema inteiro no prompt;
- `config_hash` gravado em cada execução.

**Cap. 4.**

- ✅ **D3.1 O que o modelo recebe:** na decisão e na geração do SQL, só a estrutura, as descrições e as definições, sem nenhuma linha de dados. Na explicação, até 50 linhas do resultado. **Cap. 4**, com a discussão de LGPD.
- ✅ **D3.2 Três barreiras de segurança:** um guardrail que aceita só um SELECT, a transação read-only e o usuário sem permissão de escrita. **Cap. 4.**
- ✅ **D3.3 Indaga público** em https://tcc-undb.vercel.app (FastAPI na Vercel, tempo máximo de 300 s, Python 3.12), com senha e um teto de 100 consultas a cada 24 h (`INDAGA_LIMITE_DIARIO`). Cada push no `main` gera um deploy novo, então o `main` fica congelado durante a coleta. **Cap. 4.**

## Fase 4: Banco de perguntas

- ✅ **D4.1 Os tipos são definidos em relação ao dashboard congelado**, e não pela dificuldade da pergunta:
  - **A:** um visual responde, com no máximo um segmentador;
  - **B:** o painel responde, mas com 2 ou mais filtros;
  - **C:** nenhum visual responde;
  - **D:** o dado não existe na base, ou a pergunta é ambígua.

  "Exploratória" equivale aos tipos B e C. **Motivo:** a banca simulada pediu uma definição operacional. **Cap. 3.**
- ✅ **D4.2 26 perguntas candidatas** (6 A, 6 B, 7 C e 7 D), com gabarito em SQL rodado no banco em 12/10/2026. **Ver P8.** **Cap. 3 e apêndice.**
- ✅ **D4.3 Critérios de acerto**, definidos antes da coleta: numero, percentual, lista, recusa e rubrica. **Tolerâncias:**
  - 0,01 em valores em reais e em médias;
  - 0,05 dia no prazo;
  - 0,1 ponto percentual nos percentuais;
  - zero nas contagens.

  **Cap. 3.**
- ✅ **D4.4 Critério "percentual" criado** em 12/10/2026, antes de qualquer coleta. Ele aceita a resposta em pontos (6,63) ou em fração (0,0663). **Motivo:** as duas formas estão certas, e o critério "numero" marcaria a fração como erro. **Cap. 3.**
- ✅ **D4.5 Perguntas sensíveis às definições,** para separar quem segue as definições de quem não segue:
  - **A2:** contar os cancelados dá 54.011 pedidos, contra 53.532 pela definição;
  - **B5:** contar customer_id dá 23.599 clientes, contra 23.051 por customer_unique_id.

  **Cap. 5** (discussão dos erros).
- ⚠️ **D4.6 O mesmo agente (o autor) construiu as duas soluções e escreveu as perguntas.** A revisão dos gabaritos pelo orientador (P8) e as perguntas escritas pelos participantes (Frente C) atenuam isso. **Cap. 5** (validade interna).
- ✅ **D4.7 Versão do dashboard usada na classificação:** hash `650a8b665c17` dos arquivos de `dashboard/`, anterior à navegação lateral (D2.9), que não muda o que o painel responde. Registrar o hash final no congelamento (P6). **Cap. 3.**
- ✅ **D4.8 Critério "recusa" com revisão manual** (12/10/2026, auditoria antes da coleta). Se a IA recusa (sem_dados ou esclarecimento), a resposta conta como correta. Se a IA executa o SQL e escreve a explicação, a resposta vai para revisão, e não para incorreto. **Motivo:** no teste, a D2 ("Quanto vendemos ontem?") devolveu R$ 0,00, mas a explicação dizia que a base termina em 2018 e que a pergunta não pode ser respondida. Essa é a resposta desejada. **Cap. 3.**
- ✅ **D4.9 Seis perguntas-armadilha** (B7, B8, C8, C9, C10, C11; 12/10/2026): qualidade de dados, conhecimento de domínio, fan trap, mudança de definição, várias etapas e granularidade. Não foram testadas na IA antes de entrar. **Motivo:** reduzir o risco de efeito teto (D9.3) sem viés de seleção; cada uma se justifica pela literatura (Kimball Group, [2013?]; Liu et al., 2025; Li et al., 2023) e pelo realismo. **Cap. 3.**
- ✅ **D4.10 Seleção final de 20 perguntas:** A1, A2, A5, A6 | B1, B3, B4, B5, B7, B8 | C1, C3, C4, C8, C9, C11 | D1, D2, D3, D5. Critérios: pelo menos 4 por tipo; mais B e C porque são os tipos exploratórios; evitar repetição e perguntas adivinháveis; limitar a correção manual. As 32 candidatas ficam em `avaliacao/perguntas_candidatas.csv`. **Cap. 3 e apêndice.**
- ✅ **D4.11 Rubricas das perguntas do tipo D** escritas na coluna `observacao` (13/10/2026). D1, D2 e D3: correto se a IA avisar que o dado não existe (custo, vendas depois de 2018, metas) sem inventar um valor; D5: correto se pedir esclarecimento ou declarar o critério adotado. **Cap. 3.**

## Fase 6 (descontinuada): estudo interativo online

Entre 12 e 13/10/2026 foi construída uma página de estudo na Vercel, em que o
participante usava as duas ferramentas embutidas, com 4 grupos
contrabalanceados, SUS e medida de viés de automação. Foi **substituída** pelo
questionário e pelas perguntas dos participantes (D10.1). O código saiu do
repositório e continua no histórico do Git. Duas lições ficam:

- ⚠️ **D6.19 Pergunta pronta favorece a IA.** Com o enunciado na tela, a tarefa no Indaga virou copiar e colar: o acerto do participante repetiu o da IA, e a formulação, que é a parte difícil da linguagem natural, ficou com o pesquisador. **Consequência no fluxo novo:** as perguntas dos participantes são rodadas com o texto literal, sem reescrita (D10.8). **Cap. 3.**
- ✅ **D6.18 Achado qualitativo do teste do autor:** na B1, o painel levou a um erro real (R$ 2,19 Mi, que é SP no ano inteiro, contra R$ 1,46 Mi no 2º semestre), porque o filtro de semestre só existe na página Vendas. **Cap. 5** (exemplo).

## Fluxo de coleta (13/10/2026)

- ✅ **D10.1 Quatro frentes:** A, avaliação técnica com as 20 perguntas do banco; B, questionário; C, perguntas escritas pelos participantes; D, consolidação. A e B correm em paralelo; C começa depois do fechamento do formulário. **Motivo:** substituir o estudo interativo por uma coleta mais simples para participantes de fora, e trazer perguntas reais, formuladas por quem usa dados, para a avaliação. **Cap. 3.**
- ✅ **D10.2 Congelamento:** a configuração do Indaga (modelo, prompts, descrições, `config_hash`) e o painel ficam congelados do início da Frente A até o fim da Frente C. Mudança feita depois de ver resultados vai para este registro, com data e motivo. **Cap. 3.**
- ✅ **D10.3 Falha de API:** uma nova tentativa, feita e registrada pelo `rodar.py`. Se falhar de novo, a execução vira **erro de execução**, fora da taxa de acerto, e não conta como resposta errada. Cada execução registra a data e o identificador do modelo devolvido pela API. **Cap. 3.**
- ✅ **D10.4 Unidade avaliada** (descrição revista em D10.12)**:** a resposta final que o usuário lê (resultado e explicação), e não só o SQL. Explicações com números que não aparecem no resultado vão para revisão, e os casos de resultado certo com texto errado são contados à parte (`explicacao_errada`). **Cap. 3.**
- ✅ **D10.5 Revisão manual com dois avaliadores:** os erros (para reconferir o gabarito antes de contar o erro), as recusas e as rubricas são julgados pelo autor e por um segundo avaliador, cada um sem ver o outro. Consenso no veredito final; concordância medida pelo percentual e pelo kappa de Cohen (`avaliacao/concordancia.py`). Correção de gabarito entra neste registro. **Ver P18.** **Cap. 3.**
- ✅ **D10.6 Esforço de adaptação do painel** numa escala de 0 a 3: 0, nenhuma mudança; 1, nova medida DAX; 2, novo visual; 3, mudança no modelo de dados. **Motivo:** as horas de construção não valem como medida (D2.1); o que a pergunta exigiria do painel é mais defensável e liga-se à "origem das perguntas" do Quadro 2. **Cap. 3.**
- ✅ **D10.7 Integridade da base:** contagem de linhas antes e depois da coleta (`scripts/contar_linhas.py`); as duas precisam ser iguais. A contagem de antes foi registrada em 13/10/2026. **Cap. 3.**
- ✅ **D10.8 Perguntas dos participantes:** até 3 por pessoa, extraídas do questionário. A triagem junta duplicadas, mantém as que a base não responde (tipo D) e descarta só as incompreensíveis ou fora do tema, com o motivo registrado. A classificação nos tipos A a D é feita pelo autor e por um segundo classificador, com a concordância medida. As perguntas são rodadas no Indaga **com o texto literal**, 3 vezes cada, com o mesmo `config_hash` da Frente A. **Motivo:** medir o uso real (D6.19). **Cap. 3.**
- ✅ **D10.9 Questionário:** meta de pelo menos 20 respostas, idealmente 30, em canais variados (gestores e profissionais de dados, não só colegas de curso). O CSV original fica intacto e fora do Git (`dados/questionario/`); a limpeza é feita numa cópia, com cada exclusão registrada. **Ver P1 e P20.** **Cap. 3.**
- ✅ **D10.10 Matriz de decisão** por tipo de pergunta (`avaliacao/matriz.py`), apresentada separada e junta para as perguntas do banco e as dos participantes, cruzada com o questionário, e com a lista dos resultados que contrariam a hipótese. Logs, CSVs e o `config_hash` ficam no repositório (`avaliacao/resultados/`). **Cap. 5.**
- ✅ **D10.11 Coluna `coberta_pela_documentacao`** em `perguntas.csv` (13/10/2026, antes da coleta): "sim" quando tudo o que a pergunta exige está escrito em `config/descricoes.json` (definições, descrições de colunas e observações); "nao" quando acertar exige conhecimento ou inferência fora dela. Nas 20 perguntas, ficaram "nao" a B7 (a base não documenta que set. e out. de 2018 estão praticamente vazios), a B8 (a base não tem região; é preciso saber as UFs do Nordeste), a D2 (a data final da base não está documentada) e a D5 (a documentação não define "melhor cliente"). As outras 16 são "sim"; a C8 e a C11, por exemplo, têm a armadilha descrita nas observações. A matriz (`matriz.py`) separa os resultados por essa coluna, e as perguntas dos participantes recebem a mesma classificação (C3). **Motivo:** o Indaga recebe uma camada semântica escrita pelo autor, que já conhece as perguntas; sem essa separação, um acerto alto pode refletir a documentação, e não a capacidade do modelo. **Ver P8** (a classificação é conferida junto com os gabaritos). **Cap. 3 e 5.**
- ✅ **D10.12 Unidade de correção e amostra dos acertos automáticos** (13/10/2026, antes da coleta). A unidade de correção é a execução (uma pergunta numa repetição), e o veredito é sobre a resposta que o usuário recebe, resultado e explicação. A descrição de D10.4 foi ajustada porque a correção automática compara só o resultado com o gabarito; a explicação só era olhada nas recusas, nas rubricas e quando citava números fora do resultado. Por isso, entra na revisão manual uma amostra dos acertos automáticos: uma execução por pergunta, sorteada com semente fixa (o nome da rodada), julgada pelos dois avaliadores como os demais casos. **Motivo:** estimar os falsos positivos do critério automático (resultado certo pela razão errada, ou explicação errada), que de outro modo ficariam invisíveis; a taxa de reversão na amostra vai para a discussão da validade da medida. **Cap. 3 e 5.**

## Repositório e auditoria

- ✅ **D9.2 Repositório público** em https://github.com/ArivaldoFilho/tcc-undb (12/10/2026). Ficam fora do Git: `.env` (segredos), `dados/` (CSVs do Kaggle e respostas do questionário), o `.docx` do TCC (texto não publicado) e o `.pbix` (gerado a partir do PBIP). **Motivo:** reprodutibilidade, com o código, os SQLs, os gabaritos, os critérios e os resultados abertos para a banca. **Cap. 3** (disponibilidade do material).
- ⚠️ **D9.3 Auditoria de 12/10/2026: risco de efeito teto.** No teste com 5 perguntas, a IA acertou todas as corrigíveis automaticamente. Se a IA acertar quase tudo, a matriz de decisão fica pobre. **Mitigação:** perguntas-armadilha (D4.9) e perguntas reais dos participantes (D10.8). **Cap. 5.**
