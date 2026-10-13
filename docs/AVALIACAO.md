# Projeto de avaliação

Este documento explica como o TCC compara as duas formas de análise de dados:
o que é medido, como, com quais perguntas e por que o desenho é este. As
decisões estão detalhadas, com os motivos, em [DECISOES.md](DECISOES.md); o
guia operacional do estudo com usuários está em [ESTUDO.md](ESTUDO.md).

## 1. O que se quer descobrir

**Pergunta de pesquisa:** em quais cenários a análise feita por IA generativa
em linguagem natural pode substituir ou complementar a análise em dashboards
de BI?

**Hipótese:** a IA responde melhor a perguntas exploratórias, e o dashboard é
mais confiável para indicadores recorrentes. Para que a hipótese possa ser
testada, os dois termos foram definidos de forma operacional:

- **exploratória** = perguntas dos tipos B e C (seção 3);
- **confiável** = acerto em relação ao gabarito e consistência entre
  repetições.

**Produto final:** uma matriz de decisão que cruza os tipos de pergunta com as
dimensões de comparação (acerto, tempo, reprodutibilidade, custo, esforço e
confiança) e indica quando usar cada abordagem.

## 2. As duas soluções avaliadas

| | Solução A: dashboard | Solução B: Indaga |
|---|---|---|
| O que é | Painel no Power BI com 3 páginas (Visão geral, Vendas, Entrega e satisfação) | Sistema em que um LLM (`claude-opus-5-5`) transforma a pergunta em SQL, executa e explica o resultado |
| Como o usuário pergunta | Escolhendo página, filtros e visuais | Escrevendo em português |
| Dados | Base Olist no PostgreSQL (Supabase) | A mesma base, o mesmo banco |
| Definições de métrica | As de `config/descricoes.json`, reproduzidas em DAX | As mesmas, enviadas ao modelo no prompt |

As duas soluções usam **o mesmo banco e as mesmas definições**, por exemplo
de "pedido válido", "faturamento" e "prazo de entrega". Sem isso, a
comparação mediria definições diferentes, e não abordagens diferentes.

## 3. O banco de perguntas

### Tipos de pergunta

O tipo de cada pergunta é definido **em relação ao dashboard congelado**, e
não pela dificuldade da pergunta:

| Tipo | Critério | Exemplo |
|---|---|---|
| A. Prevista | Um único visual do painel responde, com no máximo um filtro | Qual foi o faturamento total de 2017? |
| B. Variação | O painel responde, mas exige dois ou mais filtros combinados | Faturamento com clientes de SP no 2º semestre de 2017 |
| C. Não prevista | Nenhum visual do painel responde | Quantos clientes compraram mais de uma vez? |
| D. Sem resposta ou ambígua | A base não tem o dado, ou a pergunta admite mais de uma leitura | Qual foi o lucro líquido de 2017? |

### Seleção

Foram escritas 32 perguntas candidatas, das quais 20 foram selecionadas:
4 do tipo A, 6 do B, 6 do C e 4 do D. Os tipos B e C têm mais perguntas
porque são os exploratórios da hipótese.

Seis das 20 são **armadilhas**: perguntas realistas com uma dificuldade
conhecida na literatura, como a junção de tabelas que multiplica linhas (fan
trap), o conhecimento de domínio ("Nordeste"), a mudança de definição
("ticket com frete") e os dados incompletos no fim do período. Elas existem
para evitar o efeito teto, isto é, a IA acertar tudo porque as perguntas são
fáceis demais. **Nenhuma foi testada na IA antes de entrar no banco:**
escolher perguntas porque a IA erra nelas seria um viés de seleção.

### Gabaritos e critérios de acerto

Cada pergunta tem um gabarito em SQL, executado no banco, e um critério de
acerto definido **antes** da coleta:

| Critério | Quando a resposta é correta |
|---|---|
| numero | Uma linha, com um valor igual ao gabarito dentro da tolerância |
| percentual | Como numero; aceita a resposta em pontos (6,63) ou em fração (0,0663) |
| lista | O mesmo conjunto de itens do gabarito, em qualquer ordem |
| recusa | A IA avisa que o dado não existe; se executou SQL e explicou na narrativa, uma pessoa julga |
| rubrica | Correção manual, por um texto de critério escrito com a pergunta |

**Tolerâncias:** 0,01 em reais e em médias, 0,05 dia no prazo, 0,1 ponto
percentual nos percentuais e zero nas contagens.

Os gabaritos ainda serão conferidos pelo orientador, e as perguntas do tipo C
serão revisadas por uma pessoa de fora.

## 4. Visão geral da avaliação

A avaliação tem duas partes complementares, que respondem a perguntas
diferentes:

| | Fase 5: avaliação técnica | Fase 6: estudo com usuários |
|---|---|---|
| Pergunta que responde | Quão bem cada ferramenta responde, por si só? | O que acontece quando uma pessoa usa cada ferramenta? |
| Quem participa | Ninguém: o sistema roda sozinho, e o autor responde no painel | 10 a 20 pessoas, pela internet |
| Perguntas | As 20 do banco, com o enunciado literal | 8 do banco, apresentadas como cenários de negócio |
| Principais medidas | Acerto, consistência, tempo, custo | Acerto, tempo, confiança, viés de automação, usabilidade |
| Reprodutível | Sim, totalmente | Não: depende das pessoas |

A Fase 5, sozinha, já sustenta a matriz de decisão (é a versão mínima do
TCC). A Fase 6 acrescenta o lado humano: formular a pergunta, verificar a
resposta e confiar nela.

## 5. Fase 5: avaliação técnica

### Indaga

1. Cada uma das 20 perguntas é feita **5 vezes** ao Indaga. As repetições são
   intercaladas (todas as perguntas na rodada 1, depois todas na 2...), para
   que uma instabilidade momentânea da API não caia toda sobre a mesma
   pergunta.
2. Cada execução é gravada no banco com o SQL gerado, o resultado, a
   explicação, o tempo de cada etapa, os tokens, o custo e o `config_hash`.
   O `config_hash` identifica a configuração exata (modelo, esforço, prompts,
   descrições do esquema) e prova que ela não mudou durante a coleta.
3. O script de correção compara cada resultado com o gabarito, pelo critério
   da pergunta.

**Medidas por pergunta:**
- **taxa de acerto** nas 5 repetições;
- **consistência:** a fração das repetições que chegou ao mesmo resultado. É
  a medida da reprodutibilidade, porque o LLM não é determinístico;
- **número de SQLs diferentes** gerados para a mesma pergunta;
- **tempo** mediano e máximo, e **custo** médio por resposta;
- **números citados na explicação que não aparecem no resultado**, separados
  para revisão manual. Servem para detectar alucinação na etapa de texto,
  mesmo quando o SQL está certo.

### Dashboard

O autor responde às mesmas 20 perguntas no painel e registra, em
`avaliacao/dashboard.csv`:
- se o painel responde (sim, parcial ou não);
- quantos passos (filtros e cliques) foram necessários;
- o valor lido;
- o que seria preciso mudar no painel para responder às perguntas que ele não
  responde (nova medida, novo visual ou mudança no modelo). Essa é a medida de
  **esforço de adaptação**, que substitui as horas de construção, já que as
  duas soluções foram construídas com apoio de IA.

**Custo estimado da Fase 5:** cerca de US$ 4 a 5 (100 execuções a cerca de
US$ 0,04 cada, conforme o teste de auditoria).

## 6. Fase 6: estudo com usuários

### Como funciona para o participante

O participante recebe um único link (https://tcc-undb.vercel.app) e faz tudo
pelo navegador, em cerca de 30 minutos:

1. lê e aceita o termo de consentimento;
2. responde a um perfil curto, sem dados que o identifiquem;
3. resolve 4 tarefas com uma das ferramentas, que aparece embutida na página,
   e responde ao questionário de usabilidade (SUS) sobre ela;
4. resolve outras 4 tarefas com a outra ferramenta e responde ao SUS dela;
5. diz qual ferramenta prefere para cada tipo de pergunta, em qual confiou
   mais, e deixa comentários.

### Desenho

- **Intrassujeito com contrabalanceamento:** cada pessoa usa as duas
  ferramentas. Quatro grupos cruzam a ordem das ferramentas com o conjunto de
  perguntas; cada participante novo entra no grupo menos preenchido.

  | Grupo | Primeira parte | Segunda parte |
  |---|---|---|
  | 0 | Painel com o conjunto X | Indaga com o conjunto Y |
  | 1 | Indaga com X | Painel com Y |
  | 2 | Painel com Y | Indaga com X |
  | 3 | Indaga com Y | Painel com X |

- **Conjuntos equivalentes:** X e Y têm uma pergunta de cada tipo, em pares
  (A1/A2, B1/B4, C4/C3, D1/D3).
- **Cenários de negócio, e não perguntas prontas.** O participante vê uma
  situação, por exemplo: "O marketing quer avaliar a Black Friday da categoria
  de beleza e saúde, em novembro de 2017. Quanto essa categoria faturou
  naquele mês?". No painel, ele precisa traduzir a situação em filtros; no
  Indaga, precisa escrever a pergunta. Se a pergunta aparecesse pronta, a
  tarefa no Indaga viraria copiar e colar, e o estudo mediria de novo só a IA.
- **Colar o cenário é permitido.** É o uso real de um LLM. A análise registra
  se a pessoa colou ou reformulou, e compara o acerto das duas estratégias.

### O que é medido

| Nível | Medidas |
|---|---|
| Cada tarefa | tempo (a partir do carregamento da ferramenta); resposta; acerto; confiança de 1 a 5; se a pessoa conferiu a resposta; "a informação não existe nos dados" ou "não consegui" |
| Cada tarefa no Indaga | número de consultas; se colou ou reformulou; se a resposta da IA estava certa; se a pessoa abriu o SQL |
| Cada ferramenta | nota SUS (0 a 100) |
| Cada participante | perfil; preferência por tipo de pergunta; em qual ferramenta confiou mais |

**Medida-chave: viés de automação.** Conta quantas vezes a IA errou, o
participante aceitou a resposta errada e declarou confiança 4 ou 5. É a
medida que liga o estudo a Gu et al. (2024), segundo os quais até
especialistas aceitam análises erradas feitas por IA.

### Correção das respostas digitadas

A resposta digitada é comparada ao gabarito com a maior entre a tolerância
da pergunta e 0,5% do valor, porque os cartões do Power BI mostram valores
abreviados ("R$ 6,11 Mi"). A correção tem quatro resultados possíveis:

- **correto:** o valor bate com o gabarito;
- **correto_escala_inferida:** a pessoa omitiu a unidade ("6.11"), mas o valor
  bate quando lido como mil ou milhão. Conta como acerto e fica identificado;
- **nao_respondeu:** a pessoa marcou "não consegui" ou disse que a informação
  não existe numa pergunta que tem dado. No tipo C, no painel, essa é a
  resposta esperada;
- **incorreto:** qualquer outro valor.

## 7. Da coleta à matriz de decisão

Os resultados das duas fases são cruzados por tipo de pergunta. O formato
esperado (exemplo de formato, **não** de resultado):

| Tipo | Acerto IA | Acerto painel | Consistência IA | Tempo IA x painel | Viés de automação | Indicação |
|---|---|---|---|---|---|---|
| A | ...% | ...% | ...% | ... | ... | ... |
| B | ... | ... | ... | ... | ... | ... |
| C | ... | painel não responde | ... | ... | ... | ... |
| D | recusou em ...% | ... | ... | ... | ... | ... |

**Análise estatística:**
- estatística descritiva por ferramenta e por tipo;
- na Fase 6, teste de Wilcoxon pareado (acertos, tempo e SUS de cada
  participante nas duas ferramentas), se a amostra permitir;
- categorização dos comentários abertos.

Os resultados que contrariarem a hipótese também entram na discussão.

## 8. Como a validade foi protegida

| Risco | Proteção |
|---|---|
| Comparar definições, e não abordagens | Uma camada de métricas única para as duas soluções |
| Ajustar uma solução às perguntas | Dashboard congelado antes do banco de perguntas; configuração do Indaga congelada e comprovada pelo `config_hash` |
| Mudar o critério depois de ver os resultados | Critérios e tolerâncias definidos antes da coleta; mudanças posteriores registradas com data e motivo |
| Escolher perguntas que favoreçam um lado | Armadilhas justificadas pela literatura, sem teste prévio na IA; revisão dos gabaritos pelo orientador e por uma pessoa de fora |
| Não determinismo do LLM | 5 repetições por pergunta, com medida de consistência |
| Efeito de ordem e de aprendizado no estudo | 4 grupos contrabalanceados e conjuntos diferentes por ferramenta |
| Painel prejudicado pela interface web | Botões de navegação entre páginas; tempo medido a partir do carregamento |
| Dados do piloto misturados com os reais | Participantes do piloto com códigos próprios (T001...), fora da análise |

## 9. Limitações conhecidas

- **Uma base, um modelo, uma língua:** os resultados valem para este cenário
  (validade externa).
- **O mesmo autor**, com apoio de IA, construiu as duas soluções e escreveu as
  perguntas (validade interna).
- **Amostra pequena e coleta online:** sem observação direta; "conferiu a
  resposta" é declarado pela pessoa; o ambiente de cada participante varia.
- **Cliques no painel não são registrados,** porque o painel embutido é uma
  página da Microsoft.
- **O par C do estudo não é perfeitamente equivalente:** C4 (recompra) é mais
  difícil que C3 (parcelas).
- **Período efetivo da base:** de jan. 2017 a ago. 2018. 2016 e o fim de 2018
  têm poucos pedidos.

## 10. Situação atual

| Etapa | Situação |
|---|---|
| Base de dados | Pronta |
| Dashboard | Publicado; falta conferir os cartões das páginas Vendas e Entrega e congelar |
| Indaga | Pronto, local e na Vercel, com a mesma configuração |
| Banco de perguntas | 20 perguntas selecionadas; falta a revisão do orientador |
| Fase 5 | Testada com 5 perguntas; falta a rodada completa, depois do congelamento |
| Fase 6 | No ar e testada; falta definir o CEP, completar o termo, fazer o piloto e escolher as perguntas pelo resultado da Fase 5 |

## 11. Onde está cada coisa

| Arquivo | Conteúdo |
|---|---|
| `avaliacao/perguntas.csv` | As 20 perguntas finais, com gabarito e critério |
| `avaliacao/perguntas_candidatas.csv` | As 32 candidatas |
| `avaliacao/dashboard.csv` | Ficha da avaliação no painel |
| `avaliacao/BANCO_DE_PERGUNTAS.md` | Critérios, tolerâncias, armadilhas e gabaritos |
| `avaliacao/rodar.py`, `avaliacao/corrigir.py` | Execução e correção da Fase 5 |
| `avaliacao/analisar_estudo.py` | Correção e resumo da Fase 6 |
| `config/descricoes.json` | Definições de métrica compartilhadas |
| `config/estudo.json` | Conjuntos, cenários e termo do estudo |
| `static/estudo.html` | Página do estudo |
| `dashboard/` | Projeto do Power BI e o SQL do modelo |
| `docs/DECISOES.md` | Todas as decisões, com data, motivo e capítulo do TCC |
