'use client';

import InteractiveHero from "../components/blocks/hero-section";
import { InteractiveRobotSpline } from "../components/blocks/interactive-3d-robot";
import { Features } from "../components/blocks/features";
import { useEffect } from 'react';
import Link from 'next/link';

const RobotSection = () => {
  const ROBOT_SCENE_URL = "https://prod.spline.design/BDeVEmrUYvNM2Y6B/scene.splinecode";

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-black">
      {/* 3D Robot Background */}
      <InteractiveRobotSpline
        scene={ROBOT_SCENE_URL}
        className="absolute inset-0 z-0" 
      />

      {/* Content Overlay */}
      <div className="
        absolute inset-0 z-10
        pt-20 md:pt-32 lg:pt-40
        px-4 md:px-8            
        pointer-events-none
        bg-gradient-to-b from-black/70 via-transparent to-black/80     
      ">
        <div className="
          text-center
          text-white
          drop-shadow-lg
          w-full max-w-2xl
          mx-auto
        ">
          <h1 className="
            text-2xl md:text-3xl lg:text-4xl xl:text-5xl 
            font-bold 
            mb-6
          ">
            DerivX Triage Agent
          </h1>
          
          <p className="text-lg md:text-xl text-gray-300 mb-8">
            Agent Engine is the Future of Intelligent Agent to Agent and Tribe to Tribe communication, 
            designed to reduce solution building within Deriv.
          </p>
          
          <div className="
            flex flex-col sm:flex-row gap-4 justify-center
            pointer-events-auto
          ">
            <Link href="/dashboard">
              <button className="
                bg-[#f60021] text-white px-6 py-3 rounded-lg
                font-medium hover:bg-opacity-90 transition-all
                shadow-lg hover:shadow-xl
              ">
                Discover Features
              </button>
            </Link>
            
            <button className="
              bg-transparent text-white px-6 py-3 rounded-lg
              font-medium border border-white/30 hover:border-white/60
              transition-all
            ">
              Learn More
            </button>
          </div>
        </div>
      </div>
      
      {/* Accent line at the bottom */}
      <div className="absolute bottom-0 left-0 right-0 w-full h-1 bg-gradient-to-r from-transparent via-[#f60021]/20 to-transparent"></div>
    </div>
  );
};

export default function Home() {
  return (
    <>
      <InteractiveHero 
        brandName="Deriv Agent Engine"
        headline="Unifying Vision Through"
        rotatingTexts={["Intelligence", "Innovation", "Integration", "Insights", "Interaction"]}
        subheadline="A unified AI platform bringing together Deriv's AI Agents, enhancing customer touchpoints, and empowering internal teams with data-driven solutions."
        ctaText="Experience Agent Engine"
        announcementText="Introducing the Future of Enterprise Connectivity"
      />
      
      <RobotSection />
      
      <Features />
    </>
  );
}
