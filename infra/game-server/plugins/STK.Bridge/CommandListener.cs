using System.Net;
using System.Text;
using System.Text.Json;

namespace STK.Bridge;

/// <summary>
/// HTTP command listener stub — CONTRACT §4 (POST /v1/commands).
/// Whitelist: LoadMatch, PauseMatch, ResumeMatch, ForfeitMatch, GetSnapshot.
/// Real CS2 side-effects (mp_pause_match / MatchZy) — TODO, not invented here.
/// </summary>
public sealed class CommandListener : IAsyncDisposable
{
    private static readonly HashSet<string> Allowed = new(StringComparer.Ordinal)
    {
        "LoadMatch",
        "PauseMatch",
        "ResumeMatch",
        "ForfeitMatch",
        "GetSnapshot",
    };

    private readonly StkBridgeConfig _config;
    private readonly SequenceCounter _sequence;
    private readonly Dictionary<string, JsonElement> _acks = new();
    private HttpListener? _listener;
    private CancellationTokenSource? _cts;
    private Task? _loop;

    public CommandListener(StkBridgeConfig config, SequenceCounter sequence)
    {
        _config = config;
        _sequence = sequence;
    }

    public void Start()
    {
        if (_listener is not null)
            return;

        var host = string.IsNullOrWhiteSpace(_config.CommandListenHost) ? "127.0.0.1" : _config.CommandListenHost.Trim();
        // HttpListener on Windows: 0.0.0.0/+ needs URL ACL; 127.0.0.1 works for local Platform.
        if (host is "0.0.0.0" or "+" or "*")
            host = "127.0.0.1";
        var prefix = $"http://{host}:{_config.CommandListenPort}/";
        _listener = new HttpListener();
        _listener.Prefixes.Add(prefix);
        _listener.Start();
        _cts = new CancellationTokenSource();
        _loop = Task.Run(() => AcceptLoopAsync(_cts.Token));
    }

    public async ValueTask DisposeAsync()
    {
        if (_cts is not null)
        {
            await _cts.CancelAsync().ConfigureAwait(false);
            _cts.Dispose();
        }

        _listener?.Stop();
        _listener?.Close();
        if (_loop is not null)
        {
            try { await _loop.ConfigureAwait(false); }
            catch (OperationCanceledException) { }
        }
    }

    private async Task AcceptLoopAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested && _listener is { IsListening: true })
        {
            HttpListenerContext ctx;
            try
            {
                ctx = await _listener.GetContextAsync().WaitAsync(ct).ConfigureAwait(false);
            }
            catch (Exception)
            {
                break;
            }

            _ = Task.Run(() => HandleAsync(ctx), ct);
        }
    }

    private async Task HandleAsync(HttpListenerContext ctx)
    {
        var path = ctx.Request.Url?.AbsolutePath.TrimEnd('/') ?? "";
        try
        {
            if (ctx.Request.HttpMethod == "GET" && path is "/health" or "")
            {
                await WriteJsonAsync(ctx.Response, 200, new
                {
                    status = "ok",
                    role = "stk-bridge",
                    protocol_version = _config.ProtocolVersion,
                    bridge_version = _config.BridgeVersion,
                    match_id = _config.MatchId,
                    server_id = _config.ServerId,
                    last_sequence = _sequence.Current,
                }).ConfigureAwait(false);
                return;
            }

            if (ctx.Request.HttpMethod == "GET" && path == "/v1/snapshot")
            {
                await WriteJsonAsync(ctx.Response, 200, BuildStubSnapshot()).ConfigureAwait(false);
                return;
            }

            if (ctx.Request.HttpMethod == "POST" && path == "/v1/commands")
            {
                using var reader = new StreamReader(ctx.Request.InputStream, ctx.Request.ContentEncoding);
                var body = await reader.ReadToEndAsync().ConfigureAwait(false);
                using var doc = JsonDocument.Parse(string.IsNullOrWhiteSpace(body) ? "{}" : body);
                var root = doc.RootElement;
                var commandId = root.TryGetProperty("command_id", out var cidEl)
                    ? cidEl.GetString()
                    : null;
                var type = root.TryGetProperty("type", out var typeEl) ? typeEl.GetString() : null;

                if (string.IsNullOrEmpty(commandId) || string.IsNullOrEmpty(type))
                {
                    await WriteJsonAsync(ctx.Response, 400, new { error = "command_id and type required" })
                        .ConfigureAwait(false);
                    return;
                }

                if (!Allowed.Contains(type))
                {
                    await WriteJsonAsync(ctx.Response, 400, new { error = "unknown_type", allowed = Allowed.ToArray() })
                        .ConfigureAwait(false);
                    return;
                }

                if (_acks.TryGetValue(commandId, out var prev))
                {
                    await WriteJsonAsync(ctx.Response, 200, new
                    {
                        command_id = commandId,
                        type,
                        status = "duplicate",
                        timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ"),
                        error = (string?)null,
                        result = prev,
                    }).ConfigureAwait(false);
                    return;
                }

                // Stub apply: no RCON / MatchZy yet — ack confirmed for GetSnapshot/shape tests
                object? result = type == "GetSnapshot"
                    ? new { snapshot = BuildStubSnapshot() }
                    : new { stub = true, applied = false, note = "CS2 side-effect not wired (skeleton)" };

                var resultJson = JsonSerializer.SerializeToElement(result);
                _acks[commandId] = resultJson;

                await WriteJsonAsync(ctx.Response, 200, new
                {
                    command_id = commandId,
                    type,
                    status = "confirmed",
                    timestamp = DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ"),
                    error = (string?)null,
                    result,
                }).ConfigureAwait(false);
                return;
            }

            await WriteJsonAsync(ctx.Response, 404, new { error = "not_found", path }).ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            try
            {
                await WriteJsonAsync(ctx.Response, 500, new { error = ex.Message }).ConfigureAwait(false);
            }
            catch
            {
                // ignore
            }
        }
    }

    private object BuildStubSnapshot() => new
    {
        match_id = _config.MatchId,
        server_id = _config.ServerId,
        map = (string?)null,
        round = 0,
        score = new { team_a = 0, team_b = 0 },
        phase = "warmup",
        paused = false,
        loaded = false,
        completed = false,
        last_sequence = _sequence.Current,
        players = Array.Empty<object>(),
    };

    private static async Task WriteJsonAsync(HttpListenerResponse response, int code, object payload)
    {
        var bytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(payload));
        response.StatusCode = code;
        response.ContentType = "application/json";
        response.ContentLength64 = bytes.Length;
        await response.OutputStream.WriteAsync(bytes).ConfigureAwait(false);
        response.OutputStream.Close();
    }
}
