namespace STP.Bridge;

/// <summary>Monotonic sequence per match — CONTRACT §6 / INVARIANTS §6.</summary>
public sealed class SequenceCounter
{
    private int _value;

    public SequenceCounter(int start = 0) => _value = start;

    public int Current => _value;

    public int Next() => Interlocked.Increment(ref _value);

    public void Reset(int value = 0) => Interlocked.Exchange(ref _value, value);
}
