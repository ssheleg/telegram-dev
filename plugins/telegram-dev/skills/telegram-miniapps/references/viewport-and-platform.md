# The viewport, the safe areas, and the platforms

**Load this when** the app looks wrong on a real device: content under the
header, a button behind the home indicator, or a layout that jumps when the
keyboard opens.

*Read from `core.telegram.org/bots/webapps` on 2026-08-25, Bot API 10.3.*

## `100vh` is wrong, on both platforms, differently

`window.Telegram.WebApp` publishes the numbers instead:

| Field | Meaning |
|---|---|
| `viewportHeight` | visible height **right now**, including while the app is being dragged |
| `viewportStableHeight` | the height between gestures — what a layout should size to |
| `safeAreaInset` | device insets: notch, home indicator |
| `contentSafeAreaInset` | Telegram's own chrome: the header |
| `isExpanded` | whether the user has pulled the sheet to full height |
| `isFullscreen`, `isActive`, `isOrientationLocked` | Bot API 8.0+ state |

Size to `viewportStableHeight`, pad by both insets, and subscribe to
`viewportChanged`. A layout built on `viewportHeight` alone reflows on every
drag.

## The events that matter

- `viewportChanged` — with `isStateStable`; ignore the unstable ones for layout.
- `themeChanged` — the user can switch theme while the app is open.
- `activated` / `deactivated` — the app can be backgrounded without being closed.

## Theme comes from Telegram

`themeParams` carries `bg_color`, `text_color`, `hint_color`, `link_color`,
`button_color`, `button_text_color`, `secondary_bg_color` and more; `colorScheme`
is `light` or `dark`. Bind CSS custom properties to them once and let the app
follow the client. A hardcoded palette is wrong for half the users on the first
day and all of them after a theme update.

## Capabilities are versioned, and older clients silently lack them

Every WebApp method has a minimum Bot API version, and `WebApp.version` tells you
what the client supports. `WebApp.isVersionAtLeast('8.0')` is the guard;
calling a newer method on an older client does nothing and reports nothing.

Recent additions worth knowing about, all 8.0+: `requestFullscreen()`,
`addToHomeScreen()`, `DeviceStorage` (~5 MB) and `SecureStorage`, `shareMessage()`,
`downloadFile()`, `shareToStory()`, and the sensor APIs (`Accelerometer`,
`DeviceOrientation`, `Gyroscope`, `LocationManager`).

## The buttons are Telegram's, not yours

`MainButton`, `SecondaryButton`, `BackButton` and `SettingsButton` are rendered by
the client, sit outside your viewport, and match the user's theme for free. A
custom sticky footer duplicates them and loses to the keyboard on iOS.

`WebApp.ready()` tells the client the app has painted; `WebApp.expand()` asks for
full height. Call `ready()` — until you do, the client may keep showing its
loading state over a page that is already interactive.
