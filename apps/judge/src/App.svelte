<script lang="ts">
  import { onMount } from 'svelte';
  import {
    humanApiError,
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
        'Нет ссылки-приглашения. Откройте URL, который прислал организатор (с параметром ?token=…).';
      loading = false;
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const redeemed = await redeemInvite(token);
        if (cancelled) return;
        if (redeemed.role !== 'judge') {
          bootError = 'Эта ссылка не для судьи. Попросите у организатора ссылку судьи.';
          loading = false;
          return;
        }
        if (!redeemed.caps.includes('judge.review')) {
          bootError = 'У приглашения нет прав судьи. Нужна новая ссылка от организатора.';
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
        bootError = humanApiError(
          e instanceof Error ? e.message : 'Не удалось войти по приглашению',
        );
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
    <span class="mark">STK</span>
    <h1 class="display">Судья</h1>
    <p class="muted">Входим по приглашению…</p>
    <div class="bar" aria-hidden="true"></div>
  </main>
{:else if bootError}
  <main class="boot deny">
    <span class="mark warn">!</span>
    <h1 class="display">Доступ закрыт</h1>
    <p class="muted">{bootError}</p>
    <p class="tip muted">
      Не пересылайте ссылку зрителям. Если протухла — попросите организатора выдать новую из
      «Ссылки для команды».
    </p>
  </main>
{:else if session}
  <JudgePage {session} />
{/if}

<style>
  .boot {
    max-width: 26rem;
    margin: 0 auto;
    padding: 3.5rem 1.35rem 2rem;
    text-align: center;
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  .mark {
    display: inline-grid;
    place-items: center;
    width: 3rem;
    height: 3rem;
    margin-bottom: 1rem;
    border-radius: var(--radius);
    background: var(--cta);
    color: var(--cta-text);
    font-weight: 800;
  }
  .mark.warn {
    background: var(--danger);
    font-size: 1.4rem;
  }
  h1 {
    margin: 0 0 0.65rem;
    font-size: 1.75rem;
  }
  p {
    margin: 0;
    line-height: 1.45;
    max-width: 22rem;
  }
  .tip {
    margin-top: 1.25rem;
    font-size: 0.9rem;
  }
  .bar {
    margin-top: 1.5rem;
    width: 8rem;
    height: 4px;
    border-radius: var(--radius-sm);
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    background-size: 200% 100%;
    animation: slide 1.1s linear infinite;
  }
  @keyframes slide {
    from {
      background-position: 100% 0;
    }
    to {
      background-position: -100% 0;
    }
  }
</style>
