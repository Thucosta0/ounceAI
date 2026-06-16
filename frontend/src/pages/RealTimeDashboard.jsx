import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, CheckCircle, Package, RefreshCw, ShoppingCart } from 'lucide-react';

const getEventTypeColor = (tipo) => {
  switch (tipo) {
    case 'Validado':
    case 'Inclusão / Venda':
      return 'bg-green-500/20 text-green-400 border border-green-500/30';
    case 'Retirada':
    case 'Retirada de Item':
      return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30';
    case 'Divergência Fantasma':
    case 'Divergência / Reposição Fantasma':
      return 'bg-red-500/20 text-red-400 border border-red-500/30';
    case 'Reposição':
    case 'Reposição de Estoque':
      return 'bg-purple-500/20 text-purple-400 border border-purple-500/30';
    default:
      return 'bg-slate-500/20 text-slate-400 border border-slate-500/30';
  }
};

const getEventTypeLabel = (tipo) => {
  switch (tipo) {
    case 'Validado':
      return 'Inclusão / Venda';
    case 'Retirada':
      return 'Retirada de Item';
    case 'Divergência Fantasma':
      return 'Divergência / Reposição Fantasma';
    case 'Reposição':
      return 'Reposição de Estoque';
    default:
      return tipo;
  }
};

const RealTimeDashboard = () => {
  // Dados do último evento e dos últimos 5 eventos
  const [events, setEvents] = useState([]);
  const [lastEvent, setLastEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/realtime/events');
      
      if (!response.ok) {
        throw new Error('Erro ao buscar eventos');
      }
      
      const data = await response.json();
      
      if (data.success && data.events && data.events.length > 0) {
        setEvents(data.events);
        setLastEvent(data.events[0]);
      }
      
      setLoading(false);
      setError(null);
    } catch (err) {
      console.error('Erro na busca de eventos:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  // Fetch inicial + polling em tempo real
  useEffect(() => {
    fetchEvents();
    const interval = setInterval(fetchEvents, 10000); // Atualiza a cada 10 segundos
    return () => clearInterval(interval);
  }, []);

  if (loading && !lastEvent) {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-100 p-6 md:p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-blue-500 mx-auto mb-6"></div>
          <p className="text-lg text-slate-400">Carregando dados do sistema...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 text-slate-100 p-6 md:p-8 flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-6" />
          <h2 className="text-2xl font-bold mb-2 text-red-300">Ocorreu um erro ao carregar os eventos</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <button 
            onClick={fetchEvents} 
            className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 transition-colors rounded-lg font-medium mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            Tentar Novamente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 md:p-8">
      {/* Cabeçalho */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent flex items-center gap-3">
            <Activity className="w-8 h-8 text-blue-400" />
            Painel Gerencial em Tempo Real
          </h1>
          <p className="text-slate-400 mt-1">Auditoria Bimodal - Últimos Eventos Processados</p>
        </div>
        <button 
          onClick={fetchEvents}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 transition-colors rounded-lg text-sm font-medium shadow-lg shadow-blue-900/30"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Atualizar
        </button>
      </div>

      {/* Grid Principal - Duas Colunas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Coluna Esquerda - Card do Produto e Infraestrutura */}
        <div className="space-y-6">
          {/* Card do Último Evento */}
          <div className="bg-slate-800/80 border border-slate-700 rounded-2xl p-8 shadow-xl shadow-slate-900/50">
            <div className="flex items-start justify-between mb-6">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Último Evento Processado</span>
                <h2 className="text-xl font-bold text-white mt-1">{lastEvent.horario}</h2>
              </div>
              {/* Indicador LED Pulsante */}
              <div className="relative">
                <span className={`inline-flex h-4 w-4 rounded-full animate-pulse ring-4 ${lastEvent.tipo.includes('Divergência') ? 'bg-red-500 ring-red-500/20' : 'bg-green-500 ring-green-500/20'}`}></span>
              </div>
            </div>

            <div className="space-y-5">
              {/* Nome do Produto */}
              <div className="p-5 bg-slate-900/60 rounded-xl border border-slate-700/60">
                <div className="flex items-center gap-3 mb-2">
                  <Package className="w-6 h-6 text-cyan-400" />
                  <span className="text-sm text-slate-400 font-semibold uppercase tracking-wider">Produto</span>
                </div>
                <p className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
                  {lastEvent.produto}
                </p>
              </div>

              {/* Massa Nominal e Equipamento */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-900/40 rounded-xl border border-slate-700/40">
                  <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider block mb-1">Massa Nominal</span>
                  <p className="text-xl font-bold text-cyan-300">{lastEvent.massa_nominal}g</p>
                </div>
                <div className="p-4 bg-slate-900/40 rounded-xl border border-slate-700/40">
                  <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider block mb-1">Balança / Equipamento</span>
                  <p className="text-lg font-bold text-blue-300">{lastEvent.equipamento}</p>
                </div>
              </div>

              {/* Status do Evento */}
              <div className="flex items-center justify-between p-5 bg-gradient-to-r from-slate-900/80 to-slate-800/80 rounded-xl border border-slate-700/60">
                <div className="flex items-center gap-3">
                  {lastEvent.tipo.includes('Divergência') ? (
                    <AlertTriangle className="w-7 h-7 text-red-400" />
                  ) : lastEvent.tipo.includes('Validado') ? (
                    <CheckCircle className="w-7 h-7 text-green-400" />
                  ) : lastEvent.tipo.includes('Reposição') ? (
                    <ShoppingCart className="w-7 h-7 text-purple-400" />
                  ) : (
                    <Package className="w-7 h-7 text-yellow-400" />
                  )}
                  <div>
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 block">Status do Evento</span>
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${getEventTypeColor(lastEvent.tipo)}`}>
                      {getEventTypeLabel(lastEvent.tipo)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Coluna Direita - Tabela de Últimos Eventos */}
        <div className="space-y-6">
          <div className="bg-slate-800/80 border border-slate-700 rounded-2xl p-6 shadow-xl shadow-slate-900/50 h-full">
            <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-400" />
              Histórico Recente (Últimos 5)
            </h3>

            <div className="overflow-x-auto rounded-xl border border-slate-700/50">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-900/80 border-b border-slate-700">
                  <tr>
                    <th className="py-4 px-5 text-xs font-bold uppercase tracking-wider text-slate-400">Horário</th>
                    <th className="py-4 px-5 text-xs font-bold uppercase tracking-wider text-slate-400">Equipamento</th>
                    <th className="py-4 px-5 text-xs font-bold uppercase tracking-wider text-slate-400">Produto</th>
                    <th className="py-4 px-5 text-xs font-bold uppercase tracking-wider text-slate-400">Tipo de Evento</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {events.map((event) => (
                    <tr key={event.id} className="hover:bg-slate-700/30 transition-colors">
                      <td className="py-4 px-5 text-sm text-slate-300 font-mono">{event.horario}</td>
                      <td className="py-4 px-5 text-sm text-slate-200">{event.equipamento}</td>
                      <td className="py-4 px-5 text-sm text-slate-200">{event.produto}</td>
                      <td className="py-4 px-5">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold uppercase tracking-wider ${getEventTypeColor(event.tipo)}`}>
                          {getEventTypeLabel(event.tipo)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default RealTimeDashboard;
