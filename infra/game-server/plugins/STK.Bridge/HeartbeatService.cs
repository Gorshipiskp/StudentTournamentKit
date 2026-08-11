namespace STK.Bridge;

/// <summary>
/// Periodic heartbeat event stub (CONTRACT type=heartbeat).
/// Full timer wiring happens in StkBridgePlugin.OnAllPluginsLoaded.
/// </summary>
public sealed class HeartbeatService
{
    private readonly WebhookClient _webhooks;
    private readonly StkBridgeConfig _config;

    public HeartbeatService(WebhookClient webhooks, StkBridgeConfig config)
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
