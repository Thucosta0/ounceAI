import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { ShieldCheck, AlertTriangle, Package, Target, TrendingDown, CheckCircle2, RefreshCcw, FilterX } from 'lucide-react';

const StrategicDashboard = () => {
  const [filters, setFilters] = useState({
    date: 'today',
    category: 'all',
    shelfId: 'all',
  });

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams(filters).toString();
      const response = await fetch(`/api/analytics/stats?${params}`);
      const result = await response.json();
      
      if (!response.ok || result.error) {
        throw new Error(result.error || "Erro ao buscar dados da API");
      }
      
      setData(result);
    } catch (error) {
      console.error("Erro ao buscar dados estratégicos:", error);
      // Evita o crash da tela preta setando um mock vazio ou null tratado
      setData(null); 
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filters]);

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  const handleResetFilters = () => {
    setFilters({
      date: 'today',
      category: 'all',
      shelfId: 'all',
    });
    setCrossFilter({ active: false, source: null, value: null });
  };

  // CROSS-FILTERING STATE (Estilo Power BI / Looker)
  const [crossFilter, setCrossFilter] = useState({
    active: false,
    source: null, // De qual gráfico veio o clique
    value: null   // Qual valor/fatia foi clicada
  });

  // --- ECHARTS GLOBAL CONFIGURATIONS ---
  const textStyle = { color: '#a1a1aa' };
  const titleStyle = { color: '#f4f4f5', fontSize: 15, fontWeight: '500' };
  const tooltipStyle = { backgroundColor: '#18181b', borderColor: '#27272a', textStyle: { color: '#f4f4f5' } };
  const gridStyle = { left: '3%', right: '5%', bottom: '8%', top: '20%', containLabel: true };

  // Função genérica para capturar cliques nos gráficos (Cross-filtering)
  const handleChartClick = (source, params) => {
    // Se clicar na mesma fatia que já está ativa, ele limpa o filtro (toggle)
    if (crossFilter.active && crossFilter.source === source && crossFilter.value === params.name) {
      setCrossFilter({ active: false, source: null, value: null });
    } else {
      setCrossFilter({ active: true, source: source, value: params.name });
    }
  };

  // Helper para destacar visualmente a fatia clicada e "apagar" as outras
  const getOpacity = (source, name) => {
    if (!crossFilter.active) return 1;
    if (crossFilter.source === source && crossFilter.value === name) return 1;
    return 0.3; // Deixa os outros elementos transparentes (comportamento clássico do Power BI)
  };

  if (!data) return <div className="p-10 text-zinc-400">Carregando dados estratégicos...</div>;

  // ============================================================================
  // SESSÃO 1: PROTEÇÃO DE RECEITA E CONVERSÃO
  // ============================================================================

  // 1. Bar Chart: Valor Protegido por Hora
  const valueRecoveredOption = {
    title: { text: 'Valor Financeiro Protegido (R$ por Hora)', textStyle: titleStyle, left: 'center' },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, ...tooltipStyle },
    grid: gridStyle,
    xAxis: { type: 'category', data: data.receita_por_hora.map(d => d.hora), axisLabel: textStyle, axisLine: { lineStyle: { color: '#27272a' } } },
    yAxis: { type: 'value', min: 0, axisLabel: { ...textStyle, formatter: 'R$ {value}' }, splitLine: { lineStyle: { color: '#27272a', type: 'dashed' } } },
    series: [{
      name: 'Valor Protegido', type: 'bar', barWidth: '45%',
      itemStyle: { 
        color: '#10b981', 
        borderRadius: [8, 8, 0, 0],
        opacity: (params) => getOpacity('time', params.name)
      },
      data: data.receita_por_hora.map(d => d.valor)
    }]
  };

  // 2. Donut Chart: Categorias Visadas
  const categoriesOption = {
    title: { text: 'Impacto por Categoria', textStyle: titleStyle, left: 'center' },
    tooltip: { trigger: 'item', formatter: '{b}: R$ {c} ({d}%)', ...tooltipStyle },
    legend: { bottom: 0, textStyle, icon: 'circle' },
    series: [{
      name: 'Impacto Financeiro', type: 'pie', radius: ['40%', '70%'], center: ['50%', '45%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 8, borderColor: '#18181b', borderWidth: 2 },
      label: { show: false, position: 'center' },
      emphasis: { label: { show: true, fontSize: 18, fontWeight: 'bold', color: '#fff' } },
      data: data.vendas_por_categoria.map(d => ({
        ...d,
        itemStyle: { opacity: getOpacity('category', d.name) }
      }))
    }]
  };

  // 3. Funnel Chart: Ciclo de Vida da Movimentação na Gôndola
  const funnelOption = {
    title: { text: 'Auditoria: Interação vs Validação', textStyle: titleStyle, left: 'center' },
    tooltip: { trigger: 'item', formatter: '{b}: {c}', ...tooltipStyle },
    legend: { bottom: 0, textStyle, icon: 'circle' },
    series: [{
      name: 'Auditoria', type: 'funnel', left: '15%', width: '70%', height: '65%', top: '15%',
      label: { show: true, position: 'inside', color: '#fff', formatter: '{c}' }, 
      labelLine: { show: false }, 
      itemStyle: { borderColor: '#18181b', borderWidth: 2 },
      data: data.funnel_data.map(d => ({
        ...d,
        itemStyle: { opacity: getOpacity('funnel', d.name) }
      }))
    }]
  };

  // ============================================================================
  // SESSÃO 2: ACURÁCIA DA IA E CREDIBILIDADE DO SISTEMA
  // ============================================================================

  // 4. Horizontal Bar: Precisão de Detecção da IA
  const accuracyOption = {
    title: { text: 'Acurácia de Detecção da IA por Evento', textStyle: titleStyle, left: 'center' },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: '{b}: {c}% precisão', ...tooltipStyle },
    grid: gridStyle,
    xAxis: { type: 'value', min: 0, max: 100, axisLabel: { ...textStyle, formatter: '{value}%' }, splitLine: { show: false } },
    yAxis: { type: 'category', data: data.accuracy_by_event.map(d => d.name), axisLabel: textStyle, axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      name: 'Acurácia', type: 'bar', barWidth: '40%',
      itemStyle: { color: '#3b82f6', borderRadius: [0, 8, 8, 0] },
      label: { show: true, position: 'right', color: '#fff', formatter: '{c}%' },
      data: data.accuracy_by_event.map(d => d.value)
    }]
  };

  // 5. Line Chart: Evolução de Falsos Positivos
  const falsePositivesEvolutionOption = {
    title: { text: 'Evolução e Redução de Falsos Positivos (Aprendizado da IA)', textStyle: titleStyle, left: 'center' },
    tooltip: { trigger: 'axis', ...tooltipStyle },
    grid: gridStyle,
    xAxis: { type: 'category', data: data.false_positives_evolution.map(d => d.name), axisLabel: textStyle, axisLine: { lineStyle: { color: '#27272a' } } },
    yAxis: { type: 'value', min: 0, axisLabel: textStyle, splitLine: { lineStyle: { color: '#27272a', type: 'dashed' } } },
    series: [{
      name: 'Falsos Positivos', type: 'line', smooth: true,
      itemStyle: { color: '#10b981' }, lineStyle: { width: 3 },
      areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(16, 185, 129, 0.3)' }, { offset: 1, color: 'rgba(16, 185, 129, 0)' }] } },
      data: data.false_positives_evolution.map(d => d.value)
    }]
  };

  // 6. Histogram: Distribuição de Confiança da IA em Falhas (Diagnóstico do Modelo YOLO)
  const yoloConfidenceOption = {
    title: { text: 'Distribuição de Confiança da IA em Falhas (YOLO)', textStyle: titleStyle, left: 'center' },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: '{b}: {c} falhas', ...tooltipStyle },
    grid: gridStyle,
    xAxis: { 
      type: 'category', 
      data: data.confidence_distribution.map(d => d.name), 
      axisLabel: textStyle, 
      axisLine: { lineStyle: { color: '#27272a' } } 
    },
    yAxis: { type: 'value', min: 0, axisLabel: textStyle, splitLine: { show: false } },
    series: [{
      name: 'Falhas', type: 'bar', barWidth: '60%',
      itemStyle: { 
        color: (params) => {
          // Destaca as faixas de confiança muito altas onde a IA está "confiantemente errada"
          if (params.name === '0.9-1.0' || params.name === '0.8-0.9') return '#ef4444';
          return '#3b82f6';
        }, 
        borderRadius: [4, 4, 0, 0],
        opacity: (params) => getOpacity('confidence', params.name)
      },
      data: data.confidence_distribution.map(d => d.value)
    }]
  };

  return (
    <div className="min-h-screen bg-transparent text-zinc-100 p-2 md:p-6 font-sans">
      
      {/* ========================================== */}
      {/* HEADER & SCORECARDS                        */}
      {/* ========================================== */}
      <header className="mb-10">
        <div className="flex flex-col xl:flex-row justify-between items-start gap-6 mb-6">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-zinc-100 mb-1">Visão Estratégica</h1>
            <p className="text-zinc-400 text-sm">Monitoramento de eficiência, prevenção de perdas e acurácia do ecossistema.</p>
          </div>
          
          {/* Global Filters */}
          <div className="bg-zinc-800/50 p-3 rounded-xl flex flex-col sm:flex-row flex-wrap gap-3 border border-zinc-800 w-full xl:w-auto">
            <div className="flex gap-2 w-full sm:w-auto">
              <button 
                onClick={handleResetFilters} 
                className="p-2 bg-zinc-900 border border-zinc-700 rounded-lg hover:bg-zinc-800 transition-colors flex-1 sm:flex-none flex justify-center"
                title="Resetar filtros e atualizar"
              >
                <RefreshCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
            <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-1.5 w-full sm:w-auto">
              <label htmlFor="date" className="text-xs text-zinc-400 uppercase tracking-wider min-w-[70px]">Período:</label>
              <select id="date" name="date" value={filters.date} onChange={handleFilterChange} className="bg-transparent text-sm text-zinc-200 outline-none cursor-pointer flex-1">
                <option value="today" className="bg-zinc-900">Hoje</option>
                <option value="7d" className="bg-zinc-900">Últimos 7 Dias</option>
                <option value="30d" className="bg-zinc-900">Últimos 30 Dias</option>
              </select>
            </div>

            <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-1.5 w-full sm:w-auto">
              <label htmlFor="category" className="text-xs text-zinc-400 uppercase tracking-wider min-w-[70px]">Categoria:</label>
              <select id="category" name="category" value={filters.category} onChange={handleFilterChange} className="bg-transparent text-sm text-zinc-200 outline-none cursor-pointer flex-1">
                <option value="all" className="bg-zinc-900">Todas Categorias</option>
                {data.filter_options?.categories?.map(cat => (
                  <option key={cat} value={cat} className="bg-zinc-900">{cat}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-1.5 w-full sm:w-auto">
              <label htmlFor="shelfId" className="text-xs text-zinc-400 uppercase tracking-wider min-w-[70px]">Gôndola:</label>
              <select id="shelfId" name="shelfId" value={filters.shelfId} onChange={handleFilterChange} className="bg-transparent text-sm text-zinc-200 outline-none cursor-pointer flex-1">
                <option value="all" className="bg-zinc-900">Todas Gôndolas</option>
                {data.filter_options?.shelves?.map(shelf => (
                  <option key={shelf} value={shelf} className="bg-zinc-900">{shelf}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* SCORECARDS */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* 1. Valor Total em Estoque */}
          <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl transition-all hover:border-zinc-700">
            <p className="text-zinc-400 text-xs font-medium mb-1 uppercase tracking-wider">Valor Total em Estoque</p>
            <div className="flex items-end gap-2">
              <h2 className="text-3xl font-bold text-zinc-100">R$ {(data.kpis.valor_estoque / 1000).toFixed(1)}K</h2>
              <span className="text-zinc-500 text-sm font-semibold flex items-center mb-1"><Package className="w-4 h-4 mr-1" /></span>
            </div>
            <p className="text-zinc-500 text-xs mt-2">Capital imobilizado nas gôndolas</p>
          </div>

          {/* 2. Receita Recuperada */}
          <div className="bg-zinc-900 border border-green-900/30 p-5 rounded-xl transition-all hover:border-green-800/50">
            <p className="text-zinc-400 text-xs font-medium mb-1 uppercase tracking-wider">Receita Protegida (Hoje)</p>
            <div className="flex items-end gap-2">
              <h2 className="text-3xl font-bold text-green-500">R$ {(data.kpis.receita_hoje / 1000).toFixed(1)}K</h2>
              <span className="text-green-500 text-sm font-semibold flex items-center mb-1"><ShieldCheck className="w-4 h-4 mr-1" /></span>
            </div>
            <p className="text-zinc-500 text-xs mt-2">Perdas evitadas pelo sistema</p>
          </div>

          {/* 3. Divergências Fantasmas */}
          <div className="bg-zinc-900 border border-red-900/30 p-5 rounded-xl transition-all hover:border-red-800/50">
            <p className="text-zinc-400 text-xs font-medium mb-1 uppercase tracking-wider">Divergências Fantasmas</p>
            <div className="flex items-end gap-2">
              <h2 className="text-3xl font-bold text-red-500">50</h2>
              <span className="text-red-400 text-sm font-semibold flex items-center mb-1"><AlertTriangle className="w-4 h-4 mr-1" /> Alerta</span>
            </div>
            <p className="text-zinc-500 text-xs mt-2">Alterações sem detecção visual</p>
          </div>

          {/* 4. Acurácia do Sistema */}
          <div className="bg-zinc-900 border border-blue-900/30 p-5 rounded-xl transition-all hover:border-blue-800/50">
            <p className="text-zinc-400 text-xs font-medium mb-1 uppercase tracking-wider">Acurácia Geral da IA</p>
            <div className="flex items-end gap-2">
              <h2 className="text-3xl font-bold text-blue-500">{data.kpis.acuracia_ia.toFixed(1)}%</h2>
              <span className="text-blue-400 text-sm font-semibold flex items-center mb-1"><Target className="w-4 h-4 mr-1" /></span>
            </div>
            <p className="text-zinc-500 text-xs mt-2">Precisão média do ecossistema</p>
          </div>

        </div>
      </header>

      {/* ========================================== */}
      {/* SESSÃO 1: PROTEÇÃO E CONVERSÃO             */}
      {/* ========================================== */}
      <section className="mb-12">
        <div className="flex items-center gap-3 mb-6">
          <ShieldCheck className="text-zinc-400 w-6 h-6" />
          <h2 className="text-xl font-semibold text-zinc-200">Proteção de Receita & Conversão</h2>
          <div className="flex-1 h-px bg-zinc-800 ml-4"></div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl lg:col-span-2 shadow-sm">
            <ReactECharts option={valueRecoveredOption} style={{ height: '320px', width: '100%' }} onEvents={{ click: (e) => handleChartClick('time', e) }} />
          </div>
          <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl shadow-sm flex flex-col justify-center">
            <ReactECharts option={funnelOption} style={{ height: '320px', width: '100%' }} onEvents={{ click: (e) => handleChartClick('funnel', e) }} />
          </div>
          <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl lg:col-span-3 shadow-sm">
            <ReactECharts option={categoriesOption} style={{ height: '320px', width: '100%' }} onEvents={{ click: (e) => handleChartClick('category', e) }} />
          </div>
        </div>
      </section>

      {/* ========================================== */}
      {/* SESSÃO 2: ACURÁCIA E CREDIBILIDADE         */}
      {/* ========================================== */}
      <section className="mb-12">
        <div className="flex items-center gap-3 mb-6">
          <CheckCircle2 className="text-zinc-400 w-6 h-6" />
          <h2 className="text-xl font-semibold text-zinc-200">Acurácia do Sistema & Credibilidade</h2>
          <div className="flex-1 h-px bg-zinc-800 ml-4"></div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Precisão da IA (Novo Gráfico) */}
          <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl shadow-sm lg:col-span-2">
            <ReactECharts option={accuracyOption} style={{ height: '280px', width: '100%' }} />
          </div>

          {/* Evolução de Falsos Positivos (Prova de Aprendizado - Novo Gráfico) */}
          <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl shadow-sm">
            <ReactECharts option={falsePositivesEvolutionOption} style={{ height: '300px', width: '100%' }} />
          </div>

          {/* Histograma: Diagnóstico de Falhas do YOLO */}
          <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl shadow-sm">
            <ReactECharts option={yoloConfidenceOption} style={{ height: '300px', width: '100%' }} onEvents={{ click: (e) => handleChartClick('confidence', e) }} />
          </div>
        </div>
      </section>

      {/* ========================================== */}
      {/* SESSÃO 3: OPERAÇÃO E ESTOQUE FÍSICO        */}
      {/* ========================================== */}
      <section className="mb-8">
        <div className="flex items-center gap-3 mb-6">
          <Package className="text-zinc-400 w-6 h-6" />
          <h2 className="text-xl font-semibold text-zinc-200">Gestão de Estoque Físico</h2>
          <div className="flex-1 h-px bg-zinc-800 ml-4"></div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden shadow-sm">
          <div className="p-6 border-b border-zinc-800 bg-zinc-900/50">
            <h3 className="text-lg font-medium text-zinc-100">Status de Inventário e Produtos "Encalhados"</h3>
            <p className="text-zinc-400 text-sm mt-1">Monitoramento de mercadorias sem giro (Aging {'>'} 48h).</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-zinc-950/50 text-zinc-400 text-xs uppercase tracking-wider">
                  <th className="px-6 py-4 font-medium">SKU</th>
                  <th className="px-6 py-4 font-medium">Produto</th>
                  <th className="px-6 py-4 font-medium">Estoque Atual</th>
                  <th className="px-6 py-4 font-medium">Aging (Horas)</th>
                  <th className="px-6 py-4 font-medium">Impacto Financeiro</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/50">
                {data.inventory_status.map((product, idx) => (
                  <tr key={idx} className="hover:bg-zinc-800/30 transition-colors">
                    <td className="px-6 py-4 text-zinc-400 font-mono text-sm">{product.sku}</td>
                    <td className="px-6 py-4 text-zinc-100 font-medium">{product.name}</td>
                    <td className="px-6 py-4 text-zinc-100 font-bold">{product.stock} un.</td>
                    <td className="px-6 py-4">
                      <span className={`font-bold ${product.aging > 48 ? 'text-red-400' : 'text-zinc-300'}`}>
                        {product.aging}h
                      </span>
                    </td>
                    <td className="px-6 py-4 text-zinc-300">{product.impact}</td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        product.status === 'Crítico' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                        product.status === 'Alerta' ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20' :
                        'bg-zinc-800 text-zinc-300 border border-zinc-700'
                      }`}>
                        {product.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

    </div>
  );
};

export default StrategicDashboard;
