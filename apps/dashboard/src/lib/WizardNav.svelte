<script lang="ts">
  /** @deprecated use AdminStepper — kept as thin re-export for any stale imports */
  import AdminStepper from './AdminStepper.svelte';

  let {
    tournamentId = null,
    current = 'list',
  }: {
    tournamentId?: string | null;
    current: 'list' | 'teams' | 'bracket' | 'branding';
  } = $props();
</script>

<AdminStepper {tournamentId} {current} />
