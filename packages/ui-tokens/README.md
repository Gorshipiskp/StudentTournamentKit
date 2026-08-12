# packages/ui-tokens

Shared design tokens for STK frontends, aligned with **BestMomentsMaker** desktop
(near-black stage · bone text · amber accent · Sora).

## Files

| File | Role |
|------|------|
| `tokens.css` | `:root` variables + base (selection, focus, scrollbars) |
| `primitives.css` | `.btn*`, `.field`, `.panel`, `.badge`, `.callout` |

## Vite

```ts
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');

resolve: {
  alias: {
    '@stk/ui-tokens': path.join(root, 'packages/ui-tokens'),
  },
}
```

```css
@import '@stk/ui-tokens/tokens.css';
@import '@stk/ui-tokens/primitives.css';
```

Overlay OBS keeps `background: transparent` on the canvas — override in `apps/overlay/src/app.css`.
