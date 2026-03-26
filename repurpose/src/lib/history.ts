import { HistoryEntry } from "@/types";

const STORAGE_KEY = "repurpose-history";
const MAX_ENTRIES = 50;

export function getHistory(): HistoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function addToHistory(entry: HistoryEntry): void {
  const history = getHistory();
  history.unshift(entry);
  if (history.length > MAX_ENTRIES) history.pop();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

export function clearHistory(): void {
  localStorage.removeItem(STORAGE_KEY);
}
