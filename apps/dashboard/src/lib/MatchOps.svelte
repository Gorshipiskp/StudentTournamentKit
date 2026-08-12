<script lang="ts">
  import {
    createStaffLinks,
    getMatchPublic,
    startMatch,
    type StaffLinks,
  } from './api';

  let { matchId }: { matchId: string } = $props();

  let status = $state<string>('…');
  let busy = $state(false);
  let err = $state<string | null>(null);
  let links = $state<StaffLinks | null>(null);
  let copied = $state<string | null>(null);

  $effect(() => {
    void refreshStatus(matchId);
  });

  async function refreshStatus(id: string) {
    try {
      const m = await getMatchPublic(id);
      status = m.status;
    } catch {
      status = '?';
    }
  }

  async function onStart() {
    busy = true;
    err = null;
    try {
      const res = await startMatch(matchId);
      status = res.match.status;
    } catch (e) {
      err = e instanceof Error ? e.message : String(e);
    } finally {
      busy = false;
    }
  }

  async function onLinks() {
    busy = true;
    err = null;
    try {
      links = await createStaffLinks(matchId);
    } catch (e) {
      err = e instanceof Error ? e.message : String(e);
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
      }, 1500);
    } catch {
      err = 'Не удалось скопировать — скопируйте вручную';
    }
  }
</script>

<div class="ops">
  <div class="row">
    <span class="st">Статус: <strong>{status}</strong></span>
    <button type="button" disabled={busy} onclick={onStart}>Старт (Fake)</button>
    <button type="button" class="ghost" disabled={busy} onclick={onLinks}
      >Ссылки для команды</button
    >
  </div>
  <p class="hint">
    Fake-старт: матч → live без CS2 VPS (для GATE). Live-сервер — отдельно через Bridge.
  </p>
  {#if err}
    <p class="err">{err}</p>
  {/if}
  {#if links}
    <ul class="links">
      <li>
        <span>Режиссёр</span>
        <code>{links.director_url}</code>
        <button type="button" class="ghost" onclick={() => copy('dir', links!.director_url)}
          >{copied === 'dir' ? 'Скопировано' : 'Копировать'}</button
        >
      </li>
      <li>
        <span>Судья</span>
        <code>{links.judge.url}</code>
        <button type="button" class="ghost" onclick={() => copy('judge', links!.judge.url)}
          >{copied === 'judge' ? 'Скопировано' : 'Копировать'}</button
        >
      </li>
      <li>
        <span>Комментатор</span>
        <code>{links.commentator.url}</code>
        <button
          type="button"
          class="ghost"
          onclick={() => copy('watch', links!.commentator.url)}
          >{copied === 'watch' ? 'Скопировано' : 'Копировать'}</button
        >
      </li>
    </ul>
  {/if}
</div>

<style>
  .ops {
    margin-top: 0.65rem;
    padding: 0.65rem 0.75rem;
    border: 1px dashed var(--border);
    border-radius: 4px;
  }
  .row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    align-items: center;
  }
  .st {
    margin-right: 0.35rem;
    font-size: 0.9rem;
    color: var(--muted);
  }
  .hint {
    margin: 0.45rem 0 0;
    font-size: 0.8rem;
    color: var(--muted);
  }
  .err {
    color: var(--danger);
    font-size: 0.85rem;
  }
  .links {
    list-style: none;
    margin: 0.55rem 0 0;
    padding: 0;
  }
  .links li {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    align-items: center;
    padding: 0.35rem 0;
    border-top: 1px solid var(--border);
    font-size: 0.85rem;
  }
  .links span {
    min-width: 6.5rem;
    color: var(--muted);
  }
  .links code {
    flex: 1 1 12rem;
    word-break: break-all;
    font-size: 0.75rem;
  }
  button {
    background: var(--accent);
    color: #0b1210;
    border: none;
    border-radius: 4px;
    padding: 0.35rem 0.65rem;
    font-weight: 600;
    cursor: pointer;
    font-size: 0.85rem;
  }
  button.ghost {
    background: transparent;
    color: var(--muted);
    border: 1px solid var(--border);
    font-weight: 500;
  }
  button:disabled {
    opacity: 0.55;
  }
</style>
