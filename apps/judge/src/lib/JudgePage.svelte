<script lang="ts">
  import { onMount } from 'svelte';
  import {
    cancelReview,
    getMatch,
    humanApiError,
    matchStatusLabel,
    requestReview,
    resolveReview,
    reviewActionHint,
    reviewStatusLabel,
    type JudgeSession,
    type MatchPublic,
  } from './api';
  import ConfirmDialog from './ConfirmDialog.svelte';
  import { connectJudgeWs } from './judgeWs';

  let { session }: { session: JudgeSession } = $props();

  let match = $state<MatchPublic | null>(null);
  let busy = $state(false);
  let err = $state<string | null>(null);
  let flash = $state<string | null>(null);
  let forfeitPick = $state(false);
  let live = $state(false);
  let confirmOpen = $state(false);
  let pendingForfeit = $state<'team_a' | 'team_b' | null>(null);

  const canResolve = $derived(session.caps.includes('judge.resolve'));
  const matchEnded = $derived(
    match?.status === 'completed' || match?.status === 'forfeited',
  );
  const phase = $derived(match?.review_status ?? 'none');
  const hint = $derived(
    match ? reviewActionHint(match.review_status, match.status) : '',
  );

  async function refresh() {
    try {
      match = await getMatch(session.matchId);
      err = null;
    } catch (e) {
      err = humanApiError(e instanceof Error ? e.message : 'Ошибка статуса');
    }
  }

  onMount(() => {
    void refresh();
    const id = window.setInterval(() => void refresh(), 8000);
    const ws = connectJudgeWs(session.matchId, session.accessToken, {
      onStatus: (m) => {
        match = m;
        err = null;
        live = true;
      },
      onError: () => {
        live = false;
      },
    });
    return () => {
      window.clearInterval(id);
      ws.close();
    };
  });

  function buzz() {
    try {
      navigator.vibrate?.(12);
    } catch {
      /* ignore */
    }
  }

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
      pendingForfeit = null;
      confirmOpen = false;
      buzz();
      window.setTimeout(() => {
        if (flash === okMsg) flash = null;
      }, 3500);
    } catch (e) {
      err = humanApiError(e instanceof Error ? e.message : 'Ошибка действия');
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

  function askForfeit(losing: 'team_a' | 'team_b') {
    pendingForfeit = losing;
    confirmOpen = true;
  }

  function onForfeitConfirm() {
    if (!match || !pendingForfeit) return;
    const losing = pendingForfeit;
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

  function shortId(id: string): string {
    return id.length > 14 ? id.slice(0, 10) + '…' : id;
  }
</script>

<div class="page">
  <header class="top">
    <div class="brand-row">
      <span class="mark">STK</span>
      <div>
        <p class="eyebrow muted">Панель судьи</p>
        <h1 class="display">Матч</h1>
      </div>
      <span class="live" class:on={live} title={live ? 'Связь живая' : 'Опрос по таймеру'}>
        {live ? 'онлайн' : 'офлайн'}
      </span>
    </div>
    <p class="id muted">№ {shortId(session.matchId)}</p>
  </header>

  {#if match}
    <section class="surface scoreboard" aria-live="polite">
      <p class="phase" class:urgent={phase === 'paused'} class:wait={phase === 'requested' || phase === 'pause_pending'}>
        {reviewStatusLabel(match.review_status)}
      </p>

      <div class="score" role="group" aria-label="Счёт">
        <div class="side">
          <span class="team">Команда A</span>
          <span class="num">{match.score.team_a}</span>
        </div>
        <span class="colon muted">:</span>
        <div class="side">
          <span class="team">Команда B</span>
          <span class="num">{match.score.team_b}</span>
        </div>
      </div>

      <dl class="meta">
        <div>
          <dt>Матч</dt>
          <dd>{matchStatusLabel(match.status)}</dd>
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
          <dt>Пауза на сервере</dt>
          <dd>{match.actual_paused ? 'да' : 'нет'}</dd>
        </div>
      </dl>

      {#if match.judge_banner}
        <p class="banner-note">{match.judge_banner}</p>
      {/if}
    </section>

    {#if hint}
      <p class="hint-card surface">{hint}</p>
    {/if}

    <div class="spacer" aria-hidden="true"></div>

    <section class="dock" aria-label="Действия судьи">
      {#if matchEnded}
        <p class="dock-hint muted">Матч завершён. Можно закрыть вкладку.</p>
      {:else if phase === 'none' || phase === 'cancelled' || phase === 'resolved'}
        <button class="btn btn-primary" disabled={busy} onclick={() => void onRequest()}>
          {busy ? 'Отправляем…' : 'Запросить проверку'}
        </button>
      {:else if phase === 'requested'}
        <p class="dock-hint muted">Ждём паузу на закупке следующего раунда.</p>
        <button class="btn btn-warn" disabled={busy} onclick={() => void onCancel()}>
          {busy ? 'Отменяем…' : 'Отменить проверку'}
        </button>
      {:else if phase === 'pause_pending'}
        <p class="dock-hint muted">Ждём подтверждение паузы…</p>
        <div class="pulse" aria-hidden="true"></div>
      {:else if phase === 'paused'}
        {#if canResolve && !forfeitPick}
          <button class="btn btn-primary" disabled={busy} onclick={() => void onContinue()}>
            {busy ? 'Сохраняем…' : 'Продолжить матч'}
          </button>
          <button class="btn btn-danger" disabled={busy} onclick={() => (forfeitPick = true)}>
            Техническое поражение…
          </button>
        {:else if canResolve && forfeitPick}
          <p class="dock-hint">Кому техническое поражение?</p>
          <button class="btn btn-danger" disabled={busy} onclick={() => askForfeit('team_a')}>
            Поражение команде A ({match.score.team_a})
          </button>
          <button class="btn btn-danger" disabled={busy} onclick={() => askForfeit('team_b')}>
            Поражение команде B ({match.score.team_b})
          </button>
          <button class="btn btn-ghost" disabled={busy} onclick={() => (forfeitPick = false)}>
            Назад
          </button>
        {:else}
          <p class="dock-hint muted">У этой ссылки нет права завершать проверку.</p>
        {/if}
      {/if}
    </section>
  {:else}
    <p class="loading muted">Загружаем статус матча…</p>
  {/if}

  {#if flash}
    <p class="toast ok" role="status">{flash}</p>
  {/if}
  {#if err}
    <p class="toast bad" role="alert">{err}</p>
  {/if}
</div>

<ConfirmDialog
  open={confirmOpen}
  title="Выдать тех. поражение?"
  body={pendingForfeit === 'team_a'
    ? 'Команда A проиграет матч. Это нельзя отменить из панели судьи.'
    : 'Команда B проиграет матч. Это нельзя отменить из панели судьи.'}
  confirmLabel="Да, тех. поражение"
  cancelLabel="Отмена"
  oncancel={() => {
    confirmOpen = false;
    pendingForfeit = null;
  }}
  onconfirm={() => void onForfeitConfirm()}
/>

<style>
  .page {
    max-width: 28rem;
    margin: 0 auto;
    min-height: 100dvh;
    padding: 1.1rem 1rem calc(7.5rem + env(safe-area-inset-bottom));
    display: flex;
    flex-direction: column;
  }
  .top {
    margin-bottom: 1rem;
  }
  .brand-row {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
  }
  .mark {
    display: inline-grid;
    place-items: center;
    width: 2.5rem;
    height: 2.5rem;
    border-radius: var(--radius);
    background: var(--accent);
    color: var(--cta-text);
    font-weight: 800;
    font-size: 0.8rem;
    flex-shrink: 0;
  }
  .eyebrow {
    margin: 0;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  h1 {
    margin: 0.1rem 0 0;
    font-size: 1.65rem;
  }
  .live {
    margin-left: auto;
    align-self: center;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 0.3rem 0.55rem;
    border-radius: var(--radius-sm);
    background: #ebe6dc;
    color: var(--muted);
  }
  .live.on {
    background: var(--ok-bg);
    color: var(--ok);
  }
  .id {
    margin: 0.45rem 0 0;
    font-size: 0.85rem;
  }
  .scoreboard {
    padding: 1.1rem 1.15rem 1.2rem;
  }
  .phase {
    margin: 0 0 1rem;
    font-size: 1.05rem;
    font-weight: 700;
    line-height: 1.35;
  }
  .phase.urgent {
    color: var(--warn);
  }
  .phase.wait {
    color: var(--accent);
  }
  .score {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: end;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  .side {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  .side:last-child {
    text-align: right;
    align-items: flex-end;
  }
  .team {
    font-size: 0.8rem;
    font-weight: 650;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .num {
    font-size: 2.6rem;
    font-weight: 800;
    line-height: 1;
    font-variant-numeric: tabular-nums;
  }
  .colon {
    font-size: 2rem;
    font-weight: 700;
    padding-bottom: 0.2rem;
  }
  .meta {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.65rem 1rem;
    margin: 0;
  }
  .meta dt {
    margin: 0;
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--muted);
  }
  .meta dd {
    margin: 0.15rem 0 0;
    font-size: 0.98rem;
    font-weight: 650;
  }
  .banner-note {
    margin: 0.85rem 0 0;
    padding: 0.65rem 0.75rem;
    border-radius: 10px;
    background: var(--warn-bg);
    color: var(--warn);
    font-size: 0.92rem;
    line-height: 1.4;
  }
  .hint-card {
    margin-top: 0.85rem;
    padding: 0.85rem 1rem;
    font-size: 0.95rem;
    line-height: 1.45;
  }
  .spacer {
    flex: 1;
    min-height: 1rem;
  }
  .dock {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 30;
    padding: 0.85rem 1rem calc(0.85rem + env(safe-area-inset-bottom));
    background: color-mix(in srgb, var(--surface) 94%, transparent);
    border-top: 1px solid var(--border);
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
    max-width: 28rem;
    margin: 0 auto;
    width: 100%;
    box-sizing: border-box;
  }
  @media (min-width: 28rem) {
    .dock {
      left: 50%;
      transform: translateX(-50%);
      border-radius: 16px 16px 0 0;
    }
  }
  .dock-hint {
    margin: 0;
    text-align: center;
    font-size: 0.92rem;
    line-height: 1.4;
  }
  .pulse {
    height: 4px;
    border-radius: var(--radius-sm);
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    background-size: 200% 100%;
    animation: slide 1.2s linear infinite;
  }
  @keyframes slide {
    from {
      background-position: 100% 0;
    }
    to {
      background-position: -100% 0;
    }
  }
  .loading {
    margin: 2rem 0;
    text-align: center;
  }
  .toast {
    position: fixed;
    left: 1rem;
    right: 1rem;
    bottom: calc(6.5rem + env(safe-area-inset-bottom));
    z-index: 40;
    max-width: 26rem;
    margin: 0 auto;
    padding: 0.75rem 0.95rem;
    border-radius: var(--radius);
    font-size: 0.95rem;
    line-height: 1.35;
    box-shadow: var(--shadow);
  }
  .toast.ok {
    background: var(--ok-bg);
    color: var(--ok);
  }
  .toast.bad {
    background: var(--danger-muted);
    color: var(--danger);
  }
</style>
