"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { Bookmark, Search, Plus } from "lucide-react";
import { formatRelativeTime } from "./relativeTime";
import type { ThreadSummary } from "./types";
export interface ConsultationThread extends ThreadSummary {
  tagged?: boolean;
  taggedAnswers?: Array<{ id: string; text: string | null }>;
}
export function ConsultationHistory({
  threads,
  onSelect,
  onNew,
  disabled,
  loading,
  error,
  onRetry,
}: {
  threads: ConsultationThread[];
  onSelect: (id: string, answerId?: string) => void;
  onNew: () => void;
  disabled: boolean;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 60_000);
    return () => clearInterval(timer);
  }, []);
  const [filter, setFilter] = useState("all"),
    [search, setSearch] = useState("");
  const visible = threads.filter(
    (t) =>
      (filter !== "conversations" || t.tagged) &&
      (filter !== "answers" || !!t.taggedAnswers?.length) &&
      `${t.title} ${(t.taggedAnswers ?? []).map((a) => a.text).join(" ")}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  return (
    <div className="pp-history-list">
      <button
        type="button"
        className="pp-new-conversation"
        disabled={disabled}
        onClick={onNew}
      >
        <Plus size={17} />
        New conversation
      </button>
      <label className="pp-history-search">
        <Search size={16} />
        <input
          aria-label="Search history"
          placeholder="Search conversations…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </label>
      <label className="pp-history-filter">
        Show
        <select
          aria-label="Filter history"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="all">All conversations</option>
          <option value="conversations">Tagged conversations</option>
          <option value="answers">Tagged answers</option>
        </select>
      </label>
      {loading && (
        <p role="status" className="pp-panel-empty">
          Loading history…
        </p>
      )}
      {error && (
        <div role="status" className="pp-panel-empty">
          {error}
          <button type="button" onClick={onRetry}>
            Try again
          </button>
        </div>
      )}
      {!loading && !error && visible.length === 0 && (
        <p className="pp-panel-empty">
          {filter === "all"
            ? "Your conversations will appear here."
            : "No matching tags yet."}
        </p>
      )}
      <ul aria-label="Conversations">
        {visible.map((t) => (
          <li key={t.id} data-active={t.active}>
            {t.href ? (
              <Link href={t.href}>
                <span>{t.title}</span>
                <small>Historical · read-only</small>
              </Link>
            ) : (
              <button
                type="button"
                disabled={disabled}
                aria-current={t.active ? "true" : undefined}
                onClick={() => onSelect(t.id)}
              >
                <span>
                  {t.tagged && (
                    <Bookmark size={14} aria-label="Tagged conversation" />
                  )}
                  {t.title}
                </span>
                <small>
                  {t.streaming
                    ? "In progress"
                    : formatRelativeTime(t.updatedAtMs, now)}
                </small>
              </button>
            )}
            {filter === "answers" &&
              (t.taggedAnswers ?? []).map((answer) =>
                t.href ? (
                  <Link key={answer.id} href={`${t.href}#${answer.id}`}>
                    {answer.text || "Tagged answer"}
                  </Link>
                ) : (
                  <button
                    key={answer.id}
                    type="button"
                    className="pp-history-answer"
                    disabled={disabled}
                    onClick={() => onSelect(t.id, answer.id)}
                  >
                    <Bookmark size={13} />
                    {answer.text || "Tagged answer"}
                  </button>
                ),
              )}
          </li>
        ))}
      </ul>
    </div>
  );
}
