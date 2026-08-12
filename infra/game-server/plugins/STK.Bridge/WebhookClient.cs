using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.Logging;

namespace STK.Bridge;

/// <summary>
/// POST normalized events to Platform with HMAC (CONTRACT §2–3).
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
    private readonly ILogger? _logger;

    public WebhookClient(
        StkBridgeConfig config,
        SequenceCounter sequence,
        ILogger? logger = null,
        HttpClient? http = null)
    {
        _config = config;
        _sequence = sequence;
        _logger = logger;
        _http = http ?? new HttpClient { Timeout = TimeSpan.FromSeconds(5) };
    }

    public async Task<bool> EmitAsync(
        string type,
        object payload,
        string? correlationId = null,
        CancellationToken ct = default)
    {
        var eventId = Guid.NewGuid().ToString();
        var sequence = _sequence.Next();
        var evt = new Dictionary<string, object?>
        {
            ["event_id"] = eventId,
            ["sequence"] = sequence,
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
        req.Headers.TryAddWithoutValidation("X-STK-Event-Id", eventId);
        req.Headers.TryAddWithoutValidation("X-STK-Protocol-Version", _config.ProtocolVersion);

        try
        {
            using var resp = await _http.SendAsync(req, ct).ConfigureAwait(false);
            if (resp.IsSuccessStatusCode)
            {
                _logger?.LogDebug(
                    "webhook ok type={Type} sequence={Sequence} status={Status}",
                    type,
                    sequence,
                    (int)resp.StatusCode);
                return true;
            }

            var bodyPreview = "";
            try
            {
                bodyPreview = await resp.Content.ReadAsStringAsync(ct).ConfigureAwait(false);
                if (bodyPreview.Length > 200)
                    bodyPreview = bodyPreview[..200];
            }
            catch
            {
                // ignore
            }

            // Do not log webhook secret. 401/403 often = wrong secret on Platform.
            _logger?.LogWarning(
                "webhook failed type={Type} sequence={Sequence} url={Url} status={Status} body={Body}",
                type,
                sequence,
                _config.EventsUrl,
                (int)resp.StatusCode,
                bodyPreview);
            return false;
        }
        catch (Exception ex)
        {
            // Best-effort (A1): game continues if Platform is down
            _logger?.LogWarning(
                ex,
                "webhook transport error type={Type} sequence={Sequence} url={Url}",
                type,
                sequence,
                _config.EventsUrl);
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
