import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '../lib/utils';
import { Menu, X } from 'lucide-react';
import { Button } from './ui/button';
import { useTheme } from '../lib/ThemeProvider';

const menuItems = [
    { name: 'Agent Roadmap', href: '/roadmap' },
    { name: 'Agents', href: '/ai-solutions' },
    { name: 'Data Store', href: '/fileupload' },
];

const Navbar = () => {
  const [menuState, setMenuState] = useState(false);
  const { theme } = useTheme();

  return (
    <header>
      <nav
        data-state={menuState && 'active'}
        className="group fixed z-20 w-full border-b border-dashed bg-background backdrop-blur md:relative dark:bg-zinc-950/50 lg:dark:bg-transparent">
        <div className="m-auto max-w-5xl px-6">
          <div
            className="flex flex-wrap items-center justify-between gap-6 py-3 lg:gap-0 lg:py-4">
            <div className="flex w-full justify-between lg:w-auto">
              <Link to="/" aria-label="home" className="flex items-center space-x-2">
                <img src="/agent-engine.svg" alt="Agent Engine Logo" className="h-8 w-auto" />
                <span className="text-foreground font-semibold text-lg">Agent Engine</span>
              </Link>

              <button
                onClick={() => setMenuState(!menuState)}
                aria-label={menuState ? 'Close Menu' : 'Open Menu'}
                className="relative z-20 -m-2.5 -mr-4 block cursor-pointer p-2.5 lg:hidden">
                <Menu
                  className="group-data-[state=active]:rotate-180 group-data-[state=active]:scale-0 group-data-[state=active]:opacity-0 m-auto size-6 duration-200" />
                <X
                  className="group-data-[state=active]:rotate-0 group-data-[state=active]:scale-100 group-data-[state=active]:opacity-100 absolute inset-0 m-auto size-6 -rotate-180 scale-0 opacity-0 duration-200" />
              </button>
            </div>

            <div
              className="bg-background group-data-[state=active]:block lg:group-data-[state=active]:flex mb-6 hidden w-full flex-wrap items-center justify-end space-y-8 rounded-3xl border p-6 shadow-2xl shadow-zinc-300/20 md:flex-nowrap lg:m-0 lg:flex lg:w-fit lg:gap-6 lg:space-y-0 lg:border-transparent lg:bg-transparent lg:p-0 lg:shadow-none dark:shadow-none dark:lg:bg-transparent">
              <div className="lg:pr-4">
                <ul className="space-y-6 text-base lg:flex lg:gap-8 lg:space-y-0 lg:text-sm">
                  {menuItems.map((item, index) => (
                    <li key={index}>
                      <Link
                        to={item.href}
                        className="text-muted-foreground hover:text-accent-foreground block duration-150">
                        <span>{item.name}</span>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </nav>
    </header>
  );
};

export default Navbar; 