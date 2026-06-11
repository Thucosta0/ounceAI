import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import StrategicDashboard from './pages/StrategicDashboard';
import Ofertas from './pages/Ofertas';
import Configuracoes from './pages/Configuracoes';
import Login from './pages/Login';
import ProtectedRoute from './components/ProtectedRoute';

function TrollPage() {
  return (
    <div style={{ backgroundColor: '#000', color: '#fff', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', margin: 0, fontFamily: 'sans-serif', textAlign: 'center' }}>
      <img src="/imgtroll.webp" alt="Troll" style={{ maxWidth: '400px', marginBottom: '20px', borderRadius: '20px' }} />
      <h1 style={{ color: '#ff3333' }}>Não foi dessa vez.</h1>
      <p>Tentativa de ataque registrada.</p>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/.env" element={<TrollPage />} />
      <Route path="/wp-admin" element={<TrollPage />} />
      <Route path="/admin" element={<TrollPage />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route index element={<StrategicDashboard />} />
        <Route path="estrategico" element={<StrategicDashboard />} />
        <Route path="ofertas" element={<Ofertas />} />
        <Route path="configuracoes" element={<Configuracoes />} />
      </Route>
    </Routes>
  );
}

export default App;