"use client";
import { useId, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
export function PasswordField({
  label,
  value,
  onChange,
  autoComplete = "current-password",
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  autoComplete?: "current-password" | "new-password";
  disabled?: boolean;
}) {
  const inputId = useId();
  const [show, setShow] = useState(false);
  return (
    <div className="j1-field">
      <label className="j1-password-label" htmlFor={inputId}>{label}</label>
      <div className="j1-password">
        <input
          id={inputId}
          required
          type={show ? "text" : "password"}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoComplete={autoComplete}
          minLength={autoComplete === "new-password" ? 8 : undefined}
          disabled={disabled}
        />
        <button
          type="button"
          aria-label={`${show ? "Hide" : "Show"} ${label.toLowerCase()}`}
          aria-pressed={show}
          onClick={() => setShow(!show)}
        >
          {show ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      </div>
    </div>
  );
}
