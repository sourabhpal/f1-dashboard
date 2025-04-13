import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

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
              <Link href="/standings" className="text-gray-300 hover:text-white transition-colors nav-link font-goldman">
                Standings
              </Link>
              <Link href="/races" className="text-gray-300 hover:text-white transition-colors nav-link font-goldman">
                Race Data
              </Link>
              <Link href="/schedule" className="text-gray-300 hover:text-white transition-colors nav-link font-goldman">
                Schedule
              </Link>
              <Link href="/circuits" className="text-gray-300 hover:text-white transition-colors nav-link font-goldman">
                Circuits
              </Link>
              <Link href="/drivers" className="text-gray-300 hover:text-white transition-colors nav-link font-goldman">
                Drivers
              </Link>
              <Link href="/fastf1" className="text-gray-300 hover:text-white transition-colors nav-link font-goldman">
                FastF1
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
            <Link href="/" className="text-red-500 hover:text-red-400 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50 inline-flex items-center nav-link font-goldman">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1.5" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
              </svg>
              Home
            </Link>
            <Link href="/standings" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50 nav-link font-goldman">
              Standings
            </Link>
            <Link href="/races" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50 nav-link font-goldman">
              Race Data
            </Link>
            <Link href="/schedule" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50 nav-link font-goldman">
              Schedule
            </Link>
            <Link href="/circuits" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50 nav-link font-goldman">
              Circuits
            </Link>
            <Link href="/drivers" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50 nav-link font-goldman">
              Drivers
            </Link>
            <Link href="/fastf1" className="text-gray-300 hover:text-red-500 block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200 hover:bg-gray-800/50 nav-link font-goldman">
              FastF1
            </Link>
          </div>
        </div>
      )}
    </nav>
  );
} 