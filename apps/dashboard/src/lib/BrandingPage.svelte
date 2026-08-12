<script lang="ts">
  import { onMount } from 'svelte';
  import {
    getBranding,
    getOrganizerToken,
    getTournament,
    setOrganizerToken,
    uploadBranding,
    type BrandingPublic,
    type TournamentPublic,
  } from './api';
  import AdminShell from './AdminShell.svelte';
  import AdminStepper from './AdminStepper.svelte';
  import { humanApiError, toastErr, toastOk } from './toast';

  let { tournamentId }: { tournamentId: string } = $props();

  let tournament = $state<TournamentPublic | null>(null);
  let branding = $state<BrandingPublic | null>(null);
  let primary = $state('#d4a84b');
  let accent = $state('#b45309');
  let logoFile = $state<File | null>(null);
  let logoPreview = $state<string | null>(null);
  let logoInput = $state<HTMLInputElement | null>(null);
  let busy = $state(false);

  let logoSrc = $derived.by(() => {
    if (logoPreview) return logoPreview;
    if (!branding?.has_logo) return null;
    const v = branding.logo_version || '1';
    return `/api/v1/tournaments/${encodeURIComponent(tournamentId)}/branding/logo?v=${encodeURIComponent(v)}`;
  });

  onMount(() => {
    if (!getOrganizerToken()) {
      window.location.href = '/admin';
      return;
    }
    void reload();
  });

  async function reload() {
    try {
      tournament = await getTournament(tournamentId);
      branding = await getBranding(tournamentId);
      if (branding.colors.primary) primary = String(branding.colors.primary);
      if (branding.colors.accent) accent = String(branding.colors.accent);
    } catch (e) {
      const text = e instanceof Error ? e.message : String(e);
      if (text.startsWith('401')) {
        setOrganizerToken(null);
        window.location.href = '/admin';
        return;
      }
      toastErr(humanApiError(text));
    }
  }

  function onFile(e: Event) {
    const input = e.currentTarget as HTMLInputElement;
    const file = input.files?.[0] || null;
    logoFile = file;
    if (logoPreview) URL.revokeObjectURL(logoPreview);
    logoPreview = file ? URL.createObjectURL(file) : null;
  }

  async function onSave(e: Event) {
    e.preventDefault();
    busy = true;
    try {
      branding = await uploadBranding(tournamentId, {
        colors: { primary, accent },
        logo: logoFile,
      });
      logoFile = null;
      if (logoPreview) {
        URL.revokeObjectURL(logoPreview);
        logoPreview = null;
      }
      if (logoInput) logoInput.value = '';
      toastOk('Оформление сохранено — overlay подхватит цвета и лого');
      await reload();
    } catch (err) {
      toastErr(humanApiError(err instanceof Error ? err.message : String(err)));
    } finally {
      busy = false;
    }
  }
</script>

<AdminShell
  title="Оформление"
  subtitle="Необязательно — лого и цвета эфира"
  tournamentName={tournament?.name ?? null}
  {tournamentId}
  current="branding"
>
  {#snippet footer()}
    <a class="btn btn-ghost" href={`/admin/tournaments/${encodeURIComponent(tournamentId)}`}
      >Команды</a
    >
    <a class="btn btn-primary" href={`/admin/tournaments/${encodeURIComponent(tournamentId)}/bracket`}
      >К сетке →</a
    >
  {/snippet}

  <AdminStepper {tournamentId} current="branding" tournamentName={tournament?.name ?? null} />

  <div class="grid">
    <section class="surface">
      <h2 class="display">Логотип и цвета</h2>
      <form class="form" onsubmit={onSave}>
        <label class="field">
          Основной цвет
          <div class="color-row">
            <input type="color" bind:value={primary} />
            <input type="text" bind:value={primary} maxlength="7" />
          </div>
        </label>
        <label class="field">
          Акцент
          <div class="color-row">
            <input type="color" bind:value={accent} />
            <input type="text" bind:value={accent} maxlength="7" />
          </div>
        </label>
        <label class="field">
          Логотип
          <input
            bind:this={logoInput}
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            onchange={onFile}
          />
        </label>
        <button type="submit" class="btn btn-primary" disabled={busy}>
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </button>
      </form>
      <details class="more">
        <summary class="muted">Форматы</summary>
        <p class="hint muted">PNG, JPEG или WebP до 2 МБ.</p>
      </details>
    </section>

    <section class="surface preview-card">
      <h2 class="display">Превью</h2>
      <div class="preview" style={`--p:${primary};--a:${accent}`}>
        <div class="bar"></div>
        <div class="body">
          {#if logoSrc}
            <img src={logoSrc} alt="Логотип турнира" />
          {:else}
            <span class="muted">Лого пока нет</span>
          {/if}
          <p class="sample">{tournament?.name || 'Название турнира'}</p>
        </div>
      </div>
    </section>
  </div>
</AdminShell>

<style>
  .grid {
    display: grid;
    gap: 1rem;
  }
  @media (min-width: 800px) {
    .grid {
      grid-template-columns: 1.1fr 0.9fr;
      align-items: start;
    }
  }
  h2 {
    margin: 0 0 0.55rem;
    font-size: 1.15rem;
  }
  .more {
    margin-top: 0.85rem;
  }
  .more summary {
    cursor: pointer;
    font-size: 0.88rem;
  }
  .hint {
    margin: 0.45rem 0 0;
    font-size: 0.88rem;
  }
  .form {
    display: flex;
    flex-direction: column;
    gap: 0.9rem;
  }
  .color-row {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  .color-row input[type='color'] {
    width: 3rem;
    height: var(--touch);
    padding: 0.2rem;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--bg-elevated);
  }
  .color-row input[type='text'] {
    flex: 1;
  }
  .preview {
    border-radius: var(--radius);
    overflow: hidden;
    border: 1px solid var(--border);
    background: #111827;
    color: #f8fafc;
    min-height: 12rem;
  }
  .bar {
    height: 8px;
    background: linear-gradient(90deg, var(--p), var(--a));
  }
  .body {
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }
  .body img {
    max-height: 64px;
    max-width: 160px;
    object-fit: contain;
  }
  .sample {
    margin: 0;
    font-weight: 650;
    color: var(--p);
  }
</style>
