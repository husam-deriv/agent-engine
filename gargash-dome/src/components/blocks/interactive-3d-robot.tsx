'use client';

import { Suspense, lazy, useState } from 'react';
const Spline = lazy(() => import('@splinetool/react-spline'));

interface InteractiveRobotSplineProps {
  scene: string;
  className?: string;
}

export function InteractiveRobotSpline({ scene, className }: InteractiveRobotSplineProps) {
  const [hasError, setHasError] = useState(false);

  // Handle Spline errors
  const handleError = (err: any) => {
    console.error("Spline loading error:", err);
    setHasError(true);
  };

  if (hasError) {
    return (
      <div className={`w-full h-full flex items-center justify-center bg-gray-900 text-white ${className}`}>
        <div className="text-center p-4">
          <p className="text-red-400 mb-2">Failed to load 3D model</p>
          <button
            onClick={() => setHasError(false)}
            className="px-4 py-2 bg-[#f60021] text-white rounded"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <Suspense
      fallback={
        <div className={`w-full h-full flex items-center justify-center bg-gray-900 text-white ${className}`}>
          <div className="text-center">
            <svg className="animate-spin h-12 w-12 text-white mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l2-2.647z"></path>
            </svg>
            <p>Loading 3D experience...</p>
          </div>
        </div>
      }
    >
      <div className={className}>
        <Spline
          scene={scene}
          onError={handleError}
          style={{ width: '100%', height: '100%' }}
        />
      </div>
    </Suspense>
  );
}

