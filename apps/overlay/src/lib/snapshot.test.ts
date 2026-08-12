import { describe, expect, it } from 'vitest';
import {
  emptyOverlaySnapshot,
  parseOverlaySnapshot,
  resolveMatchId,
  SnapshotParseError,
} from './snapshot';

describe('parseOverlaySnapshot', () => {
  it('parses contract-shaped message', () => {
    const snap = parseOverlaySnapshot({
      protocol: 1,
      type: 'overlay.snapshot',
      match_id: 'm_1',
      version: 2,
      data: {
        scene: 'ingame',
        team_a: { name: 'Alpha', score: 7 },
        team_b: { name: 'Beta', score: 5 },
        map: 'de_mirage',
        round: 12,
        phase: 'live',
        match_status: 'live',
        paused: false,
        judge: { status: 'none', banner: null },
        watermark: { text: 'STP', visible: true },
      },
    });
    expect(snap.version).toBe(2);
    expect(snap.data.team_a.score).toBe(7);
    expect(snap.data.watermark.visible).toBe(true);
  });

  it('forces watermark.visible true', () => {
    const snap = parseOverlaySnapshot({
      protocol: 1,
      type: 'overlay.snapshot',
      match_id: 'm_1',
      version: 1,
      data: {
        scene: 'waiting',
        team_a: { name: 'A', score: 0 },
        team_b: { name: 'B', score: 0 },
        watermark: { text: 'STP', visible: false },
      },
    });
    expect(snap.data.watermark.visible).toBe(true);
  });

  it('rejects non-snapshot type', () => {
    expect(() =>
      parseOverlaySnapshot({ protocol: 1, type: 'patch', version: 1, data: {} }),
    ).toThrow(SnapshotParseError);
  });

  it('emptyOverlaySnapshot has waiting scene', () => {
    const snap = emptyOverlaySnapshot('m_x');
    expect(snap.match_id).toBe('m_x');
    expect(snap.data.scene).toBe('waiting');
  });
});

describe('resolveMatchId', () => {
  it('reads /overlay/{id}', () => {
    expect(resolveMatchId('/overlay/m_abc', '')).toBe('m_abc');
  });

  it('prefers query matchId', () => {
    expect(resolveMatchId('/overlay/other', '?matchId=m_q')).toBe('m_q');
  });
});
