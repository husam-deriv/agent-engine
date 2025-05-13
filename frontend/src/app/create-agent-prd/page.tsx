'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { toast } from 'sonner';
import { createAgentTeamPRD, QuestionAnswer, UserFiles, ToolInfo } from '@/lib/api';

// Define the list of available tools with their descriptions
const availableTools: ToolInfo[] = [
  {
    name: 'search_web',
    description: 'Search the internet for up-to-date information, useful when you need facts, current events, or domain knowledge.',
  },
  {
    name: 'query_csv_data',
    description: 'Query and filter CSV data using pandas syntax, useful for analyzing tabular data without writing code.',
  },
  {
    name: 'deep_research',
    description: 'Perform comprehensive research on complex topics with analysis and source verification.',
  },
  {
    name: 'create_mermaid_diagram',
    description: 'Generate visual diagrams from text descriptions for flowcharts, sequence diagrams, and other visualizations.',
  },
  {
    name: 'run_interactive_pipeline',
    description: 'Build and run machine learning models on CSV data using natural language queries.',
  },
  {
    name: 'rag_collection_query',
    description: 'Search vector databases for semantically relevant information from previously embedded document collections.',
  },
];

export default function CreateAgentPRDPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [qaPrompt, setQaPrompt] = useState<QuestionAnswer[]>([]);
  const [description, setDescription] = useState<string>('');
  const [files, setFiles] = useState<UserFiles>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Get data from sessionStorage
    try {
      const qaPromptStr = sessionStorage.getItem('qaPrompt');
      const descriptionStr = sessionStorage.getItem('description');
      const filesStr = sessionStorage.getItem('files');

      if (!qaPromptStr || !descriptionStr) {
        setError('Missing required data. Please go back and fill out the form.');
        return;
      }

      setQaPrompt(JSON.parse(qaPromptStr));
      setDescription(descriptionStr);
      
      if (filesStr) {
        setFiles(JSON.parse(filesStr));
      }
    } catch (error) {
      console.error('Error loading data from sessionStorage:', error);
      setError('Error loading your data. Please try again.');
    }
  }, []);

  const generateAgentTeam = async () => {
    try {
      setLoading(true);
      setProgress(10);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 2000);

      // Call API to create the agent team
      const result = await createAgentTeamPRD(
        qaPrompt,
        description,
        files,
        availableTools
      );

      clearInterval(progressInterval);
      setProgress(100);

      toast.success('Agent team created successfully!');
      
      // Store the team name for the chat page
      sessionStorage.setItem('lastCreatedTeam', result.team_name);
      
      // Navigate to the chat page after a brief delay
      setTimeout(() => {
        router.push('/chat');
      }, 1500);
    } catch (error) {
      console.error('Error creating agent team:', error);
      toast.error('Error creating agent team');
      setProgress(0);
      setLoading(false);
    }
  };

  if (error) {
    return (
      <div className="max-w-3xl mx-auto">
        <Alert variant="destructive" className="mb-4">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={() => router.push('/')}>Go Back</Button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Create Agent PRD</h1>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Generate Agent Team</CardTitle>
          <CardDescription>
            Based on your description and answers, we'll generate a custom AI agent team.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium">Project Description</h3>
              <p className="text-sm text-muted-foreground mt-1">{description}</p>
            </div>

            <div>
              <h3 className="text-lg font-medium">Clarifying Questions & Answers</h3>
              <div className="space-y-4 mt-2">
                {qaPrompt.map((qa, index) => (
                  <div key={index} className="border rounded-md p-3">
                    <p className="font-medium">Q: {qa.question}</p>
                    <p className="text-sm text-muted-foreground mt-1">A: {qa.answer}</p>
                  </div>
                ))}
              </div>
            </div>

            {(files.user_csv || files.user_doc) && (
              <div>
                <h3 className="text-lg font-medium">Uploaded Files</h3>
                <ul className="list-disc list-inside text-sm text-muted-foreground mt-1">
                  {files.user_csv && (
                    <li>
                      CSV: {files.user_csv.name} - {files.user_csv.desc}
                    </li>
                  )}
                  {files.user_doc && (
                    <li>
                      Document: {files.user_doc.name} - {files.user_doc.desc}
                    </li>
                  )}
                </ul>
              </div>
            )}

            {loading ? (
              <div className="space-y-2">
                <Progress value={progress} className="w-full" />
                <p className="text-sm text-center text-muted-foreground">
                  Creating your AI agent team... {progress}%
                </p>
              </div>
            ) : (
              <Button onClick={generateAgentTeam} className="w-full">
                Generate Agent Team
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 