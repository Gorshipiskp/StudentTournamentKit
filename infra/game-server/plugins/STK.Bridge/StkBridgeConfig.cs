namespace STK.Bridge;

/// <summary>
/// Runtime config — mirrors Fake + CONTRACT (infra/game-server/CONTRACT.md).
/// Loaded from config.json next to the plugin DLL (or CSS config hook later).
/// </summary>
public sealed class StkBridgeConfig
{
    public string PlatformUrl { get; set; } = "http://127.0.0.1:8000";
    public string WebhookSecret { get; set; } = "change_me";
    public string MatchId { get; set; } = "m_dev";
    public string ServerId { get; set; } = "srv_dev";
    public string ProtocolVersion { get; set; } = "1";
    public string BridgeVersion { get; set; } = "0.1.0";
    public int HeartbeatIntervalSeconds { get; set; } = 15;
    public string CommandListenHost { get; set; } = "0.0.0.0";
    public int CommandListenPort { get; set; } = 27099;
    public string EventsPath { get; set; } = "/api/v1/internal/cs2/events";

    public string EventsUrl =>
        PlatformUrl.TrimEnd('/') + (EventsPath.StartsWith('/') ? EventsPath : "/" + EventsPath);
}
