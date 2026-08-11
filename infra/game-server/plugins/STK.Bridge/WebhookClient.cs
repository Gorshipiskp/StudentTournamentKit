using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace STK.Bridge;

/// <summary>
/// POST normalized events to Platform with HMAC (CONTRACT §2–3).
/// Stub: no MatchZy hooks wired yet — call EmitAsync from future event adapters.
/// </summary>
public sealed class WebhookClient
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        WriteIndented = false,
    };

    private readonly StkBridgeConfig _config;
    private readonly SequenceCounter _sequence;
    private readonly HttpClient _http;

    public WebhookClient(StkBridgeConfig config, SequenceCounter sequence, HttpClient? http = null)
    {
        _config = config;
        _sequence = sequence;
        _http = http ?? new HttpClient { Timeout = TimeSpan.FromSeconds(5) };
    }

    public async Task<bool> EmitAsync(
        string type,
        object payload,
        string? correlationId = null,
        CancellationToken ct = default)
    {
        var evt = new Dictionary<string, object?>
        {
            ["event_id"] = Guid.NewGuid().ToString(),
            ["sequence"] = _sequence.Next(),
            ["server_id"] = _config.ServerId,
            ["match_id"] = _config.MatchId,
            ["type"] = type,
            ["timestamp"] = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ"),
            ["correlation_id"] = correlationId,
            ["payload"] = payload,
        };

        var raw = JsonSerializer.SerializeToUtf8Bytes(evt, JsonOptions);
        var signature = SignBody(_config.WebhookSecret, raw);

        using var req = new HttpRequestMessage(HttpMethod.Post, _config.EventsUrl);
        req.Content = new ByteArrayContent(raw);
        req.Content.Headers.TryAddWithoutValidation("Content-Type", "application/json");
        req.Headers.TryAddWithoutValidation("X-STK-Signature", signature);
        req.Headers.TryAddWithoutValidation("X-STK-Event-Id", evt["event_id"]!.ToString());
        req.Headers.TryAddWithoutValidation("X-STK-Protocol-Version", _config.ProtocolVersion);

        try
        {
            using var resp = await _http.SendAsync(req, ct).ConfigureAwait(false);
            // Platform returns 200 even for duplicate; non-2xx = transport problem
            return resp.IsSuccessStatusCode;
        }
        catch (Exception)
        {
            // Best-effort (A1): game continues if Platform is down
            return false;
        }
    }

    public static string SignBody(string secret, byte[] rawBody)
    {
        var key = Encoding.UTF8.GetBytes(secret);
        var hash = HMACSHA256.HashData(key, rawBody);
        return "sha256=" + Convert.ToHexString(hash).ToLowerInvariant();
    }
}
