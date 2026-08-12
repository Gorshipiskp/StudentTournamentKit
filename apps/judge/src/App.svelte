<script lang="ts">
  import { onMount } from 'svelte';
  import {
    redeemInvite,
    resolveInviteToken,
    type JudgeSession,
  } from './lib/api';
  import JudgePage from './lib/JudgePage.svelte';

  let session = $state<JudgeSession | null>(null);
  let bootError = $state<string | null>(null);
  let loading = $state(true);

  onMount(() => {
    const token = resolveInviteToken(window.location.search);
    if (!token) {
      bootError =
        'Нет ссылки-приглашения. Откройте URL с параметром ?token=…';
      loading = false;
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const redeemed = await redeemInvite(token);
        if (cancelled) return;
        if (redeemed.role !== 'judge') {
          bootError = 'Эта ссылка не для судьи.';
          loading = false;
          return;
        }
        if (!redeemed.caps.includes('judge.review')) {
          bootError = 'У приглашения нет прав судьи.';
          loading = false;
          return;
        }
        session = {
          accessToken: redeemed.access_token,
          matchId: redeemed.match_id,
          role: redeemed.role,
          caps: redeemed.caps,
        };
        loading = false;
      } catch (e) {
        if (cancelled) return;
        bootError =
          e instanceof Error ? e.message : 'Не удалось войти по приглашению';
        loading = false;
      }
    })();

    return () => {
      cancelled = true;
    };
  });
</script>

{#if loading}
  <main class="boot">
    <p>Вход по приглашению…</p>
  </main>
{:else if bootError}
  <main class="boot deny">
    <h1>Доступ закрыт</h1>
    <p>{bootError}</p>
  </main>
{:else if session}
  <JudgePage {session} />
{/if}

<style>
  .boot {
    max-width: 28rem;
    margin: 0 auto;
    padding: 3rem 1.25rem;
    text-align: center;
  }
  .deny h1 {
    font-size: 1.5rem;
    margin: 0 0 0.75rem;
  }
  .deny p {
    color: var(--muted);
    line-height: 1.45;
  }
</style>
