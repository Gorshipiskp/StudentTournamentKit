namespace STK.Bridge;

/// <summary>Monotonic sequence per match — CONTRACT §6 / INVARIANTS §6.
/// Persists to disk so plugin/DS restart does not rewind and break Platform ingest.
/// </summary>
public sealed class SequenceCounter
{
    private readonly string? _persistPath;
    private int _value;

    public SequenceCounter(int start = 0, string? persistPath = null)
    {
        _persistPath = persistPath;
        _value = start;
        if (_persistPath is not null)
            TryLoad();
    }

    public int Current => Volatile.Read(ref _value);

    public int Next()
    {
        var n = Interlocked.Increment(ref _value);
        TrySave(n);
        return n;
    }

    public void Reset(int value = 0)
    {
        Interlocked.Exchange(ref _value, value);
        TrySave(value);
    }

    private void TryLoad()
    {
        try
        {
            if (_persistPath is null || !File.Exists(_persistPath))
                return;
            var text = File.ReadAllText(_persistPath).Trim();
            if (int.TryParse(text, out var n) && n >= 0)
                Interlocked.Exchange(ref _value, n);
        }
        catch
        {
            // keep in-memory start
        }
    }

    private void TrySave(int value)
    {
        if (_persistPath is null)
            return;
        try
        {
            var dir = Path.GetDirectoryName(_persistPath);
            if (!string.IsNullOrEmpty(dir))
                Directory.CreateDirectory(dir);
            File.WriteAllText(_persistPath, value.ToString());
        }
        catch
        {
            // best-effort
        }
    }
}
