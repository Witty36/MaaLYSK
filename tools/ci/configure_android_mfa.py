#!/usr/bin/env python3
"""Apply MaaLYSK display settings to an ephemeral MFAAvalonia checkout.

MaaLYSK is portrait-first and expects 720x1280 screenshots for its main flow.
MFAAvalonia's Android controller is landscape-first, so this patch:

- creates the hidden virtual display at 720x1280 by default;
- keeps current-screen capture at the real display size (portrait or landscape);
- switches the mobile preview aspect ratio to 9:16.

The script runs from MaaLYSK CI against the temporary mfa-source checkout only.
The MFAAvalonia repository itself is never modified.
"""

from pathlib import Path
import os


DEFAULT_SOURCE_ROOT = "mfa-source"
DEFAULT_WIDTH = 720
DEFAULT_HEIGHT = 1280

PROVIDER_REL = Path("MFAAvalonia.Android/AndroidNativeControllerProvider.cs")
PREVIEW_REL = Path("MFAAvalonia/Views/Mobile/MobileTaskQueueView.axaml.cs")

PROVIDER_MARKER = """        var virtualWidth = useVirtualDisplay
            ? MobileRunConfiguration.Resolution == MobileRunResolution.P1080 ? 1920 : 1280
            : Math.Max(displayInfo.Width, displayInfo.Height);
        var virtualHeight = useVirtualDisplay
            ? MobileRunConfiguration.Resolution == MobileRunResolution.P1080 ? 1080 : 720
            : Math.Min(displayInfo.Width, displayInfo.Height);
"""

PREVIEW_MARKER = "    private const double PreviewAspectRatio = 16.0 / 9.0;"
PREVIEW_REPLACEMENT = "    private const double PreviewAspectRatio = 9.0 / 16.0;"


def rewrite(path: Path, marker: str, replacement: str, description: str) -> None:
    if not path.is_file():
        raise SystemExit(f"[ERR] {description} file not found: {path}")
    text = path.read_text(encoding="utf-8")
    count = text.count(marker)
    if count != 1:
        raise SystemExit(
            f"[ERR] {description} marker matched {count} times in {path}; "
            "MFAAvalonia source has changed."
        )
    path.write_text(
        text.replace(marker, replacement, 1),
        encoding="utf-8",
        newline="\n",
    )
    print(f"patched {description}: {path}")


def main() -> None:
    source_root = Path(os.environ.get("MFA_SOURCE_ROOT", DEFAULT_SOURCE_ROOT))
    width = int(os.environ.get("MFA_ANDROID_VIRTUAL_WIDTH", DEFAULT_WIDTH))
    height = int(os.environ.get("MFA_ANDROID_VIRTUAL_HEIGHT", DEFAULT_HEIGHT))

    provider_replacement = f"""        var virtualWidth = useVirtualDisplay ? {width} : displayInfo.Width;
        var virtualHeight = useVirtualDisplay ? {height} : displayInfo.Height;
"""
    rewrite(
        source_root / PROVIDER_REL,
        PROVIDER_MARKER,
        provider_replacement,
        "Android controller display size",
    )

    preview_path = source_root / PREVIEW_REL
    if not preview_path.is_file():
        raise SystemExit(f"[ERR] mobile preview file not found: {preview_path}")
    preview_text = preview_path.read_text(encoding="utf-8")
    if PREVIEW_MARKER in preview_text:
        if preview_text.count(PREVIEW_MARKER) != 1:
            raise SystemExit(
                f"[ERR] mobile preview marker matched "
                f"{preview_text.count(PREVIEW_MARKER)} times in {preview_path}"
            )
        preview_path.write_text(
            preview_text.replace(PREVIEW_MARKER, PREVIEW_REPLACEMENT, 1),
            encoding="utf-8",
            newline="\n",
        )
        print(f"patched mobile preview aspect ratio: {preview_path}")
    elif PREVIEW_REPLACEMENT in preview_text:
        print(f"mobile preview aspect ratio already portrait: {preview_path}")
    else:
        raise SystemExit(
            f"[ERR] mobile preview aspect ratio marker not found in {preview_path}"
        )

    print(f"MFAAvalonia Android display configured: {width}x{height} virtual display")


if __name__ == "__main__":
    main()
