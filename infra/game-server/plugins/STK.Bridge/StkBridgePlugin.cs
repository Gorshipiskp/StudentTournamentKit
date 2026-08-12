using CounterStrikeSharp.API.Core;
using Microsoft.Extensions.Logging;

namespace STK.Bridge;

/// <summary>
/// STK.Bridge — thin CounterStrikeSharp layer (ADR-023 / F1).
/// CSS game events → CONTRACT webhooks. Docs: https://docs.cssharp.dev/docs/features/game-events.html
/// </summary>
public sealed class StkBridgePlugin : BasePlugin
{
    public override string ModuleName => "STK.Bridge";
    public override string ModuleVersion => "0.3.3";
    public override string ModuleAuthor => "StudentTournamentKit";
    public override string ModuleDescription =>
        "Platform bridge: normalized webhooks, commands, heartbeat (CONTRACT protocol_version=1)";

    private StkBridgeConfig _config = new();
    private SequenceCounter _sequence = new();
    private MatchLiveState _live = new();
    private WebhookClient? _webhooks;
    private HeartbeatService? _heartbeat;
    private CommandListener? _commands;
    private CancellationTokenSource? _heartbeatCts;

    public override void Load(bool hotReload)
    {
        _config = LoadConfig();
        var seqPath = Path.Combine(ModuleDirectory, "sequence.txt");
        _sequence = new SequenceCounter(persistPath: seqPath);
        _live = new MatchLiveState();
        _webhooks = new WebhookClient(_config, _sequence, Logger);
        _heartbeat = new HeartbeatService(_webhooks, _config);
        _commands = new CommandListener(_config, _sequence, _live);

        Logger.LogInformation(
            "STK.Bridge loading match_id={MatchId} server_id={ServerId} platform={Platform} protocol={Protocol} version={Version} last_sequence={Seq}",
            _config.MatchId,
            _config.ServerId,
            _config.PlatformUrl,
            _config.ProtocolVersion,
            ModuleVersion,
            _sequence.Current);

        try
        {
            _commands.Start();
            Logger.LogInformation(
                "Command listener on {Host}:{Port} (POST /v1/commands)",
                _config.CommandListenHost,
                _config.CommandListenPort);
        }
        catch (Exception ex)
        {
            Logger.LogWarning(ex, "Command listener failed to start (firewall / URL ACL?). Stub continues.");
        }

        // CSS game events — https://docs.cssharp.dev/examples/WithGameEventHandlers.html
        RegisterEventHandler<EventRoundStart>(OnRoundStart);
        RegisterEventHandler<EventRoundEnd>(OnRoundEnd);
        RegisterEventHandler<EventBombPlanted>(OnBombPlanted);
        RegisterEventHandler<EventBombBegindefuse>(OnBombBeginDefuse);
        RegisterEventHandler<EventBombDefused>(OnBombDefused);
        RegisterEventHandler<EventBombExploded>(OnBombExploded);
        Logger.LogInformation(
            "Registered CSS handlers: RoundStart/End, BombPlanted/Begindefuse/Defused/Exploded");

        _heartbeatCts = new CancellationTokenSource();
        _ = RunHeartbeatLoopAsync(_heartbeatCts.Token);
    }

    public override void Unload(bool hotReload)
    {
        _heartbeatCts?.Cancel();
        _heartbeatCts?.Dispose();
        if (_commands is not null)
        {
            _commands.DisposeAsync().AsTask().GetAwaiter().GetResult();
        }

        Logger.LogInformation("STK.Bridge unloaded");
    }

    private HookResult OnRoundStart(EventRoundStart @event, GameEventInfo info)
    {
        try
        {
            var (scoreA, scoreB) = GameScoreReader.ReadCtTScores();
            var map = GameScoreReader.CurrentMap();
            var warmup = GameScoreReader.IsWarmup();
            var phase = warmup ? "warmup" : GameScoreReader.DisplayPhase();
            var round = GameScoreReader.DisplayRound(scoreA, scoreB);
            _live.Observe(round, scoreA, scoreB, phase, map);

            // Only skip spammy warmup RoundStart. Never block live rounds.
            if (warmup)
            {
                Logger.LogDebug("skip round_start webhook (warmup)");
                return HookResult.Continue;
            }

            var payload = _live.RoundStartPayload();
            Logger.LogInformation("emit round_start round={Round} phase={Phase}", round, phase);
            _ = EmitFireAndForgetAsync("round_start", payload);
        }
        catch (Exception ex)
        {
            Logger.LogWarning(ex, "round_start handler failed");
        }

        return HookResult.Continue;
    }

    private HookResult OnRoundEnd(EventRoundEnd @event, GameEventInfo info)
    {
        try
        {
            var (scoreA, scoreB) = GameScoreReader.ReadCtTScores();
            var map = GameScoreReader.CurrentMap();
            // CSS Winner: 2=CT, 3=T (team_a=CT, team_b=T)
            string? winnerSide = @event.Winner switch
            {
                2 => "team_a",
                3 => "team_b",
                _ => null,
            };

            // Always emit round_end (score + overlay FX). Warmup only zeros the round number.
            var warmup = GameScoreReader.IsWarmup();
            var phase = warmup ? "warmup" : GameScoreReader.DisplayPhase(atRoundEnd: true);
            var round = GameScoreReader.DisplayRound(scoreA, scoreB, atRoundEnd: true);
            _live.Observe(round, scoreA, scoreB, phase, map, winnerSide);

            var payload = _live.RoundEndPayload();
            Logger.LogInformation(
                "emit round_end round={Round} score_a={A} score_b={B} winner={Winner} warmup={Warmup}",
                round,
                scoreA,
                scoreB,
                winnerSide ?? @event.Winner.ToString(),
                warmup);
            _ = EmitFireAndForgetAsync("round_end", payload);
        }
        catch (Exception ex)
        {
            Logger.LogWarning(ex, "round_end handler failed");
        }

        return HookResult.Continue;
    }

    private HookResult OnBombPlanted(EventBombPlanted @event, GameEventInfo info)
    {
        try
        {
            var site = @event.Site;
            var payload = MatchLiveState.BombPlantedPayload(site);
            Logger.LogInformation("emit bomb_planted site={Site}", site);
            _ = EmitFireAndForgetAsync("bomb_planted", payload);
        }
        catch (Exception ex)
        {
            Logger.LogWarning(ex, "bomb_planted handler failed");
        }

        return HookResult.Continue;
    }

    private HookResult OnBombBeginDefuse(EventBombBegindefuse @event, GameEventInfo info)
    {
        try
        {
            var payload = MatchLiveState.BombDefuseStartPayload(@event.Haskit);
            Logger.LogInformation("emit bomb_defuse_start has_kit={Kit}", @event.Haskit);
            _ = EmitFireAndForgetAsync("bomb_defuse_start", payload);
        }
        catch (Exception ex)
        {
            Logger.LogWarning(ex, "bomb_defuse_start handler failed");
        }

        return HookResult.Continue;
    }

    private HookResult OnBombDefused(EventBombDefused @event, GameEventInfo info)
    {
        try
        {
            var payload = MatchLiveState.BombSitePayload(@event.Site);
            Logger.LogInformation("emit bomb_defused site={Site}", @event.Site);
            _ = EmitFireAndForgetAsync("bomb_defused", payload);
        }
        catch (Exception ex)
        {
            Logger.LogWarning(ex, "bomb_defused handler failed");
        }

        return HookResult.Continue;
    }

    private HookResult OnBombExploded(EventBombExploded @event, GameEventInfo info)
    {
        try
        {
            var payload = MatchLiveState.BombSitePayload(@event.Site);
            Logger.LogInformation("emit bomb_exploded site={Site}", @event.Site);
            _ = EmitFireAndForgetAsync("bomb_exploded", payload);
        }
        catch (Exception ex)
        {
            Logger.LogWarning(ex, "bomb_exploded handler failed");
        }

        return HookResult.Continue;
    }

    private async Task EmitFireAndForgetAsync(string type, object payload)
    {
        if (_webhooks is null)
            return;
        try
        {
            await _webhooks.EmitAsync(type, payload).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            Logger.LogDebug(ex, "emit {Type} swallowed", type);
        }
    }

    private async Task RunHeartbeatLoopAsync(CancellationToken ct)
    {
        var delay = TimeSpan.FromSeconds(Math.Max(5, _config.HeartbeatIntervalSeconds));
        while (!ct.IsCancellationRequested)
        {
            try
            {
                if (_heartbeat is not null)
                    await _heartbeat.SendOnceAsync(ct).ConfigureAwait(false);
            }
            catch (OperationCanceledException) when (ct.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                Logger.LogDebug(ex, "heartbeat emit failed (best-effort)");
            }

            try
            {
                await Task.Delay(delay, ct).ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                break;
            }
        }
    }

    private StkBridgeConfig LoadConfig()
    {
        try
        {
            var path = Path.Combine(ModuleDirectory, "config.json");
            if (!File.Exists(path))
            {
                Logger.LogWarning("config.json not found at {Path}; using defaults", path);
                return new StkBridgeConfig();
            }

            var json = File.ReadAllText(path);
            var cfg = System.Text.Json.JsonSerializer.Deserialize<StkBridgeConfig>(json);
            return cfg ?? new StkBridgeConfig();
        }
        catch (Exception ex)
        {
            Logger.LogWarning(ex, "Failed to load config.json; using defaults");
            return new StkBridgeConfig();
        }
    }
}
