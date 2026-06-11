# Documentação das Consultas SQL - Dashboard OunceAI

Este documento descreve as consultas SQL utilizadas para alimentar o painel de controle (dashboard) do OunceAI, mapeando os dados do banco `ounceai_db` para as seções da interface.

Todas as consultas estão implementadas em `app/routes/analytics.py` e utilizam *parameterized queries* (consultas parametrizadas com `%s`) do `psycopg2` para prevenir ataques de Injeção SQL (SQL Injection). O sistema também conta com um mecanismo de cache em memória que armazena os resultados por 5 minutos, garantindo um tempo de resposta inferior a 2 segundos (atualmente ~0.0058s em testes locais).

## 1. Filtros Globais do Dashboard

Alimenta os menus suspensos (dropdowns) de Categorias e Gôndolas no cabeçalho do Dashboard.

**Consulta SQL (Categorias):**
```sql
SELECT DISTINCT categoria FROM dim_produto WHERE categoria IS NOT NULL ORDER BY categoria
```
- **Tabela:** `dim_produto`
- **Campos:** `categoria`

**Consulta SQL (Gôndolas):**
```sql
SELECT DISTINCT id_prateleira FROM dim_hardware ORDER BY id_prateleira
```
- **Tabela:** `dim_hardware`
- **Campos:** `id_prateleira`

## 2. Indicadores Chave de Desempenho (KPIs)

Alimenta os cartões principais no topo da página: Receita Protegida, Valor Total em Estoque, Divergências Fantasmas e Acurácia Geral da IA.

**Consulta SQL:**
```sql
SELECT 
    SUM(f.receita_protegida) as receita,
    COUNT(f.id_evento) as vendas,
    AVG(f.yolo_confidence_score) * 100 as acuracia,
    COUNT(*) FILTER (WHERE f.status_auditoria = 'Divergência Fantasma') as fantasmas
FROM fato_auditoria_bimodal f
JOIN dim_produto p ON f.fk_produto = p.sk_produto
JOIN dim_hardware h ON f.fk_hardware = h.sk_hardware
JOIN dim_tempo t ON f.fk_tempo = t.sk_tempo
WHERE t.data_completa >= %s [AND p.categoria = %s] [AND h.id_prateleira = %s]
```
- **Tabelas:** `fato_auditoria_bimodal`, `dim_produto`, `dim_hardware`, `dim_tempo`
- **Campos:** `receita_protegida`, `id_evento`, `yolo_confidence_score`, `status_auditoria`, `data_completa`, `categoria`, `id_prateleira`
- **Regras de Negócio:** 
  - `acuracia` é a média da confiança da IA multiplicada por 100.
  - `fantasmas` utiliza a cláusula `FILTER` para contar apenas os eventos classificados como "Divergência Fantasma".

**Consulta SQL Auxiliar (Valor em Estoque):**
```sql
SELECT SUM(preco_unitario * 50) as total_estoque FROM dim_produto
```
- **Tabela:** `dim_produto`
- **Campos:** `preco_unitario`
- **Regras de Negócio:** Simula o valor total em estoque multiplicando o preço unitário por um fator fixo (50).

## 3. Gráfico de Funil: Auditoria (Interação vs Validação)

Alimenta o gráfico de funil que mostra a jornada de eventos: total de interações físicas, quantas a IA capturou, e quantas foram validadas na auditoria.

**Consulta SQL:**
```sql
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE ia_detectou = true) as ia,
    COUNT(*) FILTER (WHERE status_auditoria = 'Validado') as validado
FROM fato_auditoria_bimodal f
JOIN dim_produto p ON f.fk_produto = p.sk_produto
JOIN dim_hardware h ON f.fk_hardware = h.sk_hardware
JOIN dim_tempo t ON f.fk_tempo = t.sk_tempo
WHERE t.data_completa >= %s [AND p.categoria = %s] [AND h.id_prateleira = %s]
```
- **Tabelas:** `fato_auditoria_bimodal` e junções dimensionais.
- **Campos:** `ia_detectou`, `status_auditoria`
- **Regras de Negócio:** Filtra contagens baseadas na flag booleana de detecção da IA e no status de auditoria 'Validado'.

## 4. Gráfico de Barras: Distribuição de Confiança da IA

Mostra em qual faixa de confiança (YOLO score) a inteligência artificial tem operado.

**Consulta SQL:**
```sql
SELECT 
    CASE 
        WHEN yolo_confidence_score < 0.5 THEN '0.4-0.5'
        WHEN yolo_confidence_score < 0.6 THEN '0.5-0.6'
        WHEN yolo_confidence_score < 0.7 THEN '0.6-0.7'
        WHEN yolo_confidence_score < 0.8 THEN '0.7-0.8'
        WHEN yolo_confidence_score < 0.9 THEN '0.8-0.9'
        ELSE '0.9-1.0'
    END as faixa,
    COUNT(*) as count
FROM fato_auditoria_bimodal f
JOIN dim_produto p ON f.fk_produto = p.sk_produto
JOIN dim_hardware h ON f.fk_hardware = h.sk_hardware
JOIN dim_tempo t ON f.fk_tempo = t.sk_tempo
WHERE t.data_completa >= %s [AND p.categoria = %s] [AND h.id_prateleira = %s]
GROUP BY faixa
ORDER BY faixa
```
- **Tabelas:** `fato_auditoria_bimodal` e junções dimensionais.
- **Campos:** `yolo_confidence_score`
- **Regras de Negócio:** Agrupa os scores em *bins* de 0.1 de intervalo utilizando uma instrução `CASE WHEN`.

## 5. Tabela de Gestão de Estoque e Status (Produtos "Encalhados")

Alimenta a tabela inferior do dashboard, mostrando os produtos com maior impacto financeiro devido a perdas estimadas.

**Consulta SQL:**
```sql
SELECT 
    p.id_sku as sku, 
    p.nome_produto as name, 
    COUNT(f.id_evento) as stock, 
    SUM(f.perda_estimada) as impact,
    CASE WHEN SUM(f.perda_estimada) > 100 THEN 'Crítico' ELSE 'Alerta' END as status
FROM fato_auditoria_bimodal f
JOIN dim_produto p ON f.fk_produto = p.sk_produto
JOIN dim_hardware h ON f.fk_hardware = h.sk_hardware
JOIN dim_tempo t ON f.fk_tempo = t.sk_tempo
WHERE t.data_completa >= %s [AND p.categoria = %s] [AND h.id_prateleira = %s] AND f.perda_estimada > 0
GROUP BY p.id_sku, p.nome_produto
ORDER BY impact DESC
LIMIT 4
```
- **Tabelas:** `fato_auditoria_bimodal` e junções dimensionais.
- **Campos:** `id_sku`, `nome_produto`, `id_evento`, `perda_estimada`
- **Regras de Negócio:** 
  - Retorna apenas registros onde houve `perda_estimada` maior que 0.
  - O status é classificado como 'Crítico' se o somatório das perdas for maior que R$ 100,00, senão 'Alerta'.
  - Ordenado pelo maior impacto financeiro, limitando aos Top 4.

## 6. Gráfico de Rosca: Impacto por Categoria

Alimenta o gráfico central que divide as receitas protegidas por tipo de categoria de produto.

**Consulta SQL:**
```sql
SELECT p.categoria as name, SUM(f.receita_protegida) as value
FROM fato_auditoria_bimodal f
JOIN dim_produto p ON f.fk_produto = p.sk_produto
JOIN dim_hardware h ON f.fk_hardware = h.sk_hardware
JOIN dim_tempo t ON f.fk_tempo = t.sk_tempo
WHERE t.data_completa >= %s [AND p.categoria = %s] [AND h.id_prateleira = %s] AND f.receita_protegida > 0
GROUP BY p.categoria
```
- **Tabelas:** `fato_auditoria_bimodal` e junções dimensionais.
- **Campos:** `categoria`, `receita_protegida`
- **Regras de Negócio:** Agrupa o somatório financeiro da receita protegida por cada categoria de produto.

## 7. Gráfico de Barras Horizontais: Top Produtos

Alimenta os dados baseados no somatório da receita protegida por cada produto individual.

**Consulta SQL:**
```sql
SELECT p.nome_produto as nome, SUM(f.receita_protegida) as valor
FROM fato_auditoria_bimodal f
JOIN dim_produto p ON f.fk_produto = p.sk_produto
JOIN dim_hardware h ON f.fk_hardware = h.sk_hardware
JOIN dim_tempo t ON f.fk_tempo = t.sk_tempo
WHERE t.data_completa >= %s [AND p.categoria = %s] [AND h.id_prateleira = %s]
GROUP BY p.nome_produto
ORDER BY valor DESC
LIMIT 6
```
- **Tabelas:** `fato_auditoria_bimodal` e junções dimensionais.
- **Campos:** `nome_produto`, `receita_protegida`
- **Regras de Negócio:** Retorna os 6 principais produtos que mais contribuíram para a receita protegida.
