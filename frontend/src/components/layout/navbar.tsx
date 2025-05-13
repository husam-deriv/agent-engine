import Link from 'next/link';
import Image from 'next/image';
import { Button } from '@/components/ui/button';

export default function Navbar() {
  return (
    <nav className="border-b">
      <div className="container flex items-center justify-between py-4">
        <div className="flex items-center gap-3 pl-20">
          <Link href="/" className="flex items-center gap-2">
            <Image 
              src="/agent-engine.svg" 
              alt="Agent Engine Logo" 
              width={32} 
              height={32} 
            />
            <span className="text-2xl font-bold">Agent Engine</span>
          </Link>
          <span className="text-gray-500">|</span>
          <div className="flex items-center gap-2">
            <Image 
              src="/GargashLogo.png" 
              alt="Gargash Logo" 
              width={28} 
              height={28} 
            />
            <span className="font-medium">Gargash</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost">Create Agent</Button>
          </Link>
          <Link href="/chat">
            <Button variant="ghost">Chat with Agent</Button>
          </Link>
          <Link href="/files">
            <Button variant="ghost">View Files</Button>
          </Link>
        </div>
      </div>
    </nav>
  );
} 