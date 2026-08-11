namespace STP.Bridge;

/// <summary>
/// Periodic heartbeat event stub (CONTRACT type=heartbeat).
/// Full timer wiring happens in StpBridgePlugin.OnAllPluginsLoaded.
/// </summary>
public sealed class HeartbeatService
{
    private readonly WebhookClient _webhooks;
    private readonly StpBridgeConfig _config;

    public HeartbeatService(WebhookClient webhooks, StpBridgeConfig config)
    {
        _webhooks = webhooks;
        _config = config;
    }

    public Task SendOnceAsync(CancellationToken ct = default) =>
        _webhooks.EmitAsync(
            "heartbeat",
            new
            {
                bridge_version = _config.BridgeVersion,
                protocol_version = _config.ProtocolVersion,
            },
            ct: ct);
}
