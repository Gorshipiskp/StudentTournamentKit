<script lang="ts">
  let {
    value,
    tone = 'default',
  }: {
    value: number;
    tone?: 'default' | 'a' | 'b';
  } = $props();
</script>

{#key value}
  <span class="flash tone-{tone}">{value}</span>
{/key}

<style>
  .flash {
    display: inline-block;
    font: inherit;
    color: inherit;
    font-variant-numeric: tabular-nums;
    animation: score-slam 0.55s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .tone-a {
    color: #8ec4f0;
  }

  .tone-b {
    color: #f0a86a;
  }

  @keyframes score-slam {
    0% {
      opacity: 0.35;
      transform: scale(1.35);
      filter: blur(3px);
      text-shadow: 0 0 0 transparent;
    }
    55% {
      filter: blur(0);
    }
    100% {
      opacity: 1;
      transform: scale(1);
      filter: blur(0);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .flash {
      animation: none !important;
    }
  }
</style>
