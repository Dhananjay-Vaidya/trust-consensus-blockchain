import { useState } from 'react';
import toast from 'react-hot-toast';

import { Badge } from '../components/ui/Badge';

const FIGURES = [
  { id: '1', label: 'Fig 1: F1 score vs episode (all agents × all attacks)' },
  { id: '2', label: 'Fig 2: Trust separation over time' },
  { id: '3', label: 'Fig 3: Baseline comparison bar chart' },
  { id: '4', label: 'Fig 4: Ablation study' },
  { id: '5', label: 'Fig 5: Scalability curves' },
  { id: '6', label: 'Fig 6: Malicious fraction sweep' },
  { id: '7', label: 'Fig 7: Trust network graph (PNG snapshot)' },
  { id: '8', label: 'Fig 8: Scenario comparison' },
];

export function ExportPage() {
  const [selected, setSelected] = useState<Set<string>>(new Set(['1','2','3']));
  const [format, setFormat]     = useState('png');
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [recordingUrl, setRecordingUrl]   = useState<string | null>(null);

  const toggle = (id: string) => setSelected((s) => {
    const n = new Set(s);
    n.has(id) ? n.delete(id) : n.add(id);
    return n;
  });

  const exportFigures = () => {
    const ids = [...selected].join(',');
    window.open(`/export/figures?figures=${ids}&format=${format}`, '_blank');
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true });
      const mr = new MediaRecorder(stream, { mimeType: 'video/webm' });
      const chunks: Blob[] = [];
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
      mr.onstop = () => {
        const blob = new Blob(chunks, { type: 'video/webm' });
        setRecordingUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      setMediaRecorder(mr);
      setRecording(true);
      toast('🔴 Recording started — 90 second limit', { duration: 3000 });
      setTimeout(() => { mr.stop(); setRecording(false); }, 90000);
    } catch {
      toast.error('Screen capture not available');
    }
  };

  const stopRecording = () => {
    mediaRecorder?.stop();
    setRecording(false);
  };

  const BIBTEX = `@inproceedings{vaidya2025tdcb,
  title     = {{ABAC-TDCB-FHE}: Adaptive Trust-Based Delegated Consensus
               for Secure {IoT} Blockchains with Reinforcement Learning},
  author    = {Vaidya, Dhananjay and others},
  booktitle = {Proceedings of IEEE International Conference on
               Blockchain and Cryptocurrency (ICBC)},
  year      = {2025},
  note      = {Under review}
}`;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 800 }}>
      <div>
        <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>Export</div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Export figures, data, and LaTeX tables for IEEE paper submission.
        </div>
      </div>

      {/* Figure Export */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 18 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>
          Figure Export
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 14 }}>
          {FIGURES.map((f) => (
            <label key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)' }}>
              <input type="checkbox" checked={selected.has(f.id)} onChange={() => toggle(f.id)}
                style={{ accentColor: 'var(--accent)', width: 14, height: 14 }} />
              {f.label}
            </label>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Format:</span>
          {(['png','svg','pdf'] as const).map((fmt) => (
            <button key={fmt} onClick={() => setFormat(fmt)}
              style={{ padding: '5px 12px', borderRadius: 'var(--radius-sm)', fontSize: 11, fontWeight: 600, cursor: 'pointer',
                background: format === fmt ? 'var(--accent-dim)' : 'var(--bg-elevated)',
                border: `1px solid ${format === fmt ? 'var(--accent)' : 'var(--border)'}`,
                color: format === fmt ? 'var(--accent)' : 'var(--text-secondary)' }}>
              {fmt.toUpperCase()}
            </button>
          ))}
          <button onClick={exportFigures} disabled={selected.size === 0}
            style={{ marginLeft: 'auto', padding: '8px 20px', borderRadius: 'var(--radius-md)',
              background: selected.size > 0 ? 'var(--accent)' : 'var(--bg-active)',
              color: 'white', fontWeight: 600, fontSize: 13, border: 'none',
              cursor: selected.size > 0 ? 'pointer' : 'not-allowed' }}>
            Export {selected.size} Figure{selected.size !== 1 ? 's' : ''}
          </button>
        </div>
      </div>

      {/* Data Export */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 18 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>
          Data Export
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {[
            { label: '↓ All Results CSV', href: '/export/results' },
            { label: '↓ Statistical Report', href: '/export/statistics' },
            { label: '↓ LaTeX Table (.tex)', href: '/export/latex_table' },
          ].map(({ label, href }) => (
            <a key={label} href={href}
              style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px',
                borderRadius: 'var(--radius-md)', background: 'var(--bg-elevated)',
                border: '1px solid var(--border)', color: 'var(--text-primary)',
                fontSize: 12, fontWeight: 500, textDecoration: 'none',
                transition: 'border-color 120ms' }}>
              {label}
            </a>
          ))}
        </div>
      </div>

      {/* BibTeX */}
      <div style={{ background: 'var(--bg-panel)', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)', padding: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            BibTeX Citation
          </div>
          <button onClick={() => { navigator.clipboard.writeText(BIBTEX); toast.success('Copied BibTeX'); }}
            style={{ padding: '5px 12px', borderRadius: 'var(--radius-sm)', fontSize: 11, cursor: 'pointer',
              background: 'var(--bg-elevated)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
            Copy
          </button>
        </div>
        <pre style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-secondary)',
          background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)',
          padding: 12, overflowX: 'auto', margin: 0, lineHeight: 1.6 }}>
          {BIBTEX}
        </pre>
      </div>

      {/* Demo Recording */}
      <div style={{ background: 'var(--bg-panel)', border: `1px solid ${recording ? 'var(--red)' : 'var(--border)'}`, borderRadius: 'var(--radius-lg)', padding: 18 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>
          Demo Video Recording
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.6 }}>
          Capture a 90-second screen recording for conference demo video. Automatically stops after 90 seconds.
        </p>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          {recording && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--red)' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--red)', animation: 'pulse-dot 1s infinite' }} />
              Recording…
            </span>
          )}
          <button onClick={recording ? stopRecording : () => void startRecording()}
            style={{ padding: '9px 20px', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 13, border: 'none', cursor: 'pointer',
              background: recording ? 'var(--red)' : 'var(--bg-elevated)',
              color: recording ? 'white' : 'var(--text-secondary)' }}>
            {recording ? '⏹ Stop Recording' : '⏺ Record Demo (90s)'}
          </button>
          {recordingUrl && (
            <a href={recordingUrl} download="tdcb-sim-demo.webm"
              style={{ padding: '9px 20px', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 13,
                background: 'var(--green)', color: 'white', textDecoration: 'none' }}>
              ↓ Download Recording
            </a>
          )}
        </div>
      </div>

      {/* License */}
      <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', padding: '8px 0' }}>
        <Badge label="MIT License" variant="muted" /> &nbsp; TDCB-Sim v2.0 · IEEE Research Dashboard
      </div>
    </div>
  );
}
