import { useState, useEffect } from 'react';
import { Sparkles, MapPin, Clock, Edit2, Check, X } from 'lucide-react';

const Ofertas = () => {
  const [ofertas, setOfertas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editFrases, setEditFrases] = useState([]);

  const fetchOfertas = async () => {
    try {
      const response = await fetch('/api/marketing');
      const data = await response.json();
      if (response.ok && !data.error) {
        setOfertas(data);
      } else {
        console.error("Erro na resposta da API:", data.error);
      }
    } catch (error) {
      console.error("Erro de conexão:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOfertas();
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const response = await fetch('/api/marketing/refresh-ai', { method: 'POST' });
      if (response.ok) {
        await fetchOfertas();
      } else {
        alert("Erro ao gerar ofertas.");
      }
    } catch (error) {
      console.error(error);
      alert("Erro ao conectar com o servidor.");
    } finally {
      setGenerating(false);
    }
  };

  const handleEditClick = (oferta) => {
    setEditingId(oferta._id);
    setEditFrases([...oferta.frases]);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditFrases([]);
  };

  const handleFraseChange = (index, value) => {
    const newFrases = [...editFrases];
    newFrases[index] = value;
    setEditFrases(newFrases);
  };

  const handleSaveEdit = async (id) => {
    try {
      const response = await fetch(`/api/marketing/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ frases: editFrases }),
      });
      if (response.ok) {
        // Atualiza a UI sem precisar fazer novo fetch
        setOfertas(ofertas.map(off => off._id === id ? { ...off, frases: editFrases } : off));
        setEditingId(null);
      } else {
        alert("Erro ao salvar a oferta.");
      }
    } catch (error) {
      console.error(error);
      alert("Erro ao conectar com o servidor.");
    }
  };

  return (
    <div className="min-h-screen glass-panel bg-transparent text-zinc-100 p-4 md:p-8 lg:p-12 pb-24 md:pb-12">
      <header className="mb-8 md:mb-10 flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <p className="text-orange-500 font-medium text-xs md:text-sm uppercase tracking-widest">Marketing</p>
          <h1 className="text-2xl md:text-4xl font-bold mt-1">Ofertas <span className="text-zinc-500 font-light">Dinâmicas</span></h1>
          <p className="mt-4 text-sm md:text-base text-zinc-400 max-w-2xl">
            Ofertas geradas em tempo real pelo Chatbot/IA com base no contexto atual (clima, temperatura e interações da gôndola).
          </p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-orange-500 hover:bg-orange-400 text-zinc-950 px-6 py-3 rounded-xl font-bold flex items-center gap-2 transition-all disabled:opacity-50"
        >
          <Sparkles size={18} />
          {generating ? 'Gerando pelo Gemini...' : 'Gerar Novas Ofertas'}
        </button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full p-8 text-center text-zinc-500 bg-zinc-900 border border-zinc-800 rounded-xl">
            Carregando ofertas dinâmicas...
          </div>
        ) : ofertas.length === 0 ? (
          <div className="col-span-full p-8 text-center text-zinc-500 bg-zinc-900 rounded-xl border border-zinc-800">
            Nenhuma oferta dinâmica registrada ainda. Clique em "Gerar Novas Ofertas".
          </div>
        ) : (
          ofertas.map((oferta) => (
            <div key={oferta._id} className="bg-zinc-900 border border-zinc-800 overflow-hidden flex flex-col transition-all hover:border-orange-500/50 rounded-xl">
              <div className="p-5 border-b border-zinc-800 bg-zinc-900/50 flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-zinc-100">{oferta.nome}</h3>
                  <div className="flex items-center gap-1 mt-2 text-xs text-zinc-500">
                    <MapPin size={12} />
                    <span>{oferta.contexto?.cidade || 'Local não definido'} • {oferta.contexto?.clima || 'Clima não definido'}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <div className="bg-orange-500/10 text-orange-400 text-xs font-bold px-2 py-1 border border-orange-500/20 rounded-md">
                    IA
                  </div>
                  {editingId !== oferta._id && (
                    <button 
                      onClick={() => handleEditClick(oferta)}
                      className="text-zinc-400 hover:text-zinc-100 p-1"
                      title="Editar oferta"
                    >
                      <Edit2 size={16} />
                    </button>
                  )}
                </div>
              </div>

              <div className="p-5 flex-1 flex flex-col gap-3">
                {editingId === oferta._id ? (
                  editFrases.map((frase, idx) => (
                    <textarea
                      key={idx}
                      value={frase}
                      onChange={(e) => handleFraseChange(idx, e.target.value)}
                      className="bg-zinc-950 p-3 text-sm text-zinc-200 border border-zinc-700 focus:border-orange-500 outline-none rounded-lg w-full resize-none min-h-[80px]"
                    />
                  ))
                ) : (
                  oferta.frases && oferta.frases.map((frase, idx) => (
                    <div key={idx} className="bg-zinc-950 p-4 text-sm text-zinc-300 italic border-l-2 border-orange-500 rounded-r-lg">
                      "{frase}"
                    </div>
                  ))
                )}
                
                {editingId === oferta._id && (
                  <div className="flex justify-end gap-2 mt-2">
                    <button onClick={handleCancelEdit} className="p-2 text-zinc-400 hover:text-red-400 bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors">
                      <X size={16} />
                    </button>
                    <button onClick={() => handleSaveEdit(oferta._id)} className="p-2 text-zinc-950 bg-orange-500 hover:bg-orange-400 rounded-lg transition-colors">
                      <Check size={16} />
                    </button>
                  </div>
                )}
              </div>

              <div className="p-4 border-t border-zinc-800 text-xs text-zinc-500 flex items-center gap-1">
                <Clock size={12} />
                Gerado em: {new Date(oferta.timestamp).toLocaleString('pt-BR')}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Ofertas;