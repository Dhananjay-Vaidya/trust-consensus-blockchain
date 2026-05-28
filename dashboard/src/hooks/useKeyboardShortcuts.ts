import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { useSimulationStore } from '../store/simulationStore';

export function useKeyboardShortcuts() {
  const navigate  = useNavigate();
  const status    = useSimulationStore((s) => s.status);
  const stopSim   = useSimulationStore((s) => s.stopSimulation);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'SELECT' || tag === 'TEXTAREA') return;

      switch (e.key) {
        case '/':
          e.preventDefault();
          navigate('/');
          setTimeout(() => {
            (document.querySelector('button[data-start]') as HTMLButtonElement)?.focus();
          }, 100);
          break;
        case 'Escape':
          if (status === 'running') {
            if (confirm('Stop the running simulation?')) void stopSim();
          }
          break;
        case '1': navigate('/'); break;
        case '2': navigate('/metrics'); break;
        case '3': navigate('/attack-lab'); break;
        case '4': navigate('/scenarios'); break;
        case '5': navigate('/results'); break;
        case '6': navigate('/compare'); break;
      }

      if (e.ctrlKey) {
        switch (e.key) {
          case 'e': e.preventDefault(); navigate('/export'); break;
          case 'r': e.preventDefault(); navigate('/results'); break;
          case 'c': e.preventDefault(); navigate('/compare'); break;
        }
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [navigate, status, stopSim]);
}
