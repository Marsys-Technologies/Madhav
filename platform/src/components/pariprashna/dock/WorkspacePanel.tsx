"use client";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { History, PanelRight, Pin, PinOff, X } from "lucide-react";
import { useDockController } from "./DockController";

/** Expands without persisting transient movement; only the explicit pin is remembered. */
export function WorkspacePanel({
  side,
  title,
  children,
}: {
  side: "left" | "right";
  title: string;
  children: ReactNode;
}) {
  const c = useDockController(),
    ref = useRef<HTMLElement>(null),
    trigger = useRef<HTMLButtonElement>(null);
  const skipFocus = useRef(false);
  const suppressHover = useRef(false);
  const [mobile, setMobile] = useState(false);
  const open = side === "right" ? c.open : c.leftOpen,
    pinned = side === "right" ? c.pinned : c.leftPinned;
  const setOpen = side === "right" ? c.setOpen : c.setLeftOpen,
    setPinned = side === "right" ? c.setPinned : c.setLeftPinned;
  useEffect(() => {
    const q = window.matchMedia?.("(max-width: 900px)");
    if (!q) return;
    const update = () => setMobile(q.matches);
    update();
    q.addEventListener?.("change", update);
    return () => q.removeEventListener?.("change", update);
  }, []);
  useEffect(() => {
    if (!open || !mobile) return;
    const previous = document.activeElement as HTMLElement | null;
    ref.current
      ?.querySelector<HTMLElement>("button,input,select,a[href]")
      ?.focus();
    function trap(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setOpen(false);
        return;
      }
      if (e.key !== "Tab") return;
      const targets = Array.from(
        ref.current?.querySelectorAll<HTMLElement>(
          "button:not(:disabled),input,select,a[href]",
        ) ?? [],
      );
      const first = targets[0],
        last = targets.at(-1);
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last?.focus();
      }
      if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first?.focus();
      }
    }
    document.addEventListener("keydown", trap);
    return () => {
      document.removeEventListener("keydown", trap);
      previous?.focus();
    };
  }, [open, mobile, setOpen]);
  const closePanel = () => {
    suppressHover.current = true;
    skipFocus.current = true;
    setOpen(false);
    trigger.current?.focus();
  };
  const Icon = side === "left" ? History : PanelRight;
  return (
    <div
      className={`pp-panel-slot pp-panel-${side}`}
      data-pinned={pinned}
      data-open={open}
      onMouseLeave={() => {
        suppressHover.current = false;
        if (
          !pinned &&
          !mobile &&
          !ref.current?.contains(document.activeElement)
        )
          setOpen(false);
      }}
    >
      <button
        ref={trigger}
        type="button"
        className="pp-rail-trigger"
        aria-label={`Open ${title.toLowerCase()}`}
        aria-expanded={open}
        aria-controls={`pp-${side}-panel`}
        onClick={() => {
          suppressHover.current = false;
          setOpen(!open);
        }}
        onMouseEnter={() => {
          if (!mobile && !suppressHover.current) setOpen(true);
        }}
        onFocus={() => {
          if (skipFocus.current) {
            skipFocus.current = false;
            return;
          }
          if (!mobile && !suppressHover.current) setOpen(true);
        }}
      >
        <Icon size={19} />
      </button>
      {open && mobile && (
        <button
          className="pp-panel-veil"
          aria-label={`Close ${title.toLowerCase()}`}
          onClick={() => setOpen(false)}
        />
      )}
      <aside
        ref={ref}
        id={`pp-${side}-panel`}
        className="pp-workspace-panel"
        hidden={!open}
        role={mobile && open ? "dialog" : undefined}
        aria-modal={mobile && open ? true : undefined}
        aria-label={title}
        onMouseEnter={() => {
          if (!mobile && !suppressHover.current) setOpen(true);
        }}
        onMouseLeave={() => {
          if (
            !pinned &&
            !mobile &&
            !ref.current?.contains(document.activeElement)
          )
            setOpen(false);
        }}
        onBlur={(e) => {
          if (
            !pinned &&
            !mobile &&
            !e.currentTarget.contains(e.relatedTarget as Node)
          )
            setOpen(false);
        }}
        onKeyDown={(e) => {
          if (e.key === "Escape") {
            e.stopPropagation();
            closePanel();
          }
        }}
      >
        <div className="pp-panel-heading">
          <span>{title}</span>
          <div>
            <button
              type="button"
              aria-label={
                pinned
                  ? `Release ${title.toLowerCase()} pin`
                  : `Pin ${title.toLowerCase()} open`
              }
              aria-pressed={pinned}
              onClick={() => setPinned(!pinned)}
            >
              {pinned ? <PinOff size={17} /> : <Pin size={17} />}
            </button>
            <button
              type="button"
              aria-label={`Close ${title.toLowerCase()}`}
              onClick={closePanel}
            >
              <X size={18} />
            </button>
          </div>
        </div>
        {children}
      </aside>
    </div>
  );
}
