'use client';

import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface MermaidRendererProps {
  chart: string;
}

export function MermaidRenderer({ chart }: MermaidRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mermaidId = `mermaid-${Math.random().toString(36).substring(2, 11)}`;

  useEffect(() => {
    if (containerRef.current) {
      try {
        mermaid.render(mermaidId, chart).then(({ svg }) => {
          if (containerRef.current) {
            containerRef.current.innerHTML = svg;
          }
        });
      } catch (error) {
        console.error('Mermaid rendering error:', error);
        if (containerRef.current) {
          containerRef.current.innerHTML = `<div class="p-2 bg-red-100 border border-red-300 rounded">Error rendering diagram</div>`;
        }
      }
    }
  }, [chart, mermaidId]);

  return <div ref={containerRef} className="my-4" />;
} 