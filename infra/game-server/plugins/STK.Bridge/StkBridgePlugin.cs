using CounterStrikeSharp.API.Core;
using Microsoft.Extensions.Logging;

namespace STK.Bridge;

/// <summary>
/// STK.Bridge — thin CounterStrikeSharp layer over MatchZy (ADR-023 / F1).
/// Skeleton: config, webhook client, sequence, heartbeat + command listener stubs.
/// Do NOT invent MatchZy hook signatures here — wire after recon on VPS.
/// </summary>
public sealed class StkBridgePlugin : BasePlugin
{
    public override string ModuleName => "STK.Bridge";
    public override string ModuleVersion => "0.1.0";
    public override string ModuleAuthor => "StudentTournamentKit";
    public override string ModuleDescription =>
        "Platform bridge: normalized webhooks, commands, heartbeat (CONTRACT protocol_version=1)";

    private StkBridgeConfig _config = new();
    private SequenceCounter _sequence = new();
    private WebhookClient? _webhooks;
    private HeartbeatService? _heartbeat;
    private CommandListener? _commands;
    private CancellationTokenSource? _heartbeatCts;

    public override void Load(bool hotReload)
    {
        _config = LoadConfig();
        _sequence = new SequenceCounter();
        _webhooks = new WebhookClient(_config, _sequence);
        _heartbeat = new HeartbeatService(_webhooks, _config);
        _commands = new CommandListener(_config, _sequence);

        Logger.LogInformation(
            "STK.Bridge loading match_id={MatchId} server_id={ServerId} platform={Platform} protocol={Protocol}",
            _config.MatchId,
            _config.ServerId,
            _config.PlatformUrl,
            _config.ProtocolVersion);

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

        _heartbeatCts = new CancellationTokenSource();
        _ = RunHeartbeatLoopAsync(_heartbeatCts.Token);

        // TODO (post-skeleton): register CSS/MatchZy listeners for round_start/round_end/etc.
        // Docs: https://docs.cssharp.dev/ — do not invent event APIs in this prompt.
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
