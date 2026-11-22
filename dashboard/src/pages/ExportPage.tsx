import { useEffect, useRef, useState } from "react";
import {
  DownloadSimple,
  FileCsv,
  FileCode,
  VideoCamera,
  Stop,
  Printer,
  Copy,
  Check,
} from "@phosphor-icons/react";
import { useResults } from "../hooks/useResults";
import { useSimulationStore } from "../store/simulationStore";
function download(name: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function ExportPage() {
  const { data: runs = [] } = useResults();
  const [runId, setRunId] = useState("");
  const config = useSimulationStore((s) => s.config);
  const [recording, setRecording] = useState(false),
    [recordingUrl, setRecordingUrl] = useState<string | null>(null),
    [error, setError] = useState(""),
    [copied, setCopied] = useState(false);
  const recorder = useRef<MediaRecorder | null>(null),
    stream = useRef<MediaStream | null>(null),
    timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const stop = () => {
    clearTimeout(timer.current);
    if (recorder.current?.state === "recording") recorder.current.stop();
    setRecording(false);
  };
  useEffect(
    () => () => {
      clearTimeout(timer.current);
      if (recorder.current?.state === "recording") recorder.current.stop();
      stream.current?.getTracks().forEach((t) => t.stop());
    },
    [],
  );
  useEffect(
    () => () => {
      if (recordingUrl) URL.revokeObjectURL(recordingUrl);
    },
    [recordingUrl],
  );
  const record = async () => {
    setError("");
    try {
      stream.current = await navigator.mediaDevices.getDisplayMedia({
        video: true,
      });
      const mr = new MediaRecorder(stream.current);
      recorder.current = mr;
      const chunks: Blob[] = [];
      mr.ondataavailable = (e) => {
        if (e.data.size) chunks.push(e.data);
      };
      mr.onstop = () => {
        setRecordingUrl(
          URL.createObjectURL(new Blob(chunks, { type: mr.mimeType })),
        );
        stream.current?.getTracks().forEach((t) => t.stop());
        setRecording(false);
        clearTimeout(timer.current);
      };
      stream.current.getVideoTracks()[0].onended = stop;
      mr.start();
      setRecording(true);
      timer.current = setTimeout(stop, 90000);
    } catch {
      setError(
        "Screen recording did not start. Allow screen sharing in your browser and try again.",
      );
    }
  };
  const command = "python generate_paper_figures.py";
  return (
    <div className="export-grid">
      <section className="export-card">
        <span className="export-icon">
          <FileCsv size={25} />
        </span>
        <h2>Experiment data</h2>
        <p>
          Download source metrics for an individual experiment, or collect all
          saved results in one archive.
        </p>
        <label className="field-label" htmlFor="export-run">
          Recorded experiment
        </label>
        <select
          id="export-run"
          value={runId}
          onChange={(e) => setRunId(e.target.value)}
        >
          <option value="">Choose an experiment</option>
          {runs.map((r) => (
            <option key={r.run_id} value={r.run_id}>
              {r.run_id}
            </option>
          ))}
        </select>
        <div className="export-actions">
          {runId ? (
            <a className="quiet-button" href={`/results/${runId}/download`}>
              <DownloadSimple size={16} />
              Download CSV
            </a>
          ) : (
            <button className="quiet-button" disabled>
              Select a run to download
            </button>
          )}
          <a className="quiet-button" href="/export/results">
            All results ZIP
          </a>
        </div>
        <div className="export-footnote">
          {runs.length} saved experiments available
        </div>
      </section>
      <section className="export-card">
        <span className="export-icon">
          <FileCode size={25} />
        </span>
        <h2>Reproducibility</h2>
        <p>
          Save the current workspace configuration with its agent, attack, seed,
          and training parameters.
        </p>
        <pre className="configuration-preview">
          {JSON.stringify(
            {
              agent: config.agent,
              attack: config.attack,
              nodes: config.nodes,
              episodes: config.episodes,
              seed: config.seed,
            },
            null,
            2,
          )}
        </pre>
        <button
          className="quiet-button"
          onClick={() =>
            download(
              "tdcb-experiment-config.json",
              JSON.stringify(config, null, 2),
              "application/json",
            )
          }
        >
          <DownloadSimple size={16} />
          Save configuration JSON
        </button>
      </section>
      <section className="export-card">
        <span className="export-icon">
          <VideoCamera size={25} />
        </span>
        <h2>Presentation recording</h2>
        <p>
          Capture a browser tab, window, or screen. Recording stops
          automatically after 90 seconds.
        </p>
        <div className="recording-preview">
          <VideoCamera size={32} weight="light" />
          <span>
            {recording
              ? "Recording in progress"
              : "Ready to capture your demonstration"}
          </span>
        </div>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="export-actions">
          <button
            className={`quiet-button ${recording ? "recording-active" : ""}`}
            onClick={() => (recording ? stop() : void record())}
          >
            {recording ? <Stop size={16} /> : <VideoCamera size={16} />}{" "}
            {recording ? "Stop recording" : "Start recording"}
          </button>
          {recordingUrl && (
            <a
              className="quiet-button"
              href={recordingUrl}
              download="tdcb-presentation.webm"
            >
              <DownloadSimple size={16} />
              Download video
            </a>
          )}
        </div>
      </section>
      <section className="export-card">
        <span className="export-icon">
          <Printer size={25} />
        </span>
        <h2>Paper figures</h2>
        <p>
          Generate figures from saved experiment results using the repository's
          plotting workflow.
        </p>
        <div className="command-block">
          <code>{command}</code>
          <button
            className="text-button"
            aria-label="Copy figure generation command"
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(command);
                setCopied(true);
              } catch {
                setError(
                  "Could not copy command. Select and copy the text directly.",
                );
              }
            }}
          >
            {copied ? <Check size={17} /> : <Copy size={17} />}
          </button>
        </div>
        <p className="data-note">
          Run this command from the repository root. Check each figure against
          the underlying CSV before including it in your paper.
        </p>
        <button className="quiet-button" onClick={() => window.print()}>
          <Printer size={16} />
          Print this view
        </button>
      </section>
    </div>
  );
}
