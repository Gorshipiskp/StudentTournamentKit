<script lang="ts">
  import { onMount } from 'svelte';
  import {
    cancelReview,
    getMatch,
    requestReview,
    resolveReview,
    reviewStatusLabel,
    type JudgeSession,
    type MatchPublic,
  } from './api';
  import { connectJudgeWs } from './judgeWs';

  let { session }: { session: JudgeSession } = $props();

  let match = $state<MatchPublic | null>(null);
  let busy = $state(false);
  let err = $state<string | null>(null);
  let flash = $state<string | null>(null);
  let forfeitPick = $state(false);

  const canResolve = $derived(session.caps.includes('judge.resolve'));

  async function refresh() {
    try {
      match = await getMatch(session.matchId);
      err = null;
    } catch (e) {
      err = e instanceof Error ? e.message : 'Ошибка статуса';
    }
  }

  onMount(() => {
    void refresh();
    // Fallback poll if WS drops; primary updates via /ws/judge
    const id = window.setInterval(() => void refresh(), 8000);
    const ws = connectJudgeWs(session.matchId, session.accessToken, {
      onStatus: (m) => {
        match = m;
        err = null;
      },
    });
    return () => {
      window.clearInterval(id);
      ws.close();
    };
  });

  async function run(action: () => Promise<unknown>, okMsg: string) {
    if (busy) return;
    busy = true;
    err = null;
    flash = null;
    try {
      await action();
      await refresh();
      flash = okMsg;
      forfeitPick = false;
    } catch (e) {
      err = e instanceof Error ? e.message : 'Ошибка действия';
      await refresh();
    } finally {
      busy = false;
    }
  }

  function onRequest() {
    return run(
      () => requestReview(session.matchId, session.accessToken),
      'Проверка запрошена',
    );
  }

  function onCancel() {
    return run(
      () => cancelReview(session.matchId, session.accessToken),
      'Проверка отменена',
    );
  }

  function onContinue() {
    if (!match) return;
    return run(
      () =>
        resolveReview(session.matchId, session.accessToken, {
          action: 'continue',
          version: match!.version,
        }),
      'Матч продолжается',
    );
  }

  function onForfeit(losing: 'team_a' | 'team_b') {
    if (!match) return;
    return run(
      () =>
        resolveReview(session.matchId, session.accessToken, {
          action: 'forfeit',
          version: match!.version,
          losing_team: losing,
        }),
      losing === 'team_a'
        ? 'Тех. поражение команде A'
        : 'Тех. поражение команде B',
    );
  }
</script>

<main class="page">
  <header class="top">
    <p class="eyebrow">Судья</p>
    <h1>Матч</h1>
    <p class="id">{session.matchId}</p>
  </header>

  {#if match}
    <section class="card status" aria-live="polite">
      <p class="banner" class:paused={match.review_status === 'paused'}>
        {reviewStatusLabel(match.review_status)}
      </p>
      <div class="score">
        <span>A {match.score.team_a}</span>
        <span class="sep">:</span>
        <span>{match.score.team_b} B</span>
      </div>
      <dl class="meta">
        <div>
          <dt>Статус</dt>
          <dd>{match.status}</dd>
        </div>
        <div>
          <dt>Раунд</dt>
          <dd>{match.round}</dd>
        </div>
        <div>
          <dt>Карта</dt>
          <dd>{match.map ?? '—'}</dd>
        </div>
        <div>
          <dt>Пауза</dt>
          <dd>{match.actual_paused ? 'да' : 'нет'}</dd>
        </div>
      </dl>
    </section>

    <section class="actions">
      {#if match.review_status === 'none' || match.review_status === 'cancelled' || match.review_status === 'resolved'}
        <button
          class="btn primary"
          disabled={busy || match.status === 'completed' || match.status === 'forfeited'}
          onclick={() => void onRequest()}
        >
          Запрос проверки
        </button>
      {:else if match.review_status === 'requested'}
        <p class="hint">Пауза включится в начале следующего раунда (закупка).</p>
        <button class="btn warn" disabled={busy} onclick={() => void onCancel()}>
          Отменить
        </button>
      {:else if match.review_status === 'pause_pending'}
        <p class="hint">Ждём подтверждение паузы на сервере…</p>
      {:else if match.review_status === 'paused'}
        {#if canResolve && !forfeitPick}
          <button class="btn primary" disabled={busy} onclick={() => void onContinue()}>
            Продолжить
          </button>
          <button
            class="btn danger"
            disabled={busy}
            onclick={() => (forfeitPick = true)}
          >
            Тех. поражение
          </button>
        {:else if canResolve && forfeitPick}
          <p class="hint">Кому техническое поражение?</p>
          <button
            class="btn danger"
            disabled={busy}
            onclick={() => void onForfeit('team_a')}
          >
            Поражение команде A
          </button>
          <button
            class="btn danger"
            disabled={busy}
            onclick={() => void onForfeit('team_b')}
          >
            Поражение команде B
          </button>
          <button class="btn ghost" disabled={busy} onclick={() => (forfeitPick = false)}>
            Назад
          </button>
        {:else}
          <p class="hint">Нет права завершать проверку.</p>
        {/if}
      {/if}
    </section>
  {:else}
    <p class="loading">Загрузка статуса…</p>
  {/if}

  {#if flash}
    <p class="flash ok">{flash}</p>
  {/if}
  {#if err}
    <p class="flash bad" role="alert">{err}</p>
  {/if}
</main>

<style>
  .page {
    max-width: 28rem;
    margin: 0 auto;
    padding: 1.25rem 1rem 2.5rem;
    padding-bottom: max(2.5rem, env(safe-area-inset-bottom));
  }
  .top {
    margin-bottom: 1.25rem;
  }
  .eyebrow {
    margin: 0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.75rem;
    color: var(--muted);
  }
  h1 {
    margin: 0.2rem 0 0;
    font-size: 1.75rem;
  }
  .id {
    margin: 0.35rem 0 0;
    color: var(--muted);
    font-size: 0.9rem;
    word-break: break-all;
  }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.1rem;
  }
  .banner {
    margin: 0 0 0.85rem;
    font-size: 1.05rem;
    font-weight: 600;
    line-height: 1.35;
  }
  .banner.paused {
    color: var(--warn);
  }
  .score {
    display: flex;
    justify-content: center;
    gap: 0.65rem;
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.85rem;
  }
  .sep {
    color: var(--muted);
  }
  .meta {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.55rem 1rem;
    margin: 0;
  }
  .meta dt {
    margin: 0;
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
  }
  .meta dd {
    margin: 0.15rem 0 0;
    font-size: 0.95rem;
  }
  .actions {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    margin-top: 1.25rem;
  }
  .hint {
    margin: 0;
    color: var(--muted);
    font-size: 0.95rem;
    line-height: 1.4;
  }
  .btn {
    min-height: var(--tap);
    border: none;
    border-radius: 12px;
    padding: 0.85rem 1rem;
    font-size: 1.1rem;
    font-weight: 600;
  }
  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .btn.primary {
    background: var(--accent);
    color: #fff;
  }
  .btn.primary:not(:disabled):active {
    background: var(--accent-press);
  }
  .btn.warn {
    background: var(--warn);
    color: #1a1400;
  }
  .btn.danger {
    background: var(--danger);
    color: #fff;
  }
  .btn.danger:not(:disabled):active {
    background: var(--danger-press);
  }
  .btn.ghost {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
  }
  .loading {
    color: var(--muted);
  }
  .flash {
    margin-top: 1rem;
    padding: 0.75rem 0.9rem;
    border-radius: 8px;
    font-size: 0.95rem;
  }
  .flash.ok {
    background: color-mix(in srgb, var(--ok) 22%, transparent);
    color: var(--ok);
  }
  .flash.bad {
    background: color-mix(in srgb, var(--danger) 22%, transparent);
    color: #ffb4b4;
  }
</style>
