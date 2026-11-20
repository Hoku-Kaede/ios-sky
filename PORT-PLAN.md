# ios-sky port plan

Target: Redmi 12 5G (`sky` / `sky_in` / `parrot`), model `23076RN4BI`, stock
`OS2.0.205.0.VMWINXM` (Android 15). Base: `ios-topaz` (XNU 8796 + iOS 16.7.16
iPhone X userland). All recon is read-only. Nothing is unlocked, flashed or
wiped yet.

## 1. Verified device facts

| Item | Value | Source |
| --- | --- | --- |
| Boot slot | `_b` | `getprop ro.boot.slot_suffix` |
| Bootloader | locked, `verifiedbootstate=green`, `ro.boot.flash.locked=1` | `getprop` |
| Dynamic partitions | yes | `getprop ro.boot.dynamic_partitions` |
| DTB index | 8 (`ro.boot.dtb_idx`) | `getprop` |
| DTBO index | 27 (`ro.boot.dtbo_idx`) | `getprop` |
| Board DTB root | `qcom,montague`, `qcom,msm-id=0x245`, `qcom,board-id=0x600` | `vendor_boot.img` @0xac7000, 0x64e97 bytes |
| DTBO 27 root | `qcom,ravelin-qrd`, includes `0x245`, Xiaomi nodes | `dtbo.img` overlay 27 |
| CPU | 2x Cortex-A78 (`0xd41` v1) + 6x Cortex-A55 (`0xd05` v2), 8 cores | `/proc/cpuinfo` |
| CPU features | `atomics`, `lrcpc`, `rcpc` present; TGran16 unverified | `/proc/cpuinfo` |
| RAM | ~5.2 GiB reported by Android | `free -h` |
| Console UART | `/soc/qcom,qup_uart@a88000:115200n8` | board DTB `chosen` |
| Anti-rollback | `anti_version.txt` = `1` | firmware |

## 2. MMIO delta: ios-topaz -> ios-sky

`ios-topaz` hardcodes every hardware address in `tools/mkadt.py`,
`shim/shim.c` and the hardware patches. Sky needs these exact replacements.
Do not reuse the generic `qcom,parrot` DTB: the real board DTB is
`qcom,montague` and Android still reports `ro.board.platform=parrot`.

| Block | Topaz value | Sky value | Change site |
| --- | --- | --- | --- |
| GICD | `0x0f200000` | `0x17200000` | `mkadt.py` `GICD`; `shim/shim.c` `GICD_BASE` |
| GICR | `0x0f300000` | `0x17260000` | `mkadt.py` `GICR`; `shim/shim.c` `GICR_BASE` |
| GIC size | D 0x10000, R 0x100000 | same (DTB `17200000/10000`, `17260000/100000`) | unchanged |
| Timer | architected, TIMEBASE 19200000 | `0x17420000`, 19.2 MHz, PPIs 8-15 on MMIO frames | `mkadt.py` `TIMEBASE` already correct |
| Virtual timer INTID | 19 | 19 (Qualcomm standard; verify in shim) | `shim/shim.c` `VTIMER_INTID`, `mkadt.py` |
| Splash framebuffer | `0x5c000000`, 0xf00000 | `0xb8000000`, `0x2b00000` | `mkadt.py` `FB`/`FB_SIZE`; patches 0010, 0012, 0140, 0142 |
| Panel | 1080x2400 | 1080x2400 (DTBO 08 `focaltech,display-coords`) | `mkadt.py` `FB_W`/`FB_H` unchanged |
| UFS | `0x04804000` | `0x1d84000` | `mkadt.py` `UFS`; `sweet_ufs.c` patch 0028 |
| IMEM restart reason | `0x0c12565c` | `0x146aaf65c` (`0x146aa000 + 0x65c`) | `shim/shim.c` |
| PS_HOLD | `0x0440b000` | unresolved (no `pshold` node in board DTB) | `shim/shim.c`; find in live FDT/XBL |
| SPMI arbiter | `0x0c440000` core region | `0x0c42d000` arbiter; regions `0x0c400000`, `0x0c440000`, `0x0c4c0000` | keys/battery patches |
| Touch bus | QUP0 SE2 `0x04a88000` | QUP SE9 I2C `0x00a8c000` | touch patches, new driver |
| Battery/gauge | I2C1 SE `0x04a84000` | SPMI PM7250B (SID 2, qgauge `@4800`) | patch 0091 needs rewrite |
| MDP | topaz-specific | `0xae00000` (`qcom,mdss_mdp@ae00000`) | display patches |
| DSI ctrl0 | topaz-specific | `0xae94000` | display patches |
| Kernel RAM window | upper bank `0x140000000 + 4G` | TBD; low bank carve-outs end at `0xfa680000` | `mkadt.py` `PHYS_BASE`/`MEM_SIZE`, `--highmem` |

### Sky carve-outs (board DTB, low bank)

`hyp 0x80000000+0x600000`, `smem 0x80900000+0x200000`,
`mpss 0x8a000000+0xd700000`, `ramoops 0x97700000+0x200000`,
`xbl_sc 0xa6e00000+0x40000`, `global_sync 0xa6f00000+0x100000`,
`cpusys_vm 0xe0600000+0x400000`, `trust_ui_vm 0xe0b00000+0x4af3000`,
`tz_stat 0xe8800000+0x100000`, `tags 0xe8900000+0x680000`,
`qtee 0xe8f80000+0x500000`, `trusted_apps 0xe9480000+0x1200000`.

Candidate bring-up window: `0xa7000000` .. `0xe0600000` (~918 MiB, above
`global_sync`, below `cpusys_vm`) or upper DDR bank from `0x100000000`.
Exact bank size unreadable from Android (`/proc/device-tree/memory/reg`
permission denied); get it from a temporary boot shim or live FDT dump.

## 3. Touch resolution (open)

DTBO 08 selects `qcom,i2c-touch-active = 'novatek,NVT-ts'` on
`qupv3_se9_i2c` / `i2c@a8c000`; FocalTech `focaltech@38` on the same bus is
`status = 'disabled'`. DTBO 27 (the one actually applied) has only
`xiaomi-touch` plus a Novatek SPI node. Kernel aliases include
`focaltech,fts` -> `fts_8720`; firmware blobs list `focaltech_ft8725_fw.bin`,
`focaltech_ft8720_hx.ini`, `focaltech_ts_fw_.bin`. Overlay 08 also sets
`ic-type=8726081c` and display coords 1080x2400.

Conclusion: board is **Novatek via I2C on SE9** with FocalTech fallback
compiled in; the applied overlay 27 hides the bus node behind `xiaomi-touch`.
Before writing a driver, confirm by reading `/sys/bus/i2c/devices/`,
`dmesg` touch lines and the live DT `/proc/device-tree/soc/i2c@a8c000/`
from Android. Never assume overlay 08 is active just because its root
looks like a better match.

## 4. Patch classification (201 XNU patches + 2 userland patches)

### A. Reusable unchanged

Generic XNU/build/userland work with no SoC address dependencies:
0001-0009 (clang, UIO_STACKBUF, stub headers, closed-lib gaps), 0043-0045
(crash reports, watchdog, crashdump off), 0048-0057 (log tee, IOKit trace,
sandbox policy, heap text, sampler, containers, ACL resolver), 0057-related
image tweaks, 0099-0094 etc. where no MMIO is referenced. Verify each with
`Select-String -Pattern '0x[0-9a-fA-F]{5,}'` before copying.

### B. Address edits only

- 0010, 0012, 0140, 0142: framebuffer `0x9c000000`/`0x5c000000` ->
  `0xb8000000`, size `0xf00000` -> `0x2b00000`.
- 0028 (`sweet_ufs.c`): UFS `0x4804000` -> `0x1d84000`; UFSHCI version,
  CAP and LUN0 layout must be re-probed (sky is UFS 3.x, `qcom,ufs-phy-qmp-v4-parrot`).
- `tools/mkadt.py`, `shim/shim.c`, `shim/loader.c`, `tools/mkpayload.py`:
  all MMIO constants from section 2.
- 0060 keys: SPMI region offsets need remap to PMK8350 SID 0 `pon_hlos@1300`
  and PM7250B SID 2 `power-on@800`.

### C. New code required

- Touch: no topaz FT5452 driver applies. New GENI SE9 I2C driver at
  `0xa8c000` plus reset/IRQ GPIO from DTBO, Novatek first, FocalTech optional.
- Battery/charger: rewrite 0091 from I2C gauge to SPMI PM7250B qgauge/SMB5.
- Display: topaz MDP scanout path needs new base `0xae00000`, DSI
  `0xae94000`, panel from DTBO 27 (`vtdr6130`/`r66451` variants), DSC and
  `cont_splash_region` at `0xb8000000`.
- GPU: topaz Adreno 610/Mesa work maps to sky Adreno (verify GPU node in
  board DTB); `userland/gpu` and `userland/mesa` patches need review.
- Modem/Wi-Fi (0113-0130): topaz PAS boot from `modem_a` is board-specific.
  Sky uses a different firmware layout; leave disabled initially.
- Audio codec (0145, 0091-adjacent): sky has WCD937x (from DTBO), not topaz.
- CPU boot: topaz parks A53 Silver cores (no TGran16). Sky's A78+A55 both
  likely support 16K (verify TGran16/ID_AA64MMFR0) before copying patch 0082.

## 5. Build/tooling prerequisites

- `xnu-8796` source tree + `blacktop/darwin-xnu-build` workflow on
  `macos-14` / Xcode 15 (XNU 8796 IORPC ABI). GitHub account `Hoku-Kaede`,
  `gh` authenticated with `repo` scope.
- iPhone X (iPhone10,3 / D22AP) iOS 16.7.16 (20H392) IPSW for the userland.
  Apple artifacts stay out of git (`.gitignore`).
- Boot image v4 packing: Xiaomi ABL ignores v1/v2 and drops boot v4 ramdisk.
  Pack shim as boot v4 and append the XNU payload after shim `_end`
  (same as `ios-topaz/shim/build.sh` + `loader.c`).
- Boot-args from topaz: `debug=0xc serial=3 cpus=1 keepsyms=1
  -enable_kprintf_spam -noprogress`.

## 6. Data safety blockers (must clear before any boot test)

1. `DCIM` 14 GiB, `Pictures` 3.5 GiB, `Movies` 1.4 GiB still on phone.
   `D:\PhoneBackup` holds only 13.78 GiB of WhatsApp/YouCut data.
   D: free space is ~12 GiB. Need another destination for ~19 GiB.
2. Bootloader unlock requires user confirmation. Anti-rollback index is 1.
3. iOS root occupies `userdata`; this wipes Android user data. Confirm
   again at the moment of flashing, never earlier.
4. Do not run `fastboot getvar`, `oem unlock`, `flash`, `erase` or `wipe`
   during recon.

## 7. Ordered next actions

1. Back up `DCIM`, `Pictures`, `Movies` to a drive with >=19 GiB free.
2. Get live FDT (`adb exec-out cat /sys/firmware/fdt`) and confirm memory
   banks, PS_HOLD, touch `status`, GCC/QUP RCG offsets while Android runs.
3. Create `Hoku-Kaede/ios-sky` repo, commit tools + recon text only.
   Keep `firmware/`, `extracted/`, `recon/*.dtb`, dumps and Apple artifacts
   out of git.
4. Fork `ios-topaz` content into `ios-sky`, then apply section 2 edits.
5. Build unverified kernel in CI, QEMU smoke test, then ask user to confirm
   unlock and first temporary `fastboot boot`.
