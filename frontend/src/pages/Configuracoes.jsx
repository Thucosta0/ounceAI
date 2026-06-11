import { useState, useEffect } from 'react';
import { Settings, Save, RefreshCw, KeyRound, CheckCircle2, AlertCircle } from 'lucide-react';

const Configuracoes = () => {
  const [geminiKey, setGeminiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' });
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setFetching(true);
    try {
      const response = await fetch('/api/settings');
      if (response.ok) {
        const data = await response.json();
        setGeminiKey(data.gemini_key || '');
      } else {
        setStatusMsg({ type: 'error', text: 'Falha ao carregar configurações do servidor.' });
      }
    } catch (error) {
      setStatusMsg({ type: 'error', text: 'Erro de conexão com o servidor.' });
    } finally {
      setFetching(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatusMsg({ type: '', text: '' });
    try {
      const response = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ gemini_key: geminiKey }),
      });

      if (response.ok) {
        setStatusMsg({ type: 'success', text: 'Configurações salvas com sucesso!' });
        setTimeout(() => {
          setStatusMsg({ type: '', text: '' });
        }, 3500);
      } else {
        const err = await response.json();
        setStatusMsg({ type: 'error', text: err.error || 'Erro ao salvar configurações.' });
      }
    } catch (error) {
      setStatusMsg({ type: 'error', text: 'Falha na rede ao tentar salvar a configuração.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen glass-panel bg-transparent text-zinc-100 p-4 md:p-8 lg:p-12 pb-24 md:pb-12 max-w-4xl mx-auto">
      <header className="mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-orange-500 mb-2 flex items-center gap-3">
          <Settings className="w-6 h-6 md:w-8 md:h-8" /> Configurações do Sistema
        </h1>
        <p className="text-sm md:text-base text-zinc-400">
          Gerencie as chaves de API e configurações essenciais do ecossistema OunceAI.
        </p>
      </header>

      {statusMsg.text && (
        <div className={`p-4 mb-6 flex items-center gap-3 border border-orange-500/20 ${statusMsg.type === 'success' ? 'bg-orange-500/10 text-orange-400' : 'bg-red-500/10 border-red-500/20 text-red-400'} rounded-none`}>
          {statusMsg.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
          <span className="font-medium">{statusMsg.text}</span>
        </div>
      )}

      {fetching ? (
        <div className="flex items-center justify-center py-20 text-orange-500">
          <RefreshCw className="animate-spin" size={32} />
        </div>
      ) : (
        <div className="space-y-6">
          {/* Sessão de IA */}
          <div className="bg-zinc-900 border border-zinc-800 p-6 relative overflow-hidden rounded-none">
            <div className="absolute top-0 left-0 w-1 h-full bg-orange-500"></div>

            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-orange-500/10 text-orange-400 rounded-none">
                <KeyRound size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold text-zinc-100">Inteligência Artificial (Google Gemini)</h2>
                <p className="text-sm text-zinc-400">Chave de acesso para o Chatbot e Geração de Marketing</p>
              </div>
            </div>

            <form onSubmit={handleSave} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-400 mb-2" htmlFor="gemini_key">
                  GEMINI_KEY
                </label>
                <div className="relative">
                  <input
                    id="gemini_key"
                    type={showKey ? "text" : "password"}
                    value={geminiKey}
                    onChange={(e) => setGeminiKey(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 px-4 py-3 text-zinc-100 focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 transition-all font-mono rounded-none placeholder-zinc-500"
                    placeholder="Cole sua chave da API do Google Gemini aqui..."
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(!showKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-orange-400 transition-colors text-sm font-medium"
                  >
                    {showKey ? 'Ocultar' : 'Mostrar'}
                  </button>
                </div>
                <p className="mt-2 text-xs text-zinc-500">
                  Para gerar uma nova chave, acesse o <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" className="text-orange-400 hover:underline">Google AI Studio</a>.
                </p>
              </div>

              <div className="flex justify-end pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex items-center gap-2 bg-orange-500 hover:bg-orange-400 text-zinc-950 px-6 py-2.5 font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed rounded-none"
                >
                  {loading ? <RefreshCw className="animate-spin" size={20} /> : <Save size={20} />}
                  Salvar Configuração
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Configuracoes;