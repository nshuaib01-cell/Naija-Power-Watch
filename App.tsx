import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import GridDashboard from './components/GridDashboard';
import OutageReporter from './components/OutageReporter';
import { AnimatePresence, motion } from 'motion/react';

export default function App() {
  const [activeView, setActiveView] = useState<'dashboard' | 'reporter'>('dashboard');

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar Navigation */}
      <Sidebar activeView={activeView} onViewChange={setActiveView} />

      {/* Main Content Area */}
      <main className="flex-1 lg:ml-[260px] transition-all duration-300">
        <AnimatePresence mode="wait">
          {activeView === 'dashboard' ? (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <GridDashboard />
            </motion.div>
          ) : (
            <motion.div
              key="reporter"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3 }}
            >
              <OutageReporter />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Global Footer */}
        <footer className="p-8 text-center border-t border-gray-100 mt-auto">
          <p className="text-xs text-gray-400 font-medium">
            &copy; {new Date().getFullYear()} NaijaGrid Smart Monitoring System. 
            <span className="mx-2">|</span>
            Developed for National Grid Reliability.
          </p>
        </footer>
      </main>
    </div>
  );
}
