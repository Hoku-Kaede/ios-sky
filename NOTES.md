# ios-sky — working notes

Goal: bring up iOS 16 userland + XNU on Redmi 12 5G / `sky` (SM4375, `parrot`).
Base: `ios-topaz`, not `ios-sweet` (newer ABL/UFS/display/GPU work).

Safety: no flash, no wipe, no `fastboot getvar`. Unlock attempted 2026-11-20;
still locked. Full plan and MMIO delta: `PORT-PLAN.md`.

## State (2026-11-20)

Firmware downloaded and verified: `firmware/sky_full.tgz`, 6,276,008,361 bytes,
115 tar members. Extracted `boot.img`, `vendor_boot.img`, `dtbo.img`,
`abl.elf`, `rawprogram0.xml`, `anti_version.txt`, `misc.txt`, `vbmeta.img`,
`imagefv.elf`, `uefi.elf` under `extracted/<build>/images/`.

Board DTB extracted from `vendor_boot.img` @ `0xac7000`, size `0x64e97`, to
`recon/sky_board.dtb`. Root is `qcom,montague`, `qcom,msm-id=0x245`,
`qcom,board-id=0x600`. DTBO has 29 overlays; applied index 27 root is
`qcom,ravelin-qrd` but carries Xiaomi nodes. Do not judge overlay by model.

Boot image header v4: `kernel_size=0x2cc0e8c`, `ramdisk_size=0x150efc`,
`header_size=0x630`. `tools/unpack_bootv2.py` cannot parse v4.
`vendor_boot.img` header v4: `page_size=0x1000`,
`vendor_ramdisk_size=0xac5897`; DTB at `0xac7000`.

ABL is ELF32 ARM (0x204600 bytes). Only Xiaomi secure-boot cert strings;
no useful boot info. Do not spend more time on it.

## Hardware map (board DTB + overlay 27)

- GICv3: `0x17200000` (D 0x10000) / `0x17260000` (R 0x100000)
- Timer: `0x17420000`, 19.2 MHz, MMIO frames `0x17421000`+ (PPIs 8-15)
- UFS: `0x1d84000`, `qcom,ufshc`; PHY `qcom,ufs-phy-qmp-v4-parrot` in overlay 27
- MDP: `0xae00000`; DSI ctrl0 `0xae94000`
- Console UART: `0xa88000` (`stdout-path` in board DTB)
- IMEM restart reason: `0x146aa000 + 0x65c = 0x146aaf65c`
- SPMI arbiter: `0xc42d000`; regions `0xc400000`, `0xc440000`, `0xc4c0000`
- Splash framebuffer: `0xb8000000`, size `0x2b00000` (overlay 27 `splash_region`)
- Battery: SPMI PM7250B SID 2, qgauge `@4800`, SMB5 charger (overlay 27)
- Touch: overlay 08 selects Novatek `0x62` on `i2c@a8c000` (QUP SE9);
  FocalTech `focaltech@38` same bus is `disabled`. Overlay 27 (applied)
  has only `xiaomi-touch` + Novatek SPI node. Resolve before driver work.
- CPU: 2x A78 `0xd41` v1 + 6x A55 `0xd05` v2; `atomics`, `lrcpc`, `rcpc`.
  TGran16 still unverified.
- RAM: ~5.2 GiB from Android. Low-bank carve-outs end at `0xfa680000`;
  exact memory banks unreadable via shell. Get from live FDT dump.

## Device state

Slot `_b`, locked (`ro.boot.flash.locked=1`, `verifiedbootstate=green`),
dynamic partitions true, `ro.boot.dtb_idx=8`, `ro.boot.dtbo_idx=27`.
OEM unlocking enabled: `sys.oem_unlock_allowed=1`. Fastboot driver fixed;
`fastboot devices` sees the phone. No `getvar` used.

ADB changes already applied: animation scales 0.5,
`background_process_limit=4`; debloated analytics/MSA/mipicks/Facebook/
bugreport for user 0. Lawnchair + iOS Icon Pack installed (hash
`46547dec8655bfcd27f34e7dd1007c9ec5a3d36414e5612d46c6b67bd32ebc94`),
Lawnchair set as default home. Icon theme not yet applied in UI.

## Data safety

`D:\PhoneBackup` has 13.78 GiB WhatsApp/YouCut, verified.
Documents copied 2026-11-20, verified byte-for-byte:

- `/sdcard/Documents` -> `D:\PhoneBackup\Documents`: 85 files, 556910 bytes.
- `/sdcard/Download` document files -> `D:\PhoneBackup\DownloadDocuments`:
  47 files, 47698054 bytes. Extensions: pdf/doc/docx/txt/xls/xlsx/ppt/pptx/
  odt/epub/rtf/csv.
- `fifth sem.pdf` is zero bytes on phone and backup. No other PDF/DOC/TXT
  files exist outside those two locations.
- No erase performed. User confirmed erase scope "All non-documents" and
  chose "Unlock now"; unlock itself wipes userdata, including Documents.

Phone still holds `DCIM` 14 GiB, `Pictures` 3.5 GiB, `Movies` 1.4 GiB plus
non-document Download files. No separate erase needed before unlock.

## Unlock attempt (2026-11-20)

Official Mi Unlock `7.6.727.43` downloaded and signed in. ZIP SHA256
`6BB390BDDAAFF3E75A6A2B1ECAFA3F49BF6E4D93747302A6870698FB26285A32`.
Fastboot driver fixed; both SDK and tool `fastboot devices` work.

First unlock failed: `Couldn't unlock. Please add your account in Settings >
Developer options > Mi Unlock status.` Play Store had no Xiaomi Community.
Sideloaded developer-signed `com.mi.global.bbs` 5.4.40 (500440), 28,370,531
bytes, SHA256 `F4D0C44DF5475F406BF8A2A609F5D395A62E0DF5C01FE27F9120F6EDACC9002C`.
Signed in with same Mi account; region set to Global. `Apply for unlocking`
returned: `Application quota limit reached,please try again after 11/22
(mm/dd) 00:00 (GMT+8)`. That is `2026-11-21 21:30 IST`. Stop unlock attempts
until then. No Mi account binding has been confirmed yet.

## Repo / git

`ios-sky/` is its own git repo, public remote `Hoku-Kaede/ios-sky`.
Local identity: `Beerus` / `317692443+Hoku-Kaede@users.noreply.github.com`.
`gh` authenticated as `Hoku-Kaede` (`gist`, `read:org`, `repo`).
Pushed commits: `051d233` (initial recon), `ec4823f` (port base),
`2d0cd46` (record verified document backup; no erase yet).
Commit text/tools only. Keep `firmware/`, `extracted/`, `recon/*.dtb`,
dumps, serials and Apple artifacts out.

## Progress (2026-11-20)

- `Hoku-Kaede/ios-sky` created, public, first commit `051d233` pushed.
- Topaz base copied in: `shim/`, `xnu/patches/` (201), `userland/`,
  `.github/`, tools. Upstream README kept as reference with a sky header.
- Applied sky MMIO to `tools/mkadt.py`: GICD `0x17200000`, GICR
  `0x17260000`, FB `0xb8000000`/`0x2b00000`, UFS `0x1d84000`,
  kernel RAM window `0xbb000000 + 0x24000000`, synthetic ECID, sky strings,
  8 CPU nodes with sky MPIDRs (`SKY_CPUS=N` override).
- Applied sky MMIO to `shim/shim.c`: GICD/GICR, IMEM `0x146aaf65c`,
  CPU topology (6 A55 at `0x0-0x5`, 2 A78 at `0x600/0x700`), handoff target
  `0x600`, cpufreq probe disabled. PS_HOLD still unresolved.
- Added `tools/unpack_bootv4.py`; verified boot.img and vendor_boot.img
  extraction. `tools/mkadt.py` runs and emits `recon/sky.adt`.
- Copied and verified all phone documents to `D:\PhoneBackup`; no erase yet.
- Mi Unlock tool, driver, Xiaomi Community sign-in and Global region done.
  Apply for unlocking blocked by quota until `11/22 00:00 GMT+8`.
- XNU patches not yet edited for the sky framebuffer (`0xb8000000`).
  No shim compile available locally (no aarch64 cross compiler).

## Next concrete actions

1. Wait until `11/22 00:00 GMT+8`. Apply for unlock in Xiaomi Community, then
   use mobile data for Developer options -> Mi Unlock status -> Add account
   and device, then retry official Mi Unlock.
2. Dump live FDT via recovery/temporary boot; confirm memory banks, PS_HOLD,
   touch status and GCC/QUP RCG offsets. Shell read of `/proc/device-tree`
   is permission denied.
3. Edit framebuffer address in XNU patches (final override patch).
4. Set up `macos-14` CI build; QEMU smoke test.
5. Ask user to confirm first temporary `fastboot boot`.

## Guesses — not verified

- A78/A55 support 16K pages; verify MMFR0 before planning all-8-core SMP.
- Virtual timer INTID 19 assumed (Qualcomm standard); verify in shim.
- Anti-rollback / HyperOS unlock gate risk remains; no unlock performed.
