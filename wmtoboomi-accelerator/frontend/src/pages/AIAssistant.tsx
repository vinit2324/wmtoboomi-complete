import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Send,
  Bot,
  User,
  Loader2,
  Code,
  Lightbulb,
  AlertCircle,
} from 'lucide-react';
import { aiApi, projectsApi } from '../utils/api';
import { useStore } from '../stores/useStore';
import type { AIMessage, Project } from '../types';

export default function AIAssistant() {
  const { currentCustomer } = useStore();
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [input, setInput] = useState('');
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: projectsData } = useQuery({
    queryKey: ['projects', currentCustomer?.customerId],
    queryFn: async () => {
      const response = await projectsApi.list(currentCustomer?.customerId);
      return response.data;
    },
    enabled: !!currentCustomer,
  });

  const projects = projectsData?.projects || [];

  const chatMutation = useMutation({
    mutationFn: async (message: string) => {
      if (!currentCustomer) throw new Error('No customer selected');
      return aiApi.chat({
        customerId: currentCustomer.customerId,
        projectId: selectedProjectId || undefined,
        message,
        conversationHistory: messages,
        includeContext: !!selectedProjectId,
      });
    },
    onSuccess: (response) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.data.message,
          timestamp: new Date().toISOString(),
        },
      ]);
    },
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || chatMutation.isPending) return;

    const userMessage: AIMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    chatMutation.mutate(input.trim());
  };

  const suggestedQuestions = [
    'How do I convert pub.string:concat to Boomi?',
    'Explain the webMethods pipeline heap structure',
    'What are the 9 flow verbs in webMethods?',
    'How does Boomi handle loops differently?',
    'Convert a BRANCH/LOOP combination to Boomi',
    'Generate a Groovy script template for data transformation',
  ];

  if (!currentCustomer) {
    return (
      <div className="card text-center py-12 animate-fadeIn">
        <AlertCircle className="w-16 h-16 mx-auto text-yellow-500 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Customer Selected</h3>
        <p className="text-gray-500">
          Please select a customer with LLM settings configured to use the AI Assistant.
        </p>
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-10rem)] flex flex-col animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Assistant</h1>
          <p className="text-gray-500">
            Get help with webMethods to Boomi migration questions
          </p>
        </div>
        <div className="flex items-center gap-4">
          <select
            className="input w-64"
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
          >
            <option value="">No project context</option>
            {projects.map((project: Project) => (
              <option key={project.projectId} value={project.projectId}>
                {project.packageName}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex gap-4 min-h-0">
        {/* Messages */}
        <div className="flex-1 bg-white rounded-lg border border-gray-200 flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-center">
                <Bot className="w-16 h-16 text-jade-500 mb-4" />
                <h3 className="text-lg font-medium mb-2">
                  webMethods to Boomi Migration Assistant
                </h3>
                <p className="text-gray-500 mb-6 max-w-md">
                  Ask me anything about converting webMethods components to Boomi,
                  mapping wMPublic services, or understanding flow verbs.
                </p>
                <div className="grid grid-cols-2 gap-2 max-w-lg">
                  {suggestedQuestions.slice(0, 4).map((question) => (
                    <button
                      key={question}
                      onClick={() => {
                        setInput(question);
                      }}
                      className="p-3 text-left text-sm bg-gray-50 hover:bg-jade-50 rounded-lg border border-gray-200 hover:border-jade-300 transition-colors"
                    >
                      <Lightbulb className="w-4 h-4 text-jade-500 mb-1" />
                      {question}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${
                      message.role === 'user'
                        ? 'bg-jade-500 text-white'
                        : 'bg-gray-100 text-gray-900'
                    }`}
                  >
                    <div className="flex items-center mb-2">
                      {message.role === 'user' ? (
                        <User className="w-4 h-4 mr-2" />
                      ) : (
                        <Bot className="w-4 h-4 mr-2" />
                      )}
                      <span className="text-xs opacity-75">
                        {message.role === 'user' ? 'You' : 'Assistant'}
                      </span>
                    </div>
                    <div className="whitespace-pre-wrap text-sm">
                      {message.content}
                    </div>
                  </div>
                </div>
              ))
            )}
            {chatMutation.isPending && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-4">
                  <Loader2 className="w-5 h-5 animate-spin text-jade-500" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
            <div className="flex gap-2">
              <input
                type="text"
                className="input flex-1"
                placeholder="Ask about webMethods to Boomi conversion..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={chatMutation.isPending}
              />
              <button
                type="submit"
                className="btn-primary"
                disabled={!input.trim() || chatMutation.isPending}
              >
                {chatMutation.isPending ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Sidebar */}
        <div className="w-80 space-y-4">
          {/* Quick Actions */}
          <div className="card">
            <h3 className="font-semibold mb-3">Quick Questions</h3>
            <div className="space-y-2">
              {suggestedQuestions.map((question) => (
                <button
                  key={question}
                  onClick={() => setInput(question)}
                  className="w-full p-2 text-left text-sm hover:bg-gray-50 rounded-lg transition-colors"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>

          {/* Context Info */}
          {selectedProjectId && (
            <div className="card bg-jade-50">
              <h3 className="font-semibold mb-2 text-jade-800">Project Context</h3>
              <p className="text-sm text-jade-700">
                AI responses will include context from the selected project's
                services, flow verbs, and wMPublic invocations.
              </p>
            </div>
          )}

          {/* Tips */}
          <div className="card">
            <h3 className="font-semibold mb-3">Tips</h3>
            <ul className="text-sm text-gray-600 space-y-2">
              <li>• Select a project to include context</li>
              <li>• Ask about specific wMPublic services</li>
              <li>• Request Groovy script generation</li>
              <li>• Ask for flow verb conversion help</li>
              <li>• Get XPath generation assistance</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
