This is an Expo/React Native mobile application. Prioritize mobile-first patterns, performance, and cross-platform compatibility.

Follow [design principles](docs/design-principles.md) when diagnosing problems and designing changes.

## Expo has changed — do not trust your training data

Expo ships breaking changes every SDK release. APIs you remember are likely renamed, moved, or removed. Before writing any code that touches an Expo, EAS, or React Native API:

1. Read the major version of the `expo` package in `package.json`.
2. Fetch the matching versioned docs: `https://docs.expo.dev/versions/v<major>.0.0/`
3. For anything else, fetch https://docs.expo.dev/llms.txt — an index of all Expo docs with corrections to common LLM misconceptions. Follow its links to the specific page you need; never answer from memory.

## Commands

Use `bunx` instead of `npx` if the project uses bun (`bun.lock` present).

```bash
npx expo install <package>  # ALWAYS use instead of npm/yarn/pnpm/bun add — resolves SDK-compatible versions
npx expo start              # start the dev server
npx expo lint               # lint
npx tsc --noEmit            # typecheck
npx expo-doctor             # diagnose dependency and config issues
npx expo install --fix      # fix incompatible package versions
```

Run lint and typecheck before declaring any task done.

## Navigation & Routing

- Use **Expo Router** for all navigation. Routes live in `src/app/` — every file there is a screen, `_layout.tsx` files define navigators. Keep non-route code (components, hooks, utils) outside `src/app/`.
- Import `Link`, `router`, and `useLocalSearchParams` from `expo-router`.
- Docs: https://docs.expo.dev/router/introduction.md

## Building with EAS

Use EAS to build, sign, and submit the app in the cloud (`eas build`, `eas submit`) and to ship over-the-air updates (`eas update`) — no local Xcode or Android Studio required. Run EAS CLI as `bunx eas-cli <command>` in Bun projects, or `npx eas-cli@latest <command>` otherwise; substitute that for bare `eas` in docs examples.
Docs: https://docs.expo.dev/eas/index.md

## Rules

- If `ios/` and `android/` directories do not exist, they are generated (Continuous Native Generation). Never create or edit them by hand — configure native behavior in `app.json` and config plugins.
- Expo Go only includes its bundled native modules. After adding a library with native code, the app needs a development build: `npx expo run:ios|android` locally, or `eas build --profile development`.
- Prefer recommended Expo modules over third-party libraries, and check your available skills before adding dependencies. Docs: https://docs.expo.dev/versions/latest/index.md

## Documentation organization

Use [the documentation index](docs/README.md) to find ongoing development documents,
current references, experiments, and archives. Keep principles, technical debt,
roadmaps, and ideas directly in `docs/`; reserve subfolders for references,
experiments, archives, and local notes. Keep machine-specific notes in ignored `docs/local/`
and new private experiment outputs in ignored `scratch/`. Add status and dates to
proposals, experiment records, and archived snapshots. Update links when moving files.

## Active inference scope

The active browser path now uses the Python agent service (`server/`), which owns
SQLite history and agent execution; Ollama or llama.cpp may be local or remote. Device tools stay
on the requesting client. The retired Node proxy/browser harness has been removed.
See `server/EXECUTION.md` for startup, token handling, and current recovery.

The supported prototype is the browser UI (desktop or phone) connecting through Tailscale to the Python service on Windows, with llama.cpp inference on the Mac over home Wi-Fi. Machine-local inference selection is in ignored server/data/inference.json; Ollama remains supported. Prioritize and test this inference path for new features. Native on-device inference via llama.rn is on hold for future consideration; preserve it and keep shared code type-correct, but feature parity and native testing are not required unless explicitly requested.
