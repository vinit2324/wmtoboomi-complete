import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Bot, User, Loader2, Sparkles, Trash2 } from 'lucide-react';
import { useToast } from '../components/Toast';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function AIAssistant() {
  const { showToast } = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadProjects = async () => {
    try {
      const response = await axios.get('http://localhost:7201/api/projects');
      setProjects(response.data.projects || []);
    } catch (error) {
      console.error('Error loading projects:', error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:7201/api/ai/chat', {
        message: input,
        projectId: selectedProject || null,
        history: messages.slice(-10).map(m => ({ role: m.role, content: m.content }))
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      showToast('AI request failed. Please check LLM configuration.', 'error');
      
      // Add fallback response
      const fallbackMessage: Message = {
        role: 'assistant',
        content: `I'm here to help with your webMethods to Boomi migration! Here are some things I can help with:

**Conversion Questions:**
- How do I convert a LOOP verb to Boomi ForEach?
- What's the Boomi equivalent of pub.string:concat?
- How do I handle BRANCH logic in Boomi?

**Migration Guidance:**
- Explain pipeline heap structure
- What requires manual review?
- How to convert Java services to Groovy?

**Best Practices:**
- Document Type to Profile conversion
- Adapter to Connector mapping
- Error handling patterns

${selectedProject ? `\nI have context about your selected project and can provide specific guidance based on its services and complexity.` : '\nSelect a project above for context-aware assistance.'}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, fallbackMessage]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    showToast('Chat cleared', 'info');
  };

  const suggestedQuestions = [
    "How do I convert LOOP to Boomi ForEach?",
    "What's the Boomi equivalent of pub.string:concat?",
    "How to handle BRANCH logic in Boomi?",
    "Explain webMethods pipeline heap structure",
    "How to convert Java service to Groovy?",
    "What requires manual review in migration?"
  ];

  return (
    <div className="p-6 h-[calc(100vh-120px)] flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-jade-blue to-jade-blue-light text-white rounded-lg p-6 mb-6 shadow-lg">
        <div className="flex items-center gap-3 mb-2">
          <Sparkles size={32} />
          <h1 className="text-3xl font-bold">AI Migration Assistant</h1>
        </div>
        <p className="text-jade-gold">Get help with webMethods to Boomi conversion, mapping guidance, and best practices</p>
      </div>

      {/* Project Selector */}
      <div className="bg-white rounded-lg shadow-lg p-4 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <label className="font-semibold text-jade-blue">Context Project:</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-jade-blue focus:outline-none min-w-[300px]"
            >
              <option value="">No project selected (general assistance)</option>
              {projects.map((project) => (
                <option key={project.projectId} value={project.projectId}>
                  {project.packageName} ({project.packageInfo?.services?.total || 0} services)
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={clearChat}
            className="px-4 py-2 text-gray-600 hover:text-red-600 flex items-center gap-2"
          >
            <Trash2 size={18} />
            Clear Chat
          </button>
        </div>
      </div>

      {/* Chat Container */}
      <div className="flex-1 bg-white rounded-lg shadow-lg flex flex-col overflow-hidden">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="mx-auto text-jade-blue mb-4" size={64} />
              <h3 className="text-xl font-semibold text-jade-blue mb-2">How can I help you today?</h3>
              <p className="text-gray-600 mb-6">Ask me anything about webMethods to Boomi migration</p>
              
              <div className="grid grid-cols-2 gap-3 max-w-2xl mx-auto">
                {suggestedQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => setInput(question)}
                    className="p-3 text-left border-2 border-gray-200 rounded-lg hover:border-jade-blue hover:bg-jade-blue hover:bg-opacity-5 transition-all text-sm text-gray-700"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((message, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.role === 'assistant' && (
                    <div className="w-10 h-10 rounded-full bg-jade-blue flex items-center justify-center flex-shrink-0">
                      <Bot className="text-white" size={20} />
                    </div>
                  )}
                  <div
                    className={`max-w-[70%] p-4 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-jade-blue text-white'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                    <div className={`text-xs mt-2 ${message.role === 'user' ? 'text-jade-gold' : 'text-gray-500'}`}>
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                  {message.role === 'user' && (
                    <div className="w-10 h-10 rounded-full bg-jade-gold flex items-center justify-center flex-shrink-0">
                      <User className="text-jade-blue-dark" size={20} />
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="flex gap-3">
                  <div className="w-10 h-10 rounded-full bg-jade-blue flex items-center justify-center">
                    <Bot className="text-white" size={20} />
                  </div>
                  <div className="bg-gray-100 p-4 rounded-lg">
                    <Loader2 className="animate-spin text-jade-blue" size={20} />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t p-4">
          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !loading && sendMessage()}
              placeholder="Ask about webMethods to Boomi migration..."
              className="flex-1 px-4 py-3 border-2 border-gray-300 rounded-lg focus:border-jade-blue focus:outline-none"
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="px-6 py-3 bg-jade-gold text-jade-blue-dark rounded-lg font-semibold hover:bg-jade-gold-dark disabled:opacity-50 flex items-center gap-2 shadow-md"
            >
              <Send size={20} />
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
