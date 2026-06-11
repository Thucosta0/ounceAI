import { Outlet, Link, useLocation } from 'react-router-dom';
import { BarChart3, Tag, Settings, LogOut } from 'lucide-react';
import Chat from './Chat';
import { useAuth } from '../context/AuthContext';

const Layout = () => {
  const location = useLocation();
  const { logout } = useAuth();

  const navItems = [
    { path: '/', icon: <BarChart3 size={24} />, label: 'Visão' },
    { path: '/ofertas', icon: <Tag size={24} />, label: 'Ofertas' },
    { path: '/configuracoes', icon: <Settings size={24} />, label: 'Configurações' },
  ];

  return (
    <div className="bg-[radial-gradient(circle_at_top_right,_rgba(249,115,22,0.18),_transparent_28%),radial-gradient(circle_at_bottom_left,_rgba(59,130,246,0.16),_transparent_24%),#09090b] text-zinc-100 font-sans antialiased min-h-screen flex flex-col md:flex-row pb-16 md:pb-0">
      {/* Navbar lateral (Desktop) / Inferior (Mobile) */}
      <nav className="fixed bottom-0 md:top-0 left-0 w-full md:w-24 md:h-full flex md:flex-col items-center justify-around md:justify-start md:py-6 bg-zinc-950/70 backdrop-blur-xl border-t md:border-t-0 md:border-r border-zinc-800/80 shadow-[0_30px_80px_rgba(15,23,42,0.55)] z-40 p-3 md:p-4">
        <div className="hidden md:flex items-center justify-center w-full px-2 mb-8">
          <Link to="/" className="w-full flex items-center justify-center cursor-pointer transition-transform hover:scale-105">
            <img src="/logoounceai.png" alt="OunceAI Logo" className="w-full h-auto object-contain" />
          </Link>
        </div>
        
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              title={item.label}
              className={`transition-all-custom p-3 flex flex-col items-center gap-1 rounded-3xl ${
                isActive 
                  ? 'text-orange-400 bg-orange-500/10 ring-1 ring-orange-500/20 shadow-[0_15px_35px_rgba(249,115,22,0.12)]' 
                  : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900/70'
              }`}
            >
              {item.icon}
              <span className="text-[10px] md:hidden font-medium">{item.label}</span>
            </Link>
          );
        })}
        
        {/* Logout Button */}
        <button
          onClick={logout}
          title="Sair"
          className="transition-all-custom p-3 flex flex-col items-center gap-1 rounded-3xl text-red-400 hover:text-red-300 hover:bg-red-900/20 md:mt-auto"
        >
          <LogOut size={24} />
          <span className="text-[10px] md:hidden font-medium">Sair</span>
        </button>
      </nav>

      {/* Conteúdo Principal */}
      <main className="md:ml-20 flex-1 relative w-full overflow-x-hidden">
        <div className="md:hidden flex items-center justify-center py-4 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-30 border-b border-zinc-800/50">
          <Link to="/" className="cursor-pointer transition-transform hover:scale-105">
            <img src="/logoounce.png" alt="OunceAI Logo" className="h-8 object-contain" />
          </Link>
        </div>
        
        <div className="p-4 md:p-8 max-w-7xl mx-auto w-full">
          <Outlet />
        </div>
        
        {/* Componente de Chat Flutuante */}
        <Chat />
      </main>
    </div>
  );
};

export default Layout;
