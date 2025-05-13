'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { Avatar } from '@/components/ui/avatar';
import { toast } from 'sonner';
import { listAgentTeams, inferenceAgentTeam, AgentTeamSummary } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMermaid from 'remark-mermaidjs';
import mermaid from 'mermaid';
import { MermaidRenderer } from '@/components/ui/mermaid-renderer';

interface Message {
  role: 'user' | 'agent';
  content: string;
}

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [teams, setTeams] = useState<AgentTeamSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTeam, setSelectedTeam] = useState<AgentTeamSummary | null>(null);
  const [userInput, setUserInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [isThinking, setIsThinking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize mermaid
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose'
    });
  }, []);

  useEffect(() => {
    const fetchTeams = async () => {
      try {
        setLoading(true);
        const response = await listAgentTeams();
        setTeams(response.teams || []);
      } catch (error) {
        console.error('Error fetching teams:', error);
        toast.error('Error loading agent teams');
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();

    // If there's a team in params or session storage, select it
    const teamName = searchParams.get('team');
    const lastCreatedTeam = sessionStorage.getItem('lastCreatedTeam');
    
    if (teamName || lastCreatedTeam) {
      const nameToUse = teamName || lastCreatedTeam;
      
      // Clear last created team from session storage
      if (lastCreatedTeam) {
        sessionStorage.removeItem('lastCreatedTeam');
      }

      // Once teams are loaded, find and select the team
      if (nameToUse) {
        const selectTeamIfExists = async () => {
          const response = await listAgentTeams();
          const teams = response.teams || [];
          const team = teams.find((t: AgentTeamSummary) => t.team_name === nameToUse);
          if (team) {
            setSelectedTeam(team);
            
            // Add welcome message
            setMessages([
              {
                role: 'agent',
                content: `I'm your ${team.team_name} assistant. How can I help you today?`
              }
            ]);
          }
        };
        
        selectTeamIfExists();
      }
    }
  }, [searchParams]);

  useEffect(() => {
    // Scroll to bottom of messages
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleTeamSelect = (team: AgentTeamSummary) => {
    setSelectedTeam(team);
    setMessages([
      {
        role: 'agent',
        content: `I'm your ${team.team_name} assistant. How can I help you today?`
      }
    ]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!userInput.trim() || !selectedTeam) return;
    
    // Add user message
    const userMessage = { role: 'user' as const, content: userInput };
    setMessages((prev) => [...prev, userMessage]);
    setUserInput('');
    setIsThinking(true);

    try {
      // Call API for inference
      const response = await inferenceAgentTeam(selectedTeam.team_name, userInput);
      
      // Add agent response
      setMessages((prev) => [
        ...prev, 
        { role: 'agent' as const, content: response.result }
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Add error message
      setMessages((prev) => [
        ...prev, 
        { 
          role: 'agent' as const, 
          content: 'Sorry, I encountered an error processing your request. Please try again.'
        }
      ]);
      
      toast.error('Error sending message');
    } finally {
      setIsThinking(false);
    }
  };

  const backToTeams = () => {
    setSelectedTeam(null);
    setMessages([]);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Chat with AI Agent Teams</h1>

      {!selectedTeam ? (
        <>
          {loading ? (
            <p>Loading agent teams...</p>
          ) : teams.length === 0 ? (
            <div className="text-center py-12">
              <h2 className="text-xl font-semibold mb-2">No Agent Teams Available</h2>
              <p className="text-muted-foreground mb-6">
                You haven't created any agent teams yet.
              </p>
              <Button onClick={() => router.push('/')}>Create Your First Agent Team</Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {teams.map((team) => (
                <Card key={team.team_name} className="cursor-pointer hover:border-primary" onClick={() => handleTeamSelect(team)}>
                  <CardHeader>
                    <CardTitle>{team.team_name}</CardTitle>
                    <CardDescription>
                      Design Pattern: {team.design_pattern}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">
                      {team.description || 'No description available'}
                    </p>
                  </CardContent>
                  <CardFooter>
                    <Button className="w-full" onClick={() => handleTeamSelect(team)}>
                      Chat with Team
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          )}
        </>
      ) : (
        <Card className="mb-8">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>{selectedTeam.team_name}</CardTitle>
              <CardDescription>
                {selectedTeam.design_pattern} - {selectedTeam.description}
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={backToTeams}>
              Back to Teams
            </Button>
          </CardHeader>
          <Separator />
          <CardContent className="p-4 h-[400px] overflow-y-auto">
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex items-start gap-3 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'agent' && (
                    <Avatar className="h-8 w-8 bg-primary text-white">
                      <span className="text-xs">AI</span>
                    </Avatar>
                  )}
                  <div
                    className={`rounded-lg px-4 py-2 max-w-[80%] ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    {message.role === 'user' ? (
                      <p className="text-sm whitespace-pre-line">{message.content}</p>
                    ) : (
                      <div className="prose dark:prose-invert prose-sm max-w-none">
                        <ReactMarkdown 
                          remarkPlugins={[remarkGfm]}
                          components={{
                            p: ({ node, ...props }) => <p className="my-1" {...props} />,
                            h1: ({ node, ...props }) => <h1 className="font-bold mt-4 mb-2 first:mt-0" {...props} />,
                            h2: ({ node, ...props }) => <h2 className="font-bold mt-4 mb-2 first:mt-0" {...props} />,
                            h3: ({ node, ...props }) => <h3 className="font-bold mt-4 mb-2 first:mt-0" {...props} />,
                            ul: ({ node, ...props }) => <ul className="pl-6 my-2" {...props} />,
                            ol: ({ node, ...props }) => <ol className="pl-6 my-2" {...props} />,
                            li: ({ node, ...props }) => <li className="my-1" {...props} />,
                            a: ({ node, ...props }) => <a className="text-blue-500 hover:underline" {...props} />,
                            code: ({ node, inline, className, children, ...props }: any) => {
                              const match = /language-(\w+)/.exec(className || '');
                              const language = match && match[1];
                              
                              if (inline) {
                                return <code className="bg-gray-200 dark:bg-gray-800 px-1 py-0.5 rounded" {...props}>{children}</code>;
                              }
                              
                              if (language === 'mermaid') {
                                return <MermaidRenderer chart={String(children)} />;
                              }
                              
                              return <code className="block bg-gray-200 dark:bg-gray-800 p-2 rounded-md my-2 overflow-x-auto" {...props}>{children}</code>;
                            }
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                  {message.role === 'user' && (
                    <Avatar className="h-8 w-8 bg-secondary text-secondary-foreground">
                      <span className="text-xs">You</span>
                    </Avatar>
                  )}
                </div>
              ))}
              {isThinking && (
                <div className="flex items-start gap-3">
                  <Avatar className="h-8 w-8 bg-primary text-white">
                    <span className="text-xs">AI</span>
                  </Avatar>
                  <div className="rounded-lg px-4 py-2 bg-muted">
                    <p className="text-sm">Thinking...</p>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </CardContent>
          <Separator />
          <CardFooter className="p-4">
            <form onSubmit={handleSubmit} className="flex w-full gap-2">
              <Input
                placeholder="Type your message..."
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                disabled={isThinking}
              />
              <Button type="submit" disabled={isThinking || !userInput.trim()}>
                Send
              </Button>
            </form>
          </CardFooter>
        </Card>
      )}
    </div>
  );
} 