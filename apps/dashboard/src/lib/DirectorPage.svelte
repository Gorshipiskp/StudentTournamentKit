<script lang="ts">
  import { onMount } from 'svelte';
  import {
    SCENES,
    getMatch,
    getMatchAudit,
    getMatchHealth,
    getOverlay,
    getProduction,
    patchScene,
    postOverride,
    type AuditEntry,
    type HealthStatus,
    type MatchHealth,
    type MatchPublic,
    type OverlaySnapshot,
    type ProductionPublic,
    type SceneId,
  } from './api';
  import ToastHost from './ToastHost.svelte';
  import { humanApiError, toastErr, toastOk } from './toast';

  let { matchId }: { matchId: string } = $props();

  let match = $state<MatchPublic | null>(null);
  let production = $state<ProductionPublic | null>(null);
  let overlay = $state<OverlaySnapshot | null>(null);
  let health = $state<MatchHealth | null>(null);
  let audit = $state<AuditEntry[]>([]);
  let busy = $state(false);
  let loading = $state(true);
  let moreOpen = $state(false);
  let delayOpen = $state(false);
  let hotkeyFlash = $state<string | null>(null);

  let teamAName = $state('');
  let teamBName = $state('');
  let scoreA = $state('');
  let scoreB = $state('');
  let delayChecks = $state([false, false, false, false, false]);
  let delayPersistReady = $state(false);

  const DELAY_KEY = () => `stk_director_delay_${matchId}`;

  const SCENE_LABEL: Record<SceneId, string> = {
    waiting: 'Ожидание',
    intro: 'Интро',
    teams: 'Команды',
    ingame: 'Игра',
    break: 'Перерыв',
    winner: 'Победитель',
  };

  const HEALTH_LABEL: Record<HealthStatus, string> = {
    HEALTHY: 'В порядке',
    DEGRADED: 'Есть проблемы',
    OFFLINE: 'Нет связи',
    UNKNOWN: 'Неизвестно',
  };

  const COMPONENT_LABEL: Record<string, string> = {
    platform: 'Платформа',
    agent: 'Агент',
    obs: 'OBS',
    overlay: 'Overlay',
    game_server: 'Сервер',
    broadcast: 'Эфир',
  };

  const HEALTH_ROWS = [
    'platform',
    'agent',
    'obs',
    'overlay',
    'game_server',
    'broadcast',
  ] as const;

  const ACTOR_LABEL: Record<string, string> = {
    organizer: 'Орг.',
    judge: 'Судья',
    director: 'Реж.',
    system: 'Сист.',
  };

  const ACTION_LABEL: Record<string, string> = {
    'organizer.match_start': 'Старт',
    'director.scene_change': 'Сцена',
    'director.score_override': 'Табло',
    'organizer.score_sync': 'Синхронизация табло',
    'judge.review_request': 'Разбор',
    'judge.review_resolve': 'Решение',
    'judge.forfeit': 'Тех. пор.',
    'system.round_end': 'Раунд',
  };

  function matchStatusLabel(s: string): string {
    if (s === 'live') return 'Идёт';
    if (s === 'completed') return 'Завершён';
    if (s === 'forfeited') return 'Тех. поражение';
    if (s === 'pending' || s === 'created' || s === 'ready') return 'Ожидает';
    return s;
  }

  function sceneRu(s: string): string {
    return (SCENE_LABEL as Record<string, string>)[s] || s;
  }

  async function refresh(initial = false) {
    if (initial) loading = true;
    try {
      const [m, p, o, h, a] = await Promise.all([
        getMatch(matchId),
        getProduction(matchId),
        getOverlay(matchId),
        getMatchHealth(matchId),
        getMatchAudit(matchId, 20),
      ]);
      match = m;
      production = p;
      overlay = o;
      health = h;
      audit = a.items;
    } catch (e) {
      toastErr(humanApiError(e instanceof Error ? e.message : String(e)));
    } finally {
      loading = false;
    }
  }

  async function setScene(scene: SceneId) {
    busy = true;
    try {
      production = await patchScene(matchId, scene);
      overlay = await getOverlay(matchId);
      toastOk(SCENE_LABEL[scene]);
      void refresh();
    } catch (e) {
      toastErr(humanApiError(e instanceof Error ? e.message : String(e)));
    } finally {
      busy = false;
    }
  }

  async function submitOverride() {
    busy = true;
    const body: Record<string, string | number> = {};
    if (teamAName.trim()) body.team_a_name = teamAName.trim();
    if (teamBName.trim()) body.team_b_name = teamBName.trim();
    if (scoreA !== '') body.score_team_a = Number(scoreA);
    if (scoreB !== '') body.score_team_b = Number(scoreB);
    try {
      overlay = await postOverride(matchId, body);
      toastOk('Табло обновлено');
      void refresh();
    } catch (e) {
      toastErr(humanApiError(e instanceof Error ? e.message : String(e)));
    } finally {
      busy = false;
    }
  }

  async function clearOverride() {
    busy = true;
    try {
      overlay = await postOverride(matchId, { clear: true });
      teamAName = '';
      teamBName = '';
      scoreA = '';
      scoreB = '';
      toastOk('Правка сброшена');
      void refresh();
    } catch (e) {
      toastErr(humanApiError(e instanceof Error ? e.message : String(e)));
    } finally {
      busy = false;
    }
  }

  function openMore() {
    moreOpen = !moreOpen;
    if (moreOpen && overlay) {
      teamAName = overlay.data.team_a.name;
      teamBName = overlay.data.team_b.name;
      scoreA = String(overlay.data.team_a.score);
      scoreB = String(overlay.data.team_b.score);
    }
  }

  async function copyOverlayUrl() {
    const origin =
      window.location.port === '8080' || window.location.port === '80' || window.location.port === ''
        ? window.location.origin
        : 'http://127.0.0.1:5173';
    const url = `${origin}/overlay/${encodeURIComponent(matchId)}`;
    try {
      await navigator.clipboard.writeText(url);
      toastOk('Ссылка скопирована');
    } catch {
      toastErr('Не удалось скопировать');
    }
  }

  onMount(() => {
    try {
      const raw = sessionStorage.getItem(DELAY_KEY());
      if (raw) {
        const parsed = JSON.parse(raw) as boolean[];
        if (Array.isArray(parsed) && parsed.length === 5) delayChecks = parsed;
      }
    } catch {
      /* ignore */
    }
    delayPersistReady = true;
    void refresh(true);
    const poll = setInterval(() => void refresh(), 2500);

    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement | null)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const n = Number(e.key);
      if (n >= 1 && n <= SCENES.length) {
        e.preventDefault();
        const scene = SCENES[n - 1];
        hotkeyFlash = SCENE_LABEL[scene];
        window.setTimeout(() => {
          if (hotkeyFlash === SCENE_LABEL[scene]) hotkeyFlash = null;
        }, 700);
        void setScene(scene);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => {
      clearInterval(poll);
      window.removeEventListener('keydown', onKey);
    };
  });

  const desired = $derived(production?.desired.scene ?? '—');
  const actual = $derived(production?.actual.scene ?? '—');
  const delaySeconds = $derived(match?.configured_broadcast_delay_seconds ?? null);
  const delayLabel = $derived(
    delaySeconds != null && delaySeconds > 0 ? `${delaySeconds} с` : '90–120 с',
  );
  const overall = $derived(health?.overall ?? null);
  const agentOffline = $derived(
    health?.components.agent.status === 'OFFLINE' ||
      health?.production.agent_status === 'disconnected',
  );
  const obsOk = $derived(health?.components.obs.status === 'HEALTHY');
  const sceneSynced = $derived(desired !== '—' && desired === actual);
  const delayDone = $derived(delayChecks.filter(Boolean).length);

  $effect(() => {
    if (!delayPersistReady) return;
    try {
      sessionStorage.setItem(DELAY_KEY(), JSON.stringify(delayChecks));
    } catch {
      /* ignore */
    }
  });

  const problems = $derived(
    HEALTH_ROWS.filter((key) => {
      const s = health?.components[key]?.status;
      return s && s !== 'HEALTHY';
    }),
  );

  const recentAudit = $derived(audit.slice(0, 12));

  const delayChecklist = [
    'OBS → Дополнительно → Задержка трансляции',
    'Значение как целевая задержка выше',
    'Комментаторам — без этой задержки',
    'Проверь stream key Twitch',
    'Пробный выход / запись с delay',
  ] as const;

  function formatAuditTime(iso: string | null): string {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return iso;
      return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return iso;
    }
  }

  function auditDetail(entry: AuditEntry): string {
    const p = entry.payload || {};
    if (entry.action === 'director.scene_change') {
      return `${sceneRu(String(p.from ?? '?'))} → ${sceneRu(String(p.to ?? '?'))}`;
    }
    if (entry.action === 'judge.forfeit' && p.losing_team) {
      return String(p.losing_team);
    }
    return '';
  }
</script>

<div class="director-app">
  <div class="shell">
    <header class="top">
      <div>
        <p class="eyebrow muted">Режиссёр</p>
        <h1 class="display">
          {#if match && overlay}
            {overlay.data.team_a.name}
            <span class="score"
              >{match.score.team_a}:{match.score.team_b}</span
            >
            {overlay.data.team_b.name}
          {:else}
            Эфир
          {/if}
        </h1>
        <p class="sub muted">
          {#if match}
            {matchStatusLabel(match.status)}
            {#if match.map} · {match.map}{/if}
            · р. {match.round}
          {/if}
          · сцена <strong>{sceneRu(String(desired))}</strong>
          {#if !sceneSynced}
            <span class="warn-t">(OBS: {sceneRu(String(actual))})</span>
          {/if}
        </p>
      </div>
      <div class="top-actions">
        {#if overall}
          <span class="pill status-{overall}">{HEALTH_LABEL[overall]}</span>
        {/if}
      </div>
    </header>

    {#if hotkeyFlash}
      <div class="hotkey-flash" role="status">{hotkeyFlash}</div>
    {/if}

    {#if loading && !match}
      <p class="loading muted">Загрузка…</p>
    {:else}
      {#if agentOffline}
        <p class="callout warn" role="status">Агент не подключён — сцены в OBS не сменятся. Запусти Agent.</p>
      {:else if health && !obsOk}
        <p class="callout warn" role="status">OBS не на связи. Проверь WebSocket или Fake OBS.</p>
      {/if}

      {#if match?.judge_banner}
        <p class="callout judge" role="status">Судья: {match.judge_banner}</p>
      {/if}

      <section class="scenes" aria-label="Сцена эфира">
        <div class="scene-row">
          {#each SCENES as scene, i}
            <button
              type="button"
              class="scene-btn"
              class:active={desired === scene}
              disabled={busy}
              onclick={() => setScene(scene)}
            >
              <span class="k" aria-hidden="true">{i + 1}</span>
              {SCENE_LABEL[scene]}
            </button>
          {/each}
        </div>
        <p class="hint muted">Клавиши 1–6 · смена сцены в OBS через агент</p>
      </section>

      {#if problems.length > 0}
        <section class="problems" aria-label="Проблемы">
          <p class="problems-title">Нужно внимание</p>
          <ul>
            {#each problems as key}
              {@const row = health!.components[key]}
              <li>
                <span class="dot status-{row.status}"></span>
                {COMPONENT_LABEL[key] || key}: {HEALTH_LABEL[row.status]}
              </li>
            {/each}
          </ul>
        </section>
      {/if}

      <button type="button" class="more-toggle" aria-expanded={moreOpen} onclick={() => openMore()}>
        {moreOpen ? 'Скрыть дополнительно' : 'Дополнительно — табло, задержка, журнал'}
      </button>

      {#if moreOpen}
        <section class="more">
          <div class="block">
            <h2>Правка табло</h2>
            <p class="hint muted">Временные имена и счёт только на эфире</p>
            <form
              class="override"
              onsubmit={(e) => {
                e.preventDefault();
                void submitOverride();
              }}
            >
              <label class="field">Команда A <input bind:value={teamAName} /></label>
              <label class="field">Команда B <input bind:value={teamBName} /></label>
              <label class="field">Счёт A <input bind:value={scoreA} type="number" min="0" /></label>
              <label class="field">Счёт B <input bind:value={scoreB} type="number" min="0" /></label>
              <div class="row-actions">
                <button type="submit" class="btn btn-primary" disabled={busy}>Применить</button>
                <button type="button" class="btn btn-ghost" disabled={busy} onclick={() => clearOverride()}
                  >Сбросить</button
                >
                <button type="button" class="btn btn-ghost" onclick={() => copyOverlayUrl()}
                  >Ссылка overlay</button
                >
              </div>
            </form>
          </div>

          <div class="block">
            <button
              type="button"
              class="subfold"
              aria-expanded={delayOpen}
              onclick={() => (delayOpen = !delayOpen)}
            >
              Задержка Twitch · {delayLabel} · {delayDone}/{delayChecklist.length}
              <span>{delayOpen ? '▴' : '▾'}</span>
            </button>
            {#if delayOpen}
              <ol class="checklist">
                {#each delayChecklist as item, i}
                  <li>
                    <label>
                      <input
                        type="checkbox"
                        checked={delayChecks[i]}
                        onchange={(e) => {
                          const next = [...delayChecks];
                          next[i] = e.currentTarget.checked;
                          delayChecks = next;
                        }}
                      />
                      {item}
                    </label>
                  </li>
                {/each}
              </ol>
            {/if}
          </div>

          <div class="block">
            <h2>Журнал</h2>
            {#if recentAudit.length === 0}
              <p class="muted">Пока пусто</p>
            {:else}
              <ul class="audit">
                {#each recentAudit as entry (entry.id)}
                  <li>
                    <time>{formatAuditTime(entry.created_at)}</time>
                    <span>{ACTOR_LABEL[entry.actor_type] || entry.actor_type}</span>
                    <strong>{ACTION_LABEL[entry.action] || entry.action}</strong>
                    {#if auditDetail(entry)}
                      <span class="muted">{auditDetail(entry)}</span>
                    {/if}
                  </li>
                {/each}
              </ul>
            {/if}
          </div>
        </section>
      {/if}
    {/if}
  </div>
  <ToastHost />
</div>

<style>
  .director-app {
    min-height: 100%;
    min-height: 100dvh;
    color: var(--text);
    font-family: var(--font);
  }
  .shell {
    max-width: 52rem;
    margin: 0 auto;
    padding: 1.25rem 1.15rem 2.5rem;
  }
  .top {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1.25rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid var(--border);
  }
  .eyebrow {
    margin: 0;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-dim);
  }
  h1 {
    margin: 0.25rem 0 0;
    font-size: clamp(1.35rem, 3vw, 1.75rem);
    font-weight: 600;
    letter-spacing: -0.03em;
  }
  .score {
    margin: 0 0.35rem;
    color: var(--accent);
    font-variant-numeric: tabular-nums;
  }
  .sub {
    margin: 0.35rem 0 0;
    font-size: 0.9rem;
  }
  .sub strong {
    color: var(--text);
  }
  .warn-t {
    color: var(--warn);
  }
  .pill {
    display: inline-block;
    padding: 0.28rem 0.55rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
  }
  .pill.status-HEALTHY {
    color: var(--ok);
    background: var(--ok-muted);
  }
  .pill.status-DEGRADED,
  .pill.status-UNKNOWN {
    color: var(--warn);
    background: var(--warn-muted);
  }
  .pill.status-OFFLINE {
    color: var(--danger);
    background: var(--danger-muted);
  }
  .callout {
    margin: 0 0 0.85rem;
    padding: 0.7rem 0.9rem;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    border-left: 2px solid var(--warn);
    background: var(--warn-muted);
    font-size: 0.92rem;
    line-height: 1.4;
  }
  .callout.judge {
    border-left-color: var(--accent);
    background: var(--accent-muted);
  }
  .scenes {
    margin-bottom: 1rem;
  }
  .scene-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.45rem;
  }
  @media (min-width: 640px) {
    .scene-row {
      grid-template-columns: repeat(6, 1fr);
    }
  }
  .scene-btn {
    position: relative;
    min-height: 3.4rem;
    padding: 0.65rem 0.4rem;
    border-radius: var(--radius);
    border: 1px solid var(--border-strong);
    background: var(--bg-elevated);
    color: var(--text);
    font: inherit;
    font-weight: 600;
    font-size: 0.92rem;
    cursor: pointer;
  }
  .scene-btn:hover:not(:disabled) {
    background: var(--bg-hover);
  }
  .scene-btn.active {
    border-color: var(--accent-line);
    box-shadow: 0 0 0 1px var(--accent-muted);
    color: var(--accent);
  }
  .scene-btn:disabled {
    opacity: 0.45;
  }
  .k {
    position: absolute;
    top: 0.3rem;
    right: 0.4rem;
    font-size: 0.65rem;
    color: var(--text-dim);
    font-weight: 700;
  }
  .hint {
    margin: 0.55rem 0 0;
    font-size: 0.8rem;
  }
  .problems {
    margin-bottom: 1rem;
    padding: 0.75rem 0.9rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--bg-elevated);
  }
  .problems-title {
    margin: 0 0 0.45rem;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-dim);
    font-weight: 600;
  }
  .problems ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 0.35rem;
  }
  .problems li {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.9rem;
  }
  .dot {
    width: 0.45rem;
    height: 0.45rem;
    border-radius: 50%;
    background: var(--text-dim);
  }
  .dot.status-DEGRADED {
    background: var(--warn);
  }
  .dot.status-OFFLINE {
    background: var(--danger);
  }
  .more-toggle {
    width: 100%;
    min-height: var(--touch);
    padding: 0.65rem 0.9rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: transparent;
    color: var(--text-muted);
    font: inherit;
    font-weight: 500;
    text-align: left;
    cursor: pointer;
  }
  .more-toggle:hover {
    color: var(--text);
    background: var(--bg-hover);
  }
  .more {
    margin-top: 0.75rem;
    display: grid;
    gap: 0.75rem;
  }
  .block {
    padding: 1rem 1.1rem;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    background: var(--bg-elevated);
  }
  .block h2 {
    margin: 0 0 0.5rem;
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-dim);
    font-weight: 600;
  }
  .override {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.55rem;
  }
  .override .row-actions {
    grid-column: 1 / -1;
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin-top: 0.25rem;
  }
  .subfold {
    width: 100%;
    display: flex;
    justify-content: space-between;
    gap: 0.5rem;
    padding: 0;
    border: none;
    background: none;
    color: var(--text);
    font: inherit;
    font-weight: 600;
    cursor: pointer;
    text-align: left;
  }
  .checklist {
    margin: 0.75rem 0 0;
    padding: 0 0 0 1.1rem;
    display: grid;
    gap: 0.45rem;
    font-size: 0.88rem;
    color: var(--text-muted);
  }
  .checklist label {
    display: flex;
    gap: 0.45rem;
    align-items: flex-start;
    cursor: pointer;
  }
  .audit {
    list-style: none;
    margin: 0.5rem 0 0;
    padding: 0;
    display: grid;
    gap: 0.35rem;
    font-size: 0.82rem;
  }
  .audit li {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem 0.55rem;
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--border);
  }
  .audit time {
    color: var(--text-dim);
    font-variant-numeric: tabular-nums;
  }
  .loading {
    text-align: center;
    padding: 2rem;
  }
  .hotkey-flash {
    position: fixed;
    top: 1rem;
    left: 50%;
    transform: translateX(-50%);
    z-index: 40;
    padding: 0.45rem 0.9rem;
    border-radius: 999px;
    background: var(--cta);
    color: var(--cta-text);
    font-weight: 700;
    pointer-events: none;
  }
  .muted {
    color: var(--text-muted);
  }
  .display {
    font-family: var(--font-display);
  }
</style>
