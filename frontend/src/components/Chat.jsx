import { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Bot } from 'lucide-react';

const Chat = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 1, text: 'Olá! Sou o assistente Ounce AI. Como posso ajudar com suas prateleiras hoje?', sender: 'ai' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userText = input;
    const newMsg = { id: Date.now(), text: userText, sender: 'user' };
    setMessages(prev => [...prev, newMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000); // 1 minuto (60000ms)

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userText }),
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error('Erro na comunicação com a API');
      }

      const data = await response.json();
      
      setMessages(prev => [...prev, { id: Date.now(), text: data.response || data.resposta, sender: 'ai' }]);
    } catch (error) {
      console.error('Chat API Error:', error);
      
      if (error.name === 'AbortError') {
        setMessages(prev => [...prev, { 
          id: Date.now(), 
          text: 'Tempo limite excedido. Por favor, pesquise algo mais simples.', 
          sender: 'ai' 
        }]);
      } else {
        setMessages(prev => [...prev, { 
          id: Date.now(), 
          text: 'Erro ao processar sua solicitação. Verifique a comunicação com o servidor.', 
          sender: 'ai' 
        }]);
      }
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="fixed bottom-20 md:bottom-6 right-4 md:right-6 z-50">
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="bg-orange-500 hover:bg-orange-400 text-zinc-950 p-4 shadow-lg shadow-orange-500/20 transition-transform hover:scale-105 rounded-full border border-orange-400"
          aria-label="Abrir Chat"
        >
          <MessageSquare size={24} />
        </button>
      )}
    
      {isOpen && (
        <div className="bg-zinc-900 w-[calc(100vw-32px)] sm:w-96 shadow-2xl border border-zinc-800 flex flex-col overflow-hidden transition-all h-[500px] max-h-[70vh] md:max-h-[80vh] rounded-2xl">
          <div className="bg-zinc-950 text-zinc-100 p-4 border-b border-zinc-800 flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-16 h-16 overflow-hidden rounded-full">
                <img src="/robo.webp" alt="OunceAI Agent" className="w-full h-full object-contain" />
              </div>
              <div className="flex flex-col">
                <span className="font-semibold tracking-wide block text-orange-400">OunceAI Agent</span>
                <span className="text-xs text-zinc-500 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span> Online
                </span>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="text-zinc-500 hover:text-zinc-300 transition-colors p-2 hover:bg-zinc-800 rounded-lg">
              <X size={20} />
            </button>
          </div>
    
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-zinc-900">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-3 text-sm border ${
                  msg.sender === 'user' 
                    ? 'bg-orange-500 text-zinc-950 border-orange-500 rounded-2xl rounded-tr-none' 
                    : 'bg-zinc-800 border-zinc-700 text-zinc-300 rounded-2xl rounded-tl-none'
                }`}>
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                </div>
              </div>
            ))}
            
            {isTyping && (
              <div className="flex justify-start">
                <div className="max-w-[80%] p-3 text-sm bg-zinc-800 border border-zinc-700 text-zinc-300 rounded-2xl rounded-tl-none flex gap-1 items-center h-10">
                  <span className="text-xs text-zinc-400 mr-1 italic">digitando</span>
                  <div className="w-1.5 h-1.5 bg-orange-500 animate-bounce rounded-full"></div>
                  <div className="w-1.5 h-1.5 bg-orange-500 animate-bounce rounded-full" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-1.5 h-1.5 bg-orange-500 animate-bounce rounded-full" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
    
          <div className="p-3 border-t border-zinc-800 bg-zinc-950 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Digite sua mensagem..."
              className="flex-1 bg-zinc-900 border border-zinc-800 text-zinc-100 px-4 py-3 text-sm focus:outline-none focus:border-orange-500 focus:ring-1 focus:ring-orange-500 placeholder-zinc-500 rounded-xl"
            />
            <button 
              onClick={handleSend}
              className="bg-orange-500 text-zinc-950 px-4 py-2 hover:bg-orange-400 transition-colors font-bold rounded-xl flex items-center justify-center"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Chat;
