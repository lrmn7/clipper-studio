## Install

Clipper Studio isn't code-signed yet, so macOS and Windows warn the first time you open it. The app is safe to run. Here's how to get past the warning.

### macOS (Apple silicon)

1. Open `ClipperStudio_<version>_aarch64.dmg` and drag **ClipperStudio** into **Applications**.
2. Open ClipperStudio. macOS says it can't verify the app: click **Done**.
3. Go to **System Settings → Privacy & Security**, scroll down to the message about ClipperStudio, and click **Open Anyway**. Confirm with your password.

If macOS says the app "is damaged and can't be opened", or there's no **Open Anyway** button, run this in Terminal, then open ClipperStudio again:

```bash
xattr -dr com.apple.quarantine /Applications/ClipperStudio.app
```

### Windows (x64)

1. Unzip `ClipperStudio_<version>_windows_x64.zip` into a folder you keep, for example `Documents\ClipperStudio`. Keep the `resources` folder next to `clipperstudio.exe`.
2. Open `clipperstudio.exe`. If **Windows protected your PC** appears, click **More info → Run anyway**.

Work or school PCs can block unsigned apps entirely. Ask your IT team in that case.

### Linux (x64)

```bash
tar xzf ClipperStudio_<version>_linux_x64.tar.gz
./ClipperStudio/clipperstudio
```

Keep the `resources` folder next to `clipperstudio`. Needs a desktop with Vulkan graphics drivers (most current distributions have them).

### Known limits

- Recording a voiceover in the editor works on macOS only for now.
- ClipperStudio updates itself from here on: it checks when it opens, and **Settings → Help & about → Update and restart** installs the new version (no install warning this time). If that fails, download the new version from its release page.
