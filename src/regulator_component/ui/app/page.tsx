"use client";
import { useState } from "react";

const API = "http://localhost:8000";

function Field({ label, value, onChange, type = "text", placeholder = "" }: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div style={{ marginBottom: 10 }}>
      <label style={{ display: "block", fontSize: 11, fontFamily: "monospace", color: "#888", marginBottom: 3, textTransform: "uppercase", letterSpacing: 1 }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          width: "100%",
          padding: "8px 10px",
          background: "#0d0d0d",
          border: "1px solid #2a2a2a",
          borderRadius: 4,
          color: "#e0e0e0",
          fontFamily: "monospace",
          fontSize: 13,
          boxSizing: "border-box",
          outline: "none",
        }}
      />
    </div>
  );
}

function Section({ title, color, children, result, onSubmit, loading }: {
  title: string;
  color: string;
  children: React.ReactNode;
  result: any;
  onSubmit: () => void;
  loading: boolean;
}) {
  return (
    <div style={{
      background: "#111",
      border: `1px solid ${color}33`,
      borderRadius: 8,
      padding: 20,
      marginBottom: 20,
    }}>
      <div style={{
        fontSize: 11,
        fontFamily: "monospace",
        color,
        textTransform: "uppercase",
        letterSpacing: 2,
        marginBottom: 16,
        borderBottom: `1px solid ${color}22`,
        paddingBottom: 10,
      }}>
        ◈ {title}
      </div>
      {children}
      <button
        onClick={onSubmit}
        disabled={loading}
        style={{
          marginTop: 10,
          padding: "9px 20px",
          background: loading ? "#1a1a1a" : color + "22",
          border: `1px solid ${color}`,
          borderRadius: 4,
          color: loading ? "#555" : color,
          fontFamily: "monospace",
          fontSize: 12,
          cursor: loading ? "not-allowed" : "pointer",
          letterSpacing: 1,
          textTransform: "uppercase",
          transition: "background 0.2s",
        }}
      >
        {loading ? "processing..." : "submit"}
      </button>
      {result && (
        <pre style={{
          marginTop: 14,
          padding: 12,
          background: "#0a0a0a",
          border: "1px solid #1e1e1e",
          borderRadius: 4,
          fontSize: 11,
          fontFamily: "monospace",
          color: result?.result?.status === "CERTIFIED" || result?.result?.status === "APPROVED" || result?.result?.approved
            ? "#4ade80"
            : result?.result?.status === "REJECTED"
            ? "#f87171"
            : "#aaa",
          overflow: "auto",
          maxHeight: 260,
          whiteSpace: "pre-wrap",
          wordBreak: "break-all",
        }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default function Home() {
  // Firmware
  const [fw, setFw] = useState({
    request_id: "fw-1",
    developer_id: "",
    drone_type: "",
    commit_hash: "",
    repository_url: "",
    version: "",
  });
  const [fwResult, setFwResult] = useState<any>(null);
  const [fwLoading, setFwLoading] = useState(false);

  // Drone
  const [dr, setDr] = useState({
    request_id: "dr-1",
    serial_number: "",
    model: "",
    manufacturer: "",
    firmware_version: "",
    firmware_certificate_id: "",
  });
  const [drResult, setDrResult] = useState<any>(null);
  const [drLoading, setDrLoading] = useState(false);

  // Insurer
  const [ins, setIns] = useState({
    message_id: "ins-1",
    insurer_id: "",
    order_id: "",
    amount: "",
    incident_id: "",
  });
  const [insResult, setInsResult] = useState<any>(null);
  const [insLoading, setInsLoading] = useState(false);

  const sendFirmware = async () => {
    setFwLoading(true);
    try {
      const res = await fetch(`${API}/firmware`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request_id: fw.request_id,
          developer_id: fw.developer_id,
          drone_type: fw.drone_type,
          firmware: {
            commit_hash: fw.commit_hash,
            repository_url: fw.repository_url,
            version: fw.version,
          },
        }),
      });
      const data = await res.json();
      setFwResult(data);
      // автоматически подставляем certificate_id в форму дрона
      const certId = data?.result?.certificate?.certificate_id;
      if (certId) {
        setDr(d => ({ ...d, firmware_certificate_id: certId }));
      }
    } finally {
      setFwLoading(false);
    }
  };

  const sendDrone = async () => {
    setDrLoading(true);
    try {
      const res = await fetch(`${API}/drone`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          request_id: dr.request_id,
          drone: {
            serial_number: dr.serial_number,
            model: dr.model,
            manufacturer: dr.manufacturer,
          },
          firmware: {
            version: dr.firmware_version,
            certificate_id: dr.firmware_certificate_id,
          },
        }),
      });
      const data = await res.json();
      setDrResult(data);
    } finally {
      setDrLoading(false);
    }
  };

  const sendInsurer = async () => {
    setInsLoading(true);
    try {
      const res = await fetch(`${API}/insurer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message_id: ins.message_id,
          insurer_id: ins.insurer_id,
          order_id: ins.order_id,
          amount: parseFloat(ins.amount) || 0,
          incident_id: ins.incident_id,
        }),
      });
      const data = await res.json();
      setInsResult(data);
    } finally {
      setInsLoading(false);
    }
  };

  return (
    <main style={{
      minHeight: "100vh",
      background: "#0a0a0a",
      color: "#e0e0e0",
      fontFamily: "monospace",
      padding: "30px 20px",
      maxWidth: 680,
      margin: "0 auto",
    }}>
      <div style={{ marginBottom: 30 }}>
        <div style={{ fontSize: 10, color: "#444", letterSpacing: 3, textTransform: "uppercase", marginBottom: 6 }}>
          UAV REGULATORY SYSTEM
        </div>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600, color: "#fff", letterSpacing: 1 }}>
          Regulator Control Panel
        </h1>
      </div>

      {/* FIRMWARE */}
      <Section title="Firmware Certification" color="#60a5fa" result={fwResult} onSubmit={sendFirmware} loading={fwLoading}>
        <Field label="Request ID" value={fw.request_id} onChange={v => setFw(f => ({ ...f, request_id: v }))} />
        <Field label="Developer ID" value={fw.developer_id} onChange={v => setFw(f => ({ ...f, developer_id: v }))} placeholder="dev_001" />
        <Field label="Drone Type" value={fw.drone_type} onChange={v => setFw(f => ({ ...f, drone_type: v }))} placeholder="quad / fixed-wing" />
        <Field label="Firmware Version" value={fw.version} onChange={v => setFw(f => ({ ...f, version: v }))} placeholder="1.0.0" />
        <Field label="Commit Hash" value={fw.commit_hash} onChange={v => setFw(f => ({ ...f, commit_hash: v }))} placeholder="abc123" />
        <Field label="Repository URL" value={fw.repository_url} onChange={v => setFw(f => ({ ...f, repository_url: v }))} placeholder="https://github.com/..." />
      </Section>

      {/* DRONE */}
      <Section title="Drone Registration" color="#a78bfa" result={drResult} onSubmit={sendDrone} loading={drLoading}>
        <Field label="Request ID" value={dr.request_id} onChange={v => setDr(d => ({ ...d, request_id: v }))} />
        <Field label="Serial Number" value={dr.serial_number} onChange={v => setDr(d => ({ ...d, serial_number: v }))} placeholder="SN-00001" />
        <Field label="Model" value={dr.model} onChange={v => setDr(d => ({ ...d, model: v }))} placeholder="DJI Mavic 3" />
        <Field label="Manufacturer" value={dr.manufacturer} onChange={v => setDr(d => ({ ...d, manufacturer: v }))} placeholder="DJI" />
        <Field label="Firmware Version" value={dr.firmware_version} onChange={v => setDr(d => ({ ...d, firmware_version: v }))} placeholder="1.0.0" />
        <Field
          label="Firmware Certificate ID (auto-filled after Firmware step)"
          value={dr.firmware_certificate_id}
          onChange={v => setDr(d => ({ ...d, firmware_certificate_id: v }))}
          placeholder="CERT-..."
        />
      </Section>

      {/* INSURER */}
      <Section title="Insurance Check" color="#34d399" result={insResult} onSubmit={sendInsurer} loading={insLoading}>
        <Field label="Message ID" value={ins.message_id} onChange={v => setIns(i => ({ ...i, message_id: v }))} />
        <Field label="Insurer ID" value={ins.insurer_id} onChange={v => setIns(i => ({ ...i, insurer_id: v }))} placeholder="ins_company_001" />
        <Field label="Order ID" value={ins.order_id} onChange={v => setIns(i => ({ ...i, order_id: v }))} placeholder="order-001" />
        <Field label="Amount" value={ins.amount} onChange={v => setIns(i => ({ ...i, amount: v }))} type="number" placeholder="1000" />
        <Field label="Incident ID" value={ins.incident_id} onChange={v => setIns(i => ({ ...i, incident_id: v }))} placeholder="incident-001" />
      </Section>
    </main>
  );
}