# ios-sky — working notes

Goal: bring up iOS 16 userland + XNU on Redmi 12 5G / `sky` (SM4375, `parrot`).
Base: `ios-topaz`, not `ios-sweet` (newer ABL/UFS/display/GPU work).

Safety: recon only. No unlock, no flash, no wipe, no `fastboot getvar`.
Full plan and MMIO delta: `PORT-PLAN.md`.

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

ADB changes already applied: animation scales 0.5,
`background_process_limit=4`; debloated analytics/MSA/mipicks/Facebook/
bugreport for user 0. Lawnchair + iOS Icon Pack installed (hash
`46547dec8655bfcd27f34e7dd1007c9ec5a3d36414e5612d46c6b67bd32ebc94`),
Lawnchair set as default home. Icon theme not yet applied in UI.

## Data safety blocker

`D:\PhoneBackup` has 13.78 GiB (WhatsApp/YouCut). Phone still holds
`DCIM` 14 GiB, `Pictures` 3.5 GiB, `Movies` 1.4 GiB. D: free is ~12 GiB.
Need >=19 GiB elsewhere before unlock/flash. `DCIM/Camera` not backed up.

## Repo / git

`ios-sky/` is currently untracked inside `D:\work` (BeerusX repo, remote
`Hoku-Kaede/BeerusX.git`). Local identity there: `Beerus` /
`317692443+Hoku-Kaede@users.noreply.github.com`.
`gh` authenticated as `Hoku-Kaede` (`gist`, `read:org`, `repo`).
No `ios-sky` repo exists yet. Create it; commit text/tools only.
Keep `firmware/`, `extracted/`, `recon/*.dtb`, dumps and Apple artifacts out.

## Next concrete actions

1. Back up `DCIM`, `Pictures`, `Movies` to a drive with >=19 GiB free.
2. Dump live FDT via `adb exec-out cat /sys/firmware/fdt`; confirm memory
   banks, PS_HOLD, touch status and GCC/QUP RCG offsets.
3. Create `Hoku-Kaede/ios-sky`, commit tools + recon text.
4. Copy topaz patches/shim/tools; apply MMIO edits from `PORT-PLAN.md`.
5. Build in CI, QEMU smoke test, then ask user to confirm unlock and first
   temporary `fastboot boot`.

## Guesses — not verified

- A78/A55 support 16K pages; verify MMFR0 before planning all-8-core SMP.
- Virtual timer INTID 19 assumed (Qualcomm standard); verify in shim.
- Anti-rollback / HyperOS unlock gate risk remains; no unlock performed.
