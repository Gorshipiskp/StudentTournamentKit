<script lang="ts">
  import OverlayView from './OverlayView.svelte';
  import type { OverlaySnapshot } from './snapshot';
  import { parseOverlaySnapshot } from './snapshot';
  import {
    buildLabFx,
    emptyLabSnapshot,
    patchOverlayScene,
    postOverlayFx,
    postOverlayOverride,
    type LabFxKind,
  } from './overlayLab';

  const SCENES = ['waiting', 'intro', 'teams', 'ingame', 'break', 'winner'] as const;

  let matchId = $state(
    typeof location !== 'undefined'
      ? new URLSearchParams(location.search).get('match') || ''
      : '',
  );
  let pushLive = $state(false);
  let snapshot = $state<OverlaySnapshot>(emptyLabSnapshot());
  let note = $state<string | null>(null);
  let busy = $state(false);

  let scoreA = $state(4);
  let scoreB = $state(3);
  let roundNo = $state(8);

  function bumpLocal(mutator: (s: OverlaySnapshot) => OverlaySnapshot) {
    snapshot = mutator({
      ...snapshot,
      version: snapshot.version + 1,
      data: { ...snapshot.data, fx: snapshot.data.fx ?? null },
    });
  }

  function applyLocalFx(kind: LabFxKind, opts?: Parameters<typeof buildLabFx>[1]) {
    const fx = buildLabFx(kind, opts);
    bumpLocal((s) => ({
      ...s,
      data: { ...s.data, fx, scene: s.data.scene === 'waiting' ? 'ingame' : s.data.scene },
    }));
    note = `Локально: ${fx.label}`;
  }

  async function fire(kind: LabFxKind, opts?: Parameters<typeof buildLabFx>[1]) {
    if (!pushLive || !matchId.trim()) {
      applyLocalFx(kind, opts);
      return;
    }
    busy = true;
    note = null;
    try {
      const body: Record<string, string | number | boolean | null> = { kind };
      if (opts?.side) body.side = opts.side;
      if (opts?.site != null) body.site = opts.site;
      if (opts?.round != null) body.round = opts.round;
      if (opts?.timer_sec != null) body.timer_sec = opts.timer_sec;
      if (opts?.has_kit != null) body.has_kit = opts.has_kit;
      const raw = await postOverlayFx(matchId.trim(), body);
      snapshot = parseOverlaySnapshot(raw);
      note = `На матч ${matchId.trim()}: ${kind}`;
    } catch (e) {
      note = e instanceof Error ? e.message : String(e);
      applyLocalFx(kind, opts);
    } finally {
      busy = false;
    }
  }

  async function clearFx() {
    if (!pushLive || !matchId.trim()) {
      bumpLocal((s) => ({ ...s, data: { ...s.data, fx: null } }));
      note = 'FX сброшен (локально)';
      return;
    }
    busy = true;
    try {
      const raw = await postOverlayFx(matchId.trim(), { clear: true });
      snapshot = parseOverlaySnapshot(raw);
      note = 'FX сброшен на матче';
    } catch (e) {
      note = e instanceof Error ? e.message : String(e);
    } finally {
      busy = false;
    }
  }

  async function setScene(scene: (typeof SCENES)[number]) {
    if (!pushLive || !matchId.trim()) {
      bumpLocal((s) => ({ ...s, data: { ...s.data, scene } }));
      note = `Сцена: ${scene}`;
      return;
    }
    busy = true;
    try {
      await patchOverlayScene(matchId.trim(), scene);
      const res = await fetch(`/api/v1/matches/${encodeURIComponent(matchId.trim())}/overlay`);
      if (res.ok) snapshot = parseOverlaySnapshot(await res.json());
      note = `Сцена на матче: ${scene}`;
    } catch (e) {
      note = e instanceof Error ? e.message : String(e);
    } finally {
      busy = false;
    }
  }

  async function pushScore() {
    bumpLocal((s) => ({
      ...s,
      data: {
        ...s.data,
        team_a: { ...s.data.team_a, score: scoreA },
        team_b: { ...s.data.team_b, score: scoreB },
        round: roundNo,
      },
    }));
    if (!pushLive || !matchId.trim()) {
      note = 'Счёт обновлён локально';
      return;
    }
    busy = true;
    try {
      const raw = await postOverlayOverride(matchId.trim(), {
        score_team_a: scoreA,
        score_team_b: scoreB,
        round: roundNo,
      });
      snapshot = parseOverlaySnapshot(raw);
      note = 'Счёт отправлен на матч';
    } catch (e) {
      note = e instanceof Error ? e.message : String(e);
    } finally {
      busy = false;
    }
  }

  function resetLocal() {
    snapshot = emptyLabSnapshot(matchId.trim() || 'lab');
    scoreA = 4;
    scoreB = 3;
    roundNo = 8;
    note = 'Превью сброшено';
  }
</script>

<div class="lab">
  <aside class="panel">
    <header class="head">
      <p class="eyebrow">StudentTournamentKit</p>
      <h1>Лаборатория оверлея</h1>
      <p class="hint">
        Жмите кнопки — анимации в превью справа. Включите «На живой матч», чтобы слать в OBS
        Browser Source через API.
      </p>
    </header>

    <label class="field">
      Match ID
      <input type="text" bind:value={matchId} placeholder="m_… или uuid" spellcheck="false" />
    </label>

    <label class="check">
      <input type="checkbox" bind:checked={pushLive} disabled={!matchId.trim()} />
      На живой матч (WS → OBS)
    </label>

    <section class="block">
      <h2>Анимации</h2>
      <div class="grid">
        <button type="button" class="btn primary" disabled={busy} onclick={() => fire('round_win', { side: 'team_a', round: roundNo })}
          >Победа CT</button
        >
        <button type="button" class="btn primary" disabled={busy} onclick={() => fire('round_win', { side: 'team_b', round: roundNo })}
          >Победа T</button
        >
        <button type="button" class="btn" disabled={busy} onclick={() => fire('bomb_planted', { site: 1 })}
          >Бомба A</button
        >
        <button type="button" class="btn" disabled={busy} onclick={() => fire('bomb_planted', { site: 2 })}
          >Бомба B</button
        >
        <button type="button" class="btn" disabled={busy} onclick={() => fire('bomb_defusing', { has_kit: true })}
          >Дефьюз (кит)</button
        >
        <button type="button" class="btn" disabled={busy} onclick={() => fire('bomb_defusing', { has_kit: false })}
          >Дефьюз</button
        >
        <button type="button" class="btn" disabled={busy} onclick={() => fire('bomb_defused')}>Разминирована</button>
        <button type="button" class="btn" disabled={busy} onclick={() => fire('bomb_exploded')}>Взрыв</button>
        <button type="button" class="btn ghost" disabled={busy} onclick={() => clearFx()}>Сбросить FX</button>
      </div>
    </section>

    <section class="block">
      <h2>Табло</h2>
      <div class="scores">
        <label
          >A <input type="number" min="0" bind:value={scoreA} /></label
        >
        <label
          >B <input type="number" min="0" bind:value={scoreB} /></label
        >
        <label
          >Раунд <input type="number" min="0" bind:value={roundNo} /></label
        >
        <button type="button" class="btn" disabled={busy} onclick={() => pushScore()}>Применить</button>
      </div>
    </section>

    <section class="block">
      <h2>Сцены</h2>
      <div class="grid scenes">
        {#each SCENES as scene}
          <button
            type="button"
            class="btn"
            class:active={snapshot.data.scene === scene}
            disabled={busy}
            onclick={() => setScene(scene)}>{scene}</button
          >
        {/each}
      </div>
    </section>

    <div class="footer">
      <button type="button" class="btn ghost" onclick={resetLocal}>Сбросить превью</button>
      {#if note}
        <p class="note" role="status">{note}</p>
      {/if}
      <p class="tip">
        OBS: <code>/overlay/&lt;matchId&gt;</code> · эта панель: <code>/overlay-lab</code>
      </p>
    </div>
  </aside>

  <div class="stage-wrap">
    <div class="stage-frame">
      <OverlayView {snapshot} connection="open" />
    </div>
  </div>
</div>

<style>
  .lab {
    --lab-bg: #0b1218;
    --lab-panel: #121a22;
    --lab-line: rgba(255, 248, 235, 0.1);
    --lab-accent: #d4a84b;
    display: grid;
    grid-template-columns: min(380px, 100%) 1fr;
    min-height: 100dvh;
    background: var(--lab-bg);
    color: #f5efe4;
    font-family: var(--font, system-ui, sans-serif);
  }

  .panel {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1.25rem 1.15rem 1.5rem;
    background: var(--lab-panel);
    border-right: 1px solid var(--lab-line);
    overflow: auto;
  }

  .eyebrow {
    margin: 0;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--lab-accent);
  }

  h1 {
    margin: 0.25rem 0 0;
    font-family: var(--font-display, inherit);
    font-size: 1.45rem;
    letter-spacing: 0.02em;
  }

  .hint,
  .tip,
  .note {
    margin: 0.55rem 0 0;
    font-size: 0.82rem;
    line-height: 1.4;
    color: rgba(245, 239, 228, 0.65);
  }

  .note {
    color: var(--lab-accent);
  }

  .field,
  .scores label {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: rgba(245, 239, 228, 0.55);
  }

  input[type='text'],
  input:not([type]),
  input[type='number'] {
    padding: 0.55rem 0.65rem;
    border: 1px solid var(--lab-line);
    border-radius: 2px;
    background: #0b1218;
    color: inherit;
    font: inherit;
    letter-spacing: 0;
    text-transform: none;
    font-weight: 500;
  }

  .check {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.88rem;
  }

  .block h2 {
    margin: 0 0 0.55rem;
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: rgba(245, 239, 228, 0.5);
  }

  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.45rem;
  }

  .scenes {
    grid-template-columns: repeat(3, 1fr);
  }

  .scores {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr auto;
    gap: 0.45rem;
    align-items: end;
  }

  .btn {
    padding: 0.55rem 0.65rem;
    border: 1px solid var(--lab-line);
    border-radius: 2px;
    background: #18222c;
    color: inherit;
    font: inherit;
    font-size: 0.82rem;
    font-weight: 650;
    cursor: pointer;
  }

  .btn:hover:not(:disabled) {
    border-color: color-mix(in srgb, var(--lab-accent) 55%, transparent);
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: wait;
  }

  .btn.primary {
    background: color-mix(in srgb, var(--lab-accent) 22%, #18222c);
    border-color: color-mix(in srgb, var(--lab-accent) 45%, transparent);
  }

  .btn.ghost {
    background: transparent;
  }

  .btn.active {
    border-color: var(--lab-accent);
    color: var(--lab-accent);
  }

  .footer {
    margin-top: auto;
    padding-top: 0.5rem;
  }

  .tip code {
    font-size: 0.78em;
    color: var(--lab-accent);
  }

  .stage-wrap {
    display: grid;
    place-items: center;
    padding: 1.25rem;
    background:
      radial-gradient(ellipse 60% 40% at 50% 0%, rgba(212, 168, 75, 0.08), transparent 60%),
      repeating-conic-gradient(#101820 0% 25%, #0c1319 0% 50%) 0 0 / 28px 28px;
  }

  .stage-frame {
    width: min(100%, 1280px);
    aspect-ratio: 16 / 9;
    background: transparent;
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.55);
    border: 1px solid var(--lab-line);
    overflow: hidden;
    position: relative;
  }

  .stage-frame :global(.stage) {
    width: 100%;
    height: 100%;
  }

  @media (max-width: 960px) {
    .lab {
      grid-template-columns: 1fr;
    }

    .panel {
      border-right: none;
      border-bottom: 1px solid var(--lab-line);
      max-height: none;
    }

    .stage-frame {
      width: 100%;
    }
  }
</style>
