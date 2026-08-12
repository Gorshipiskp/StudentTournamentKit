<script lang="ts">
  import {
    createStaffLinks,
    fetchWhipPublish,
    getMatchHealth,
    getMatchPublic,
    startMatch,
    startMatchLive,
    syncMatchScoreboard,
    type StaffLinks,
    type WhipPublishCredentials,
  } from './api';
  import { humanApiError, toastErr, toastOk } from './toast';

  let { matchId }: { matchId: string } = $props();

  let status = $state<string>('…');
  let busy = $state(false);
  let links = $state<StaffLinks | null>(null);
  let whip = $state<WhipPublishCredentials | null>(null);
  let whipReady = $state<boolean | null>(null);
  let whipDetail = $state<string | null>(null);
  let copied = $state<string | null>(null);
  let liveNote = $state<string | null>(null);
  let scoreA = $state('0');
  let scoreB = $state('0');
  let roundNo = $state('0');

  $effect(() => {
    void refreshStatus(matchId);
    void pollWhip(matchId);
    const t = window.setInterval(() => void pollWhip(matchId), 3000);
    return () => window.clearInterval(t);
  });

  function statusBadge(s: string): string {
    if (s === 'live') return 'badge-live';
    if (s === 'completed' || s === 'finished') return 'badge-completed';
    return 'badge-idle';
  }

  function statusLabel(s: string): string {
    if (s === 'live') return 'Идёт';
    if (s === 'pending' || s === 'created') return 'Ожидает';
    if (s === 'completed' || s === 'finished') return 'Завершён';
    return s;
  }

  async function refreshStatus(id: string) {
    try {
      const m = await getMatchPublic(id);
      status = m.status;
      scoreA = String(m.score?.team_a ?? 0);
      scoreB = String(m.score?.team_b ?? 0);
      roundNo = String(m.round ?? 0);
    } catch {
      status = '?';
    }
  }

  async function pollWhip(id: string) {
    try {
      const h = await getMatchHealth(id);
      const w = h.components.whip;
      if (!w) {
        whipReady = null;
        whipDetail = null;
        return;
      }
      whipReady = w.status === 'HEALTHY';
      whipDetail = w.detail ?? w.status;
    } catch {
      whipReady = null;
      whipDetail = null;
    }
  }

  async function fetchLinks(silent = false) {
    try {
      links = await createStaffLinks(matchId);
      if (!silent) toastOk('Ссылки готовы');
    } catch (e) {
      toastErr(humanApiError(e instanceof Error ? e.message : String(e)));
    }
  }

  async function onStartFake() {
    busy = true;
    liveNote = null;
    try {
      const res = await startMatch(matchId);
      status = res.match.status;
      toastOk('Репетиция запущена — ссылки для команды готовы');
      await fetchLinks(true);
      await refreshStatus(matchId);
    } catch (e) {
      toastErr(humanApiError(e instanceof Error ? e.message : String(e)));
    } finally {
      busy = false;
    }
  }

  async function onStartLive() {
    busy = true;
    liveNote = null;
    try {
      const res = await startMatchLive(matchId);
      status = res.match.status;
      const cfg = res.bridge_config;
      liveNote = res.note
        ? res.note
        : cfg
          ? `Локальный сервер: матч ${cfg.MatchId}, сервер ${cfg.ServerId}`
          : 'Старт на локальном сервере выполнен';
      toastOk('Матч на локальном сервере запущен');
      await fetchLinks(true);
      await refreshStatus(matchId);
    } catch (e) {
      toastErr(humanApiError(e instanceof Error ? e.message : String(e)));
    } finally {
      busy = false;
    }
  }

  async function onLinks() {
    busy = true;
    try {
      await fetchLinks(false);
    } finally {
      busy = false;
    }
  }

  async function onWhip() {
    busy = true;
    try {
      whip = await fetchWhipPublish(matchId);
      toastOk('Данные для OBS готовы — скопируйте сервер и токен');
      await pollWhip(matchId);
    } catch (e) {
      toastErr(humanApiError(e instanceof Error ? e.message : String(e)));
    } finally {
      busy = false;
    }
  }

  async function onScoreSyncFromServer() {
    busy = true;
    try {
      const res = await syncMatchScoreboard(matchId, { from_server: true });
      scoreA = String(res.match.score.team_a);
      scoreB = String(res.match.score.team_b);
      roundNo = String(res.match.round);
      toastOk(res.note || 'Табло взято с игрового сервера');
    } catch (e) {
      toastErr(humanApiError(e instanceof Error ? e.message : String(e)));
    } finally {
      busy = false;
    }
  }

  async function onScoreSyncManual() {
    busy = true;
    try {
      const a = Number(scoreA);
      const b = Number(scoreB);
      const r = Number(roundNo);
      if (![a, b, r].every((n) => Number.isFinite(n) && n >= 0)) {
        toastErr('Счёт и раунд — целые числа от 0');
        return;
      }
      const res = await syncMatchScoreboard(matchId, {
        from_server: false,
        score_team_a: Math.trunc(a),
        score_team_b: Math.trunc(b),
        round: Math.trunc(r),
      });
      scoreA = String(res.match.score.team_a);
      scoreB = String(res.match.score.team_b);
      roundNo = String(res.match.round);
      toastOk(res.note || 'Табло записано вручную');
    } catch (e) {
      toastErr(humanApiError(e instanceof Error ? e.message : String(e)));
    } finally {
      busy = false;
    }
  }

  async function copy(label: string, text: string) {
    try {
      await navigator.clipboard.writeText(text);
      copied = label;
      setTimeout(() => {
        if (copied === label) copied = null;
      }, 1600);
    } catch {
      toastErr('Не удалось скопировать — выделите текст вручную');
    }
  }
</script>

<div class="ops surface">
  <div class="ops-head">
    <h3 class="display">Запуск</h3>
    <span class="badge {statusBadge(status)}">{statusLabel(status)}</span>
    <button type="button" class="btn btn-ghost refresh" disabled={busy} onclick={() => refreshStatus(matchId)}
      >Обновить</button
    >
  </div>

  <div class="row">
    <button type="button" class="btn btn-primary" disabled={busy} onclick={onStartFake}>
      {busy ? 'Запускаем…' : 'Репетиция'}
    </button>
    <button type="button" class="btn btn-ghost" disabled={busy} onclick={onStartLive}>
      Локальный сервер
    </button>
    <button type="button" class="btn btn-ghost" disabled={busy} onclick={onLinks}>
      {links ? 'Обновить ссылки' : 'Ссылки'}
    </button>
    <button type="button" class="btn btn-ghost" disabled={busy} onclick={onWhip}>
      {whip ? 'Обновить OBS' : 'Данные для OBS'}
    </button>
    <a class="btn btn-ghost" href={`/director/${encodeURIComponent(matchId)}`}>Режиссёр</a>
  </div>

  <div class="score-sync">
    <h4 class="display">Табло на эфире</h4>
    <p class="hint muted">
      Платформа помнит старый счёт, пока события с CS2 не пришли или не «залипли». Кнопка «С
      сервера» запрашивает актуальный снимок у игрового сервера и сразу обновляет эфир.
    </p>
    <div class="score-row">
      <button
        type="button"
        class="btn btn-primary"
        disabled={busy}
        onclick={onScoreSyncFromServer}
      >
        С сервера
      </button>
      <label class="field">
        Счёт A
        <input bind:value={scoreA} type="number" min="0" step="1" />
      </label>
      <label class="field">
        Счёт B
        <input bind:value={scoreB} type="number" min="0" step="1" />
      </label>
      <label class="field">
        Раунд
        <input bind:value={roundNo} type="number" min="0" step="1" />
      </label>
      <button type="button" class="btn btn-ghost" disabled={busy} onclick={onScoreSyncManual}>
        Записать вручную
      </button>
    </div>
  </div>

  <p
    class="whip-status"
    class:ok={whipReady === true}
    class:bad={whipReady === false}
    role="status"
  >
    {#if whipReady === true}
      Эфир с OBS доходит до сервера — комментаторы должны видеть картинку.
    {:else if whipReady === false}
      OBS ещё не шлёт картинку на этот матч. Скопируйте данные ниже и в OBS нажмите «Начать
      трансляцию» (сервис WHIP).
    {:else}
      Статус эфира OBS: проверяем…
    {/if}
  </p>

  {#if liveNote}
    <p class="note">{liveNote}</p>
  {/if}

  {#if whip}
    <div class="whip">
      <h4 class="display">OBS — картинка комментаторам</h4>
      <ol class="steps muted">
        <li>Настройки → Трансляция → сервис <strong>WHIP</strong> (не Twitch и не «Свой»).</li>
        <li>
          Поле <strong>Сервер</strong> = строка ниже целиком (должна заканчиваться на
          <code>/whip</code>).
        </li>
        <li>
          Поле <strong>Токен предъявителя</strong> = токен ниже <em>без</em> слова Bearer.
        </li>
        <li>«Применить» → «Начать трансляцию». Статус выше должен стать зелёным.</li>
      </ol>
      <p class="hint muted">
        Токен ~{Math.round(whip.ttl / 60)} мин. Если OBS пишет ошибку — «Обновить OBS» и вставьте
        заново. Нужен OBS Studio 30+.
      </p>
      <ul class="links">
        <li>
          <span>Сервер</span>
          <code>{whip.whip_url}</code>
          <button type="button" class="btn btn-ghost" onclick={() => copy('whip-url', whip!.whip_url)}>
            {copied === 'whip-url' ? 'Скопировано' : 'Скопировать'}
          </button>
        </li>
        <li>
          <span>Токен</span>
          <code class="token">{whip.bearer}</code>
          <button type="button" class="btn btn-ghost" onclick={() => copy('whip-tok', whip!.bearer)}>
            {copied === 'whip-tok' ? 'Скопировано' : 'Скопировать'}
          </button>
        </li>
      </ul>
      {#if whipDetail && whipReady === false}
        <p class="hint muted">Сервер: {whipDetail}</p>
      {/if}
    </div>
  {/if}

  {#if links}
    <ul class="links">
      <li>
        <span>Режиссёр</span>
        <code>{links.director_url}</code>
        <button type="button" class="btn btn-ghost" onclick={() => copy('dir', links!.director_url)}>
          {copied === 'dir' ? 'Скопировано' : 'Скопировать'}
        </button>
      </li>
      <li>
        <span>Судья</span>
        <code>{links.judge.url}</code>
        <button type="button" class="btn btn-ghost" onclick={() => copy('judge', links!.judge.url)}>
          {copied === 'judge' ? 'Скопировано' : 'Скопировать'}
        </button>
      </li>
      <li>
        <span>Комментатор</span>
        <code>{links.commentator.url}</code>
        <button
          type="button"
          class="btn btn-ghost"
          onclick={() => copy('watch', links!.commentator.url)}
        >
          {copied === 'watch' ? 'Скопировано' : 'Скопировать'}
        </button>
      </li>
    </ul>
    <details class="more">
      <summary class="muted">Что выбрать</summary>
      <p class="hint muted">
        Репетиция — без CS2. Локальный сервер — живой матч. «Данные для OBS» — сервер и токен WHIP
        для картинки на /watch.
      </p>
    </details>
  {:else}
    <details class="more">
      <summary class="muted">Что выбрать</summary>
      <p class="hint muted">
        Репетиция — без CS2. Для эфира комментаторам: «Данные для OBS» → вставить в OBS (WHIP) →
        начать трансляцию.
      </p>
    </details>
  {/if}
</div>

<style>
  .ops {
    margin-top: 0.75rem;
    padding: 1rem 1.05rem;
  }
  .ops-head {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.55rem;
    margin-bottom: 0.75rem;
  }
  h3 {
    margin: 0;
    font-size: 1.05rem;
  }
  h4 {
    margin: 0.85rem 0 0.35rem;
    font-size: 0.98rem;
  }
  .refresh {
    margin-left: auto;
    min-height: 2.2rem;
    padding: 0.35rem 0.7rem;
    font-size: 0.85rem;
  }
  .row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
  }
  .score-sync {
    margin-top: 0.85rem;
    padding-top: 0.75rem;
    border-top: 1px solid var(--border);
  }
  .score-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    align-items: flex-end;
    margin-top: 0.45rem;
  }
  .score-row .field {
    margin: 0;
    min-width: 5.5rem;
  }
  .score-row .field input {
    width: 5.5rem;
  }
  .whip-status {
    margin: 0.75rem 0 0;
    padding: 0.55rem 0.75rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    font-size: 0.9rem;
    line-height: 1.35;
    background: var(--bg-input);
  }
  .whip-status.ok {
    border-color: color-mix(in srgb, var(--ok) 45%, var(--border));
    color: var(--ok);
  }
  .whip-status.bad {
    border-color: color-mix(in srgb, var(--accent) 40%, var(--border));
    color: var(--text);
  }
  .whip {
    margin-top: 0.75rem;
    padding-top: 0.65rem;
    border-top: 1px solid var(--border);
  }
  .steps {
    margin: 0.35rem 0 0.5rem;
    padding-left: 1.2rem;
    font-size: 0.88rem;
    line-height: 1.45;
  }
  .hint {
    margin: 0.45rem 0 0;
    font-size: 0.85rem;
    line-height: 1.4;
  }
  .note {
    margin: 0.5rem 0 0;
    font-size: 0.88rem;
  }
  .more {
    margin-top: 0.65rem;
  }
  .more summary {
    cursor: pointer;
    font-size: 0.85rem;
  }
  .links {
    list-style: none;
    margin: 0.75rem 0 0;
    padding: 0;
    border-top: 1px solid var(--border);
  }
  .whip .links {
    margin-top: 0.5rem;
    border-top: none;
  }
  .links li {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    align-items: center;
    padding: 0.55rem 0;
    border-top: 1px solid var(--border);
    font-size: 0.9rem;
  }
  .whip .links li:first-child {
    border-top: none;
  }
  .links span {
    min-width: 6.5rem;
    color: var(--muted);
    font-weight: 600;
  }
  .links code {
    flex: 1 1 12rem;
    word-break: break-all;
    font-size: 0.78rem;
    background: var(--bg-input);
    padding: 0.35rem 0.5rem;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    font-family: var(--mono);
  }
  .links code.token {
    user-select: all;
  }
</style>
