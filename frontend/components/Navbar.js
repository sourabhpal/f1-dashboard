import Link from 'next/link';
import Image from 'next/image';
import { useState } from 'react';

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center">
              <Image
                src="/images/f1-logo.png"
                alt="F1 Logo"
                width={160}
                height={25}
                className="h-8 sm:h-9 md:h-10 w-auto object-contain"
                priority
                quality={100}
              />
            </Link>
            <div className="hidden md:flex items-center space-x-8 ml-12">
              <Link href="/standings" className="text-gray-300 hover:text-white transition-colors">
                Standings
              </Link>
              <Link href="/races" className="text-gray-300 hover:text-white transition-colors">
                Race Data
              </Link>
              <Link href="/schedule" className="text-gray-300 hover:text-white transition-colors">
                Schedule
              </Link>
              <Link href="/circuits" className="text-gray-300 hover:text-white transition-colors">
                Circuits
              </Link>
              <Link href="/drivers" className="text-gray-300 hover:text-white transition-colors">
                Drivers
              </Link>
            </div>
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none"
            >
              <span className="sr-only">Open main menu</span>
              {!isOpen ? (
                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              ) : (
                <svg className="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {isOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            <Link href="/" className="text-red-500 hover:text-red-400 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50 inline-flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
              </svg>
              Home
            </Link>
            <Link href="/standings" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50">
              Standings
            </Link>
            <Link href="/races" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50">
              Race Data
            </Link>
            <Link href="/drivers" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50">
              Drivers
            </Link>
            <Link href="/teams" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50">
              Teams
            </Link>
            <Link href="/qualifying" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50">
              Qualifying
            </Link>
            <Link href="/timing" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50">
              Timing
            </Link>
            <Link href="/pit-stops" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50">
              Pit Stops
            </Link>
            <Link href="/weather" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50">
              Weather
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
} 