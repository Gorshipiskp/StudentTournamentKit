import { describe, expect, it } from 'vitest';
import { resolveInviteToken, reviewStatusLabel } from './api';

describe('resolveInviteToken', () => {
  it('reads ?token=', () => {
    expect(resolveInviteToken('?token=abc123')).toBe('abc123');
  });

  it('reads ?invite=', () => {
    expect(resolveInviteToken('?invite=xyz')).toBe('xyz');
  });

  it('returns null without token', () => {
    expect(resolveInviteToken('')).toBeNull();
    expect(resolveInviteToken('?matchId=m1')).toBeNull();
  });
});

describe('reviewStatusLabel', () => {
  it('maps paused', () => {
    expect(reviewStatusLabel('paused')).toContain('пауза');
  });
});

describe('humanApiError', () => {
  it('maps expired invite', async () => {
    const { humanApiError } = await import('./api');
    expect(humanApiError('401 unauthorized')).toMatch(/Ссылка/);
  });
});
