'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { createAgentTeamInitial } from '@/lib/api';
import { QuestionAnswer, UserFiles } from '@/lib/api';

const formSchema = z.object({
  description: z.string().min(10, 'Description must be at least 10 characters'),
  industry: z.string().min(2, 'Industry is required'),
  department: z.string().min(2, 'Department is required'),
  csvFile: z.any().optional(),
  csvDesc: z.string().optional(),
  docFile: z.any().optional(),
  docDesc: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

export default function CreateAgentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [questions, setQuestions] = useState<string[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [files, setFiles] = useState<UserFiles>({});
  const [initialDescription, setInitialDescription] = useState('');

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      description: '',
      industry: '',
      department: '',
      csvDesc: '',
      docDesc: '',
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, fileType: 'csv' | 'doc') => {
    if (e.target.files && e.target.files[0]) {
      const field = fileType === 'csv' ? 'csvFile' : 'docFile';
      form.setValue(field, e.target.files[0]);
    }
  };

  const onSubmit = async (data: FormValues) => {
    try {
      setLoading(true);
      const response = await createAgentTeamInitial(
        data.description,
        data.industry,
        data.department,
        data.csvFile,
        data.csvDesc,
        data.docFile,
        data.docDesc
      );

      setQuestions(response.questions);
      setFiles(response.files);
      setInitialDescription(response.description);
      
      toast.success('Questions generated successfully');
    } catch (error) {
      console.error('Error creating agent team:', error);
      toast.error('Error creating agent team');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (index: number, value: string) => {
    const newAnswers = [...answers];
    newAnswers[index] = value;
    setAnswers(newAnswers);
  };

  const submitAnswers = async () => {
    try {
      setLoading(true);
      
      // Check if all questions are answered
      if (answers.filter(Boolean).length !== questions.length) {
        toast.error('Please answer all questions');
        return;
      }

      // Format the question-answer pairs
      const qaPrompt: QuestionAnswer[] = questions.map((question, index) => ({
        question,
        answer: answers[index],
      }));

      // Store in sessionStorage for the next step
      sessionStorage.setItem('qaPrompt', JSON.stringify(qaPrompt));
      sessionStorage.setItem('description', initialDescription);
      sessionStorage.setItem('files', JSON.stringify(files));
      
      // Navigate to the next step
      router.push('/create-agent-prd');
    } catch (error) {
      console.error('Error submitting answers:', error);
      toast.error('Error submitting answers');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Create AI Agent Team</h1>

      {!questions.length ? (
        <Card>
          <CardHeader>
            <CardTitle>Step 1: Initial Project Description</CardTitle>
            <CardDescription>
              Describe your project and provide any necessary files
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Project Description</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="Describe what you want your AI Agent Team to do..."
                          {...field}
                          rows={5}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="grid grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="industry"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Industry</FormLabel>
                        <FormControl>
                          <Input placeholder="e.g. Healthcare, Finance, Education" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="department"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Department</FormLabel>
                        <FormControl>
                          <Input placeholder="e.g. Marketing, HR, Sales" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <FormItem>
                    <FormLabel>CSV File (Optional)</FormLabel>
                    <FormControl>
                      <Input
                        type="file"
                        accept=".csv"
                        onChange={(e) => handleFileChange(e, 'csv')}
                      />
                    </FormControl>
                  </FormItem>

                  <FormField
                    control={form.control}
                    name="csvDesc"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>CSV Description</FormLabel>
                        <FormControl>
                          <Input placeholder="Describe what's in the CSV file" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <FormItem>
                    <FormLabel>Document (Optional)</FormLabel>
                    <FormControl>
                      <Input
                        type="file"
                        accept=".pdf,.docx,.pptx,.html"
                        onChange={(e) => handleFileChange(e, 'doc')}
                      />
                    </FormControl>
                  </FormItem>

                  <FormField
                    control={form.control}
                    name="docDesc"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Document Description</FormLabel>
                        <FormControl>
                          <Input placeholder="Describe what's in the document" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <Button type="submit" disabled={loading}>
                  {loading ? 'Processing...' : 'Generate Questions'}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Step 2: Answer Clarifying Questions</CardTitle>
            <CardDescription>
              Answer the following questions to help us better understand your needs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {questions.map((question, index) => (
                <div key={index} className="space-y-2">
                  <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">Question {index + 1}</label>
                  <p className="text-sm text-muted-foreground">{question}</p>
                  <Textarea
                    placeholder="Your answer..."
                    value={answers[index] || ''}
                    onChange={(e) => handleAnswerChange(index, e.target.value)}
                    rows={3}
                  />
                </div>
              ))}

              <Button onClick={submitAnswers} disabled={loading}>
                {loading ? 'Processing...' : 'Submit Answers'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
