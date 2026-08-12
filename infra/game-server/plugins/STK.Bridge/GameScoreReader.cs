using CounterStrikeSharp.API;
using CounterStrikeSharp.API.Core;
using CounterStrikeSharp.API.Modules.Utils;

namespace STK.Bridge;

/// <summary>
/// Read CT/T scores + warmup/round from CSS game entities.
/// GameRules access is fail-open: never break round_* webhooks.
/// </summary>
public static class GameScoreReader
{
    /// <summary>
    /// Returns (team_a=CT, team_b=T). Missing team → 0.
    /// </summary>
    public static (int TeamA, int TeamB) ReadCtTScores()
    {
        var teamA = 0;
        var teamB = 0;

        try
        {
            foreach (var team in Utilities.FindAllEntitiesByDesignerName<CCSTeam>("cs_team_manager"))
            {
                if (team is null || !team.IsValid)
                    continue;

                var side = (CsTeam)team.TeamNum;
                if (side == CsTeam.CounterTerrorist)
                    teamA = team.Score;
                else if (side == CsTeam.Terrorist)
                    teamB = team.Score;
            }
        }
        catch
        {
            // keep zeros
        }

        return (teamA, teamB);
    }

    public static string? CurrentMap()
    {
        try
        {
            var name = Server.MapName;
            return string.IsNullOrWhiteSpace(name) ? null : name;
        }
        catch
        {
            return null;
        }
    }

    public static CCSGameRules? TryGameRules()
    {
        try
        {
            foreach (var proxy in Utilities.FindAllEntitiesByDesignerName<CCSGameRulesProxy>("cs_gamerules"))
            {
                if (proxy is null || !proxy.IsValid)
                    continue;
                var rules = proxy.GameRules;
                if (rules is not null)
                    return rules;
            }
        }
        catch
        {
            // entity not ready / schema mismatch
        }

        return null;
    }

    /// <summary>True only when GameRules explicitly reports warmup. Errors → false.</summary>
    public static bool IsWarmup()
    {
        try
        {
            return TryGameRules()?.WarmupPeriod == true;
        }
        catch
        {
            return false;
        }
    }

    /// <summary>
    /// Display round: 0 in warmup; otherwise score-based (stable without GameRules).
    /// </summary>
    public static int DisplayRound(int scoreA, int scoreB, bool atRoundEnd = false)
    {
        if (IsWarmup())
            return 0;

        try
        {
            var rules = TryGameRules();
            if (rules is not null)
            {
                var completed = rules.TotalRoundsPlayed;
                if (atRoundEnd)
                    return Math.Max(completed, scoreA + scoreB);
                return Math.Max(completed + 1, scoreA + scoreB + 1);
            }
        }
        catch
        {
            // fall through to score-based
        }

        if (atRoundEnd)
            return Math.Max(0, scoreA + scoreB);
        return Math.Max(1, scoreA + scoreB + 1);
    }

    public static string DisplayPhase(bool atRoundEnd = false)
    {
        if (IsWarmup())
            return "warmup";

        try
        {
            var rules = TryGameRules();
            if (rules?.FreezePeriod == true || atRoundEnd)
                return "freeze";
        }
        catch
        {
            if (atRoundEnd)
                return "freeze";
        }

        return atRoundEnd ? "freeze" : "buy";
    }
}
