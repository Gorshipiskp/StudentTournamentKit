namespace STK.Bridge;

/// <summary>
/// In-memory match view for webhooks + snapshot (CONTRACT §3 / §5).
/// Mapping: team_a = CT, team_b = T (documented; MatchZy team1/team2 not used in domain).
/// Round is observed from the game (not a forever-incrementing counter).
/// </summary>
public sealed class MatchLiveState
{
    private readonly object _gate = new();

    public int Round { get; private set; }
    public int ScoreTeamA { get; private set; }
    public int ScoreTeamB { get; private set; }
    public string Phase { get; private set; } = "warmup";
    public string? Map { get; private set; }
    public bool Loaded { get; private set; }
    public bool Paused { get; private set; }
    public bool Completed { get; private set; }
    public string? WinnerSide { get; private set; }

    public void Observe(
        int round,
        int scoreA,
        int scoreB,
        string phase,
        string? map,
        string? winnerSide = null)
    {
        lock (_gate)
        {
            Round = Math.Max(0, round);
            ScoreTeamA = scoreA;
            ScoreTeamB = scoreB;
            Phase = string.IsNullOrWhiteSpace(phase) ? Phase : phase;
            if (!string.IsNullOrWhiteSpace(map))
                Map = map;
            if (winnerSide is not null)
                WinnerSide = winnerSide;
            Loaded = true;
        }
    }

    public object Snapshot(string matchId, string serverId, int lastSequence)
    {
        lock (_gate)
        {
            return new
            {
                match_id = matchId,
                server_id = serverId,
                map = Map,
                round = Round,
                score = new { team_a = ScoreTeamA, team_b = ScoreTeamB },
                phase = Phase,
                paused = Paused,
                loaded = Loaded,
                completed = Completed,
                last_sequence = lastSequence,
                players = Array.Empty<object>(),
            };
        }
    }

    public object RoundStartPayload()
    {
        lock (_gate)
        {
            return new { round = Round, phase = Phase };
        }
    }

    public object RoundEndPayload()
    {
        lock (_gate)
        {
            return new
            {
                round = Round,
                score = new { team_a = ScoreTeamA, team_b = ScoreTeamB },
                map = Map,
                winner = WinnerSide,
            };
        }
    }

    public static object BombPlantedPayload(int site, int timerSec = 40) =>
        new { site, timer_sec = timerSec };

    public static object BombDefuseStartPayload(bool hasKit) =>
        new { has_kit = hasKit };

    public static object BombSitePayload(int site) =>
        new { site };
}
