/** Lightweight toast bus for admin pages. */
export type ToastKind = 'ok' | 'err' | 'info';

export type ToastItem = {
  id: number;
  kind: ToastKind;
  text: string;
};

type Listener = (items: ToastItem[]) => void;

let seq = 0;
let items: ToastItem[] = [];
const listeners = new Set<Listener>();

function emit() {
  for (const l of listeners) l(items);
}

export function subscribeToasts(listener: Listener): () => void {
  listeners.add(listener);
  listener(items);
  return () => listeners.delete(listener);
}

export function pushToast(kind: ToastKind, text: string, ms = 4200) {
  const id = ++seq;
  items = [...items, { id, kind, text }];
  emit();
  window.setTimeout(() => {
    items = items.filter((t) => t.id !== id);
    emit();
  }, ms);
}

export function toastOk(text: string) {
  pushToast('ok', text);
}

export function toastErr(text: string) {
  pushToast('err', text, 6000);
}

export function humanApiError(raw: string): string {
  if (raw.startsWith('401')) return 'Неверный логин или пароль, либо сессия истекла.';
  if (raw.startsWith('404')) return 'Не найдено. Обновите страницу.';
  if (raw.startsWith('403')) return 'Недостаточно прав для этого действия.';
  if (raw.startsWith('409')) return 'Конфликт данных — обновите страницу и попробуйте снова.';
  const brace = raw.indexOf('{');
  if (brace >= 0) {
    try {
      const j = JSON.parse(raw.slice(brace));
      if (typeof j.detail === 'string') return j.detail;
      if (Array.isArray(j.detail)) {
        return j.detail.map((d: { msg?: string }) => d.msg || String(d)).join('; ');
      }
    } catch {
      /* ignore */
    }
  }
  return raw.length > 180 ? raw.slice(0, 180) + '…' : raw;
}
