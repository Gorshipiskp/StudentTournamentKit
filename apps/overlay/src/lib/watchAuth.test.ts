import { describe, expect, it } from 'vitest';
import {
  bannerLabel,
  isMockWatch,
  isWatchPath,
  MAX_WATCH_SUBSCRIBERS,
  humanWatchError,
  mediaStatusLabel,
  resolveMediaMode,
  resolveWatchInviteToken,
  sceneLabel,
} from './watchAuth';
import { isPublisherMissingStatus } from './whepClient';

describe('resolveWatchInviteToken', () => {
  it('reads ?token=', () => {
    expect(resolveWatchInviteToken('/watch', '?token=abc')).toBe('abc');
  });

  it('reads /watch/{token}', () => {
    expect(resolveWatchInviteToken('/watch/inv_raw_xyz', '')).toBe('inv_raw_xyz');
  });

  it('prefers query over path', () => {
    expect(resolveWatchInviteToken('/watch/pathTok', '?token=queryTok')).toBe('queryTok');
  });

  it('null without token', () => {
    expect(resolveWatchInviteToken('/watch', '')).toBeNull();
    expect(resolveWatchInviteToken('/overlay/m1', '')).toBeNull();
  });
});

describe('watch helpers', () => {
  it('detects watch path and mock', () => {
    expect(isWatchPath('/watch')).toBe(true);
    expect(isWatchPath('/watch/x')).toBe(true);
    expect(isWatchPath('/overlay/m')).toBe(false);
    expect(isMockWatch('?mock=1')).toBe(true);
    expect(isMockWatch('')).toBe(false);
  });

  it('resolves media mode', () => {
    expect(resolveMediaMode('?mock=1')).toBe('mock');
    expect(resolveMediaMode('?media=fake')).toBe('fake');
    expect(resolveMediaMode('?media=whep')).toBe('whep');
    expect(resolveMediaMode('?media=mock')).toBe('mock');
    expect(resolveMediaMode('')).toBe('whep');
  });

  it('documents max 2 subscribers', () => {
    expect(MAX_WATCH_SUBSCRIBERS).toBe(2);
  });

  it('maps tech pause banner', () => {
    expect(bannerLabel('tech_pause')).toContain('пауза');
    expect(bannerLabel(null)).toBeNull();
  });

  it('humanizes watch errors and scene', () => {
    expect(humanWatchError('429 too many')).toMatch(/2/);
    expect(mediaStatusLabel('waiting_publisher')).toMatch(/картинку/i);
    expect(sceneLabel('ingame')).toBe('Игра');
  });
});

describe('whep publisher missing heuristic', () => {
  it('treats 404 as waiting publisher', () => {
    expect(isPublisherMissingStatus(404, '')).toBe(true);
    expect(isPublisherMissingStatus(400, '{"error":"no stream available"}')).toBe(true);
    expect(isPublisherMissingStatus(403, 'forbidden')).toBe(false);
  });
});
