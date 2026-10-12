# Dashboard Olist (Solução A)

Projeto Power BI no formato PBIP: o modelo semântico fica em TMDL
(`Olist.SemanticModel/`) e o relatório em PBIR (`Olist.Report/`). Os dois são
texto, então cada mudança aparece num diff. O `.pbix` é gerado a partir daqui.

## Abrir e gerar o .pbix

1. Abra `Olist.pbip` no Power BI Desktop.
2. Na primeira atualização, o Power BI pede a credencial do PostgreSQL:
   - **Tipo:** Banco de dados.
   - **Usuário:** `indaga_leitor.waakbkuksmzxgnxhuema`.
   - **Senha:** a mesma do `DATABASE_URL_LEITURA` no `.env`.
3. O Power BI também pede para aprovar cada consulta nativa (6 no total). Para
   não aprovar uma por uma, desmarque *Arquivo > Opções > Segurança > Exigir
   aprovação do usuário para novas consultas nativas de banco de dados*.
4. Clique em **Atualizar** e confira os números (seção abaixo).
5. Use *Arquivo > Salvar como*, escolha o tipo `.pbix` e salve como
   `Olist_AAAAMMDD.pbix`.

Se a conexão falhar com erro de certificado, abra *Arquivo > Opções e
configurações > Configurações da fonte de dados > Editar permissões* e
desmarque *Criptografar conexões*.

## Modelo de dados

Esquema estrela com três tabelas de fato, uma por grão, e quatro dimensões.

| Tabela | Grão | Linhas | Origem |
|---|---|---:|---|
| fItens | item de pedido | 112.650 | `sql/fItens.sql` |
| fPedidos | pedido | 99.441 | `sql/fPedidos.sql` |
| fAvaliacoes | avaliação | 99.224 | `sql/fAvaliacoes.sql` |
| dCliente | customer_id | 99.441 | `sql/dCliente.sql` |
| dProduto | produto | 32.951 | `sql/dProduto.sql` |
| dVendedor | vendedor | 3.095 | `sql/dVendedor.sql` |
| dCalendario | dia (2016 a 2018) | 1.096 | DAX |

- **Relacionamentos:** as três fatos se ligam a dCalendario, pela data da
  compra, e a dCliente. fItens também se liga a dProduto e a dVendedor. As
  fatos não se ligam entre si, porque juntar fatos de grãos diferentes
  multiplica linhas (Kimball Group).
- **Onde ficam as regras:** as definições de "pedido válido", "entregue",
  "atrasado" e "prazo" são calculadas no SQL de cada fato, com o mesmo texto
  de `config/descricoes.json`. As medidas DAX só somam, contam e dividem.
- **Medida `Pedidos`:** sem filtro de produto ou vendedor, ela conta os
  pedidos válidos de fPedidos. Com esses filtros, conta os pedidos válidos que
  têm itens do filtro em fItens. São 8 pedidos válidos sem nenhum item, por
  isso as duas contagens diferem no total.
- **Medidas que não reagem ao filtro de categoria:** entrega, atraso e nota.
  Por isso o segmentador de categoria só existe na página Vendas.

## Páginas

| Página | Segmentadores | Conteúdo |
|---|---|---|
| Visão geral | Ano, Mês, UF do cliente | Faturamento, pedidos, ticket médio, clientes únicos, nota média, % atrasados; faturamento por mês; faturamento por UF |
| Vendas | Ano, Semestre, Mês, UF do cliente, Categoria | Faturamento, pedidos, ticket médio, frete; faturamento por categoria (gráfico e tabela); faturamento por UF do vendedor |
| Entrega e satisfação | Ano, Mês, UF do cliente | Entregues, % atrasados, prazo médio, nota média, avaliações; atraso e nota por mês; prazo por UF; avaliações por nota |

## Conferência das medidas

Valores calculados em SQL direto no banco, sem filtros, em 12 out. 2026.
Depois de atualizar o Power BI, cada cartão precisa mostrar o mesmo valor.

| Medida | Valor de referência (SQL) | Power BI | OK |
|---|---:|---:|:-:|
| Faturamento | R$ 13.494.400,74 | R$ 13,49 Mi | ✅ |
| Faturamento, Ano = 2017 | R$ 6.108.492,27 | | |
| Pedidos | 98.207 | 98 Mil | ✅ |
| Ticket médio | R$ 137,41 | R$ 137,41 | ✅ |
| Frete | R$ 2.241.126,29 | | |
| Clientes únicos | 94.990 | 95 Mil | ✅ |
| Pedidos entregues | 96.476 | | |
| Pedidos atrasados | 7.827 | | |
| % pedidos atrasados | 8,1% | 8,1% | ✅ |
| Prazo médio de entrega (dias) | 12,5 | | |
| Nota média | 4,09 | 4,09 | ✅ |
| Avaliações | 99.224 | | |

## Registro de esforço (Fase 2)

| Etapa | Horas | Observação |
|---|---:|---|
| Briefing de KPIs | | |
| Modelagem (SQL das fatos e dimensões, relacionamentos) | | |
| Medidas DAX e conferência | | |
| Visual (páginas, layout, formatação) | | |

## Congelamento

Depois de conferir as medidas e fazer os ajustes visuais:

1. Salve `Olist_AAAAMMDD.pbix` e anote a data aqui.
2. A partir daí, não altere nem o `.pbix` nem esta pasta. O banco de perguntas
   (Fase 4) só começa depois do congelamento.

Congelado em: ____/____/______
