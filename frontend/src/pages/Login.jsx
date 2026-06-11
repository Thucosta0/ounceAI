import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setIsLoading(true);

    try {
      if (isRegistering) {
        const result = await register(username, password);
        if (result.success) {
          setSuccessMsg('Cadastro realizado com sucesso! Faça login.');
          setIsRegistering(false);
          setPassword('');
        } else {
          setError(result.message || 'Erro ao cadastrar.');
        }
      } else {
        const success = await login(username, password);
        if (success) {
          navigate('/');
        } else {
          setError('Usuário ou senha incorretos.');
        }
      }
    } catch (err) {
      setError(`Ocorreu um erro ao tentar ${isRegistering ? 'cadastrar' : 'fazer login'}.`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-[radial-gradient(circle_at_top_right,_rgba(249,115,22,0.18),_transparent_28%),radial-gradient(circle_at_bottom_left,_rgba(59,130,246,0.16),_transparent_24%),#09090b]">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center text-orange-500 mb-6">
          <img src="/robo.webp" alt="OunceAI Agent" className="h-32 object-contain rounded-full shadow-[0_0_15px_rgba(249,115,22,0.4)] border border-orange-500/30" />
        </div>
      </div>

      <div className="mt-2 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-zinc-900/80 backdrop-blur-xl py-8 px-4 shadow-2xl sm:rounded-2xl sm:px-10 border border-zinc-800/80">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label className="block text-sm font-medium text-zinc-300">
                Usuário
              </label>
              <div className="mt-1">
                <input
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-zinc-700 rounded-xl shadow-sm placeholder-zinc-500 focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm bg-zinc-800 text-white"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-300">
                Senha
              </label>
              <div className="mt-1">
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-zinc-700 rounded-xl shadow-sm placeholder-zinc-500 focus:outline-none focus:ring-orange-500 focus:border-orange-500 sm:text-sm bg-zinc-800 text-white"
                />
              </div>
            </div>

            {error && (
              <div className="text-red-400 text-sm text-center font-medium bg-red-900/20 py-2 rounded-lg border border-red-900/50">
                {error}
              </div>
            )}
            
            {successMsg && (
              <div className="text-emerald-400 text-sm text-center font-medium bg-emerald-900/20 py-2 rounded-lg border border-emerald-900/50">
                {successMsg}
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-bold text-white bg-orange-600 hover:bg-orange-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500 focus:ring-offset-zinc-900 disabled:opacity-50 transition-all duration-200"
              >
                {isLoading ? 'Aguarde...' : (isRegistering ? 'Cadastrar' : 'Entrar')}
              </button>
            </div>
            
            <div className="mt-4 text-center">
              <button
                type="button"
                onClick={() => {
                  setIsRegistering(!isRegistering);
                  setError('');
                  setSuccessMsg('');
                }}
                className="text-sm text-zinc-400 hover:text-orange-500 transition-colors"
              >
                {isRegistering ? 'Já tem uma conta? Faça login' : 'Não tem conta? Cadastre-se'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
