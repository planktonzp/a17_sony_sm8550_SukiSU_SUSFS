# 设计说明：LOS 24 + 23.2 增强融合

## 目标

在 **LineageOS 24.0（Android 17）/ Sony Xperia 1 V (pdx234)** 上：

1. 获得与 [a16_sony_sm8550_SukiSU_SUSFS](https://github.com/planktonzp/a16_sony_sm8550_SukiSU_SUSFS)（LOS 23.2）相近的增强体验  
2. 采用 [xperia-1v-sukisu-builtin](https://github.com/ljh195/xperia-1v-sukisu-builtin) 的兼容性策略，避免 vendor 模块与 `init_boot` 事故  

本仓库是 **CI 编排仓**：不长期托管完整内核树，由 GitHub Actions 拉取源码、打补丁、编译并上传产物。

## 冲突取舍

| 议题 | spacealtctrl (23.2) | ljh195 (24) | 本仓采纳 |
|---|---|---|---|
| 内核钉死方式 | 跟 `lineage-23.2` tip | 精确 commit + boot 日期 | **精确 commit**（`build.env`），可手动/工作流刷新 |
| 工具链 | Clang r547379 | LLVM/Clang **22.0.2** | **AOSP `clang-r596125`**（`android17-release`，对齐官方 banner） |
| `LOCALVERSION` | 自定义 branding | 与官方 **逐字一致** | **官方后缀**（否则 vendor `.ko` 全挂） |
| `/proc/version` | 不伪装 | 伪装 CC/主机/时间戳 | **伪装**（可选关闭） |
| SukiSU 分支 | `builtin` | `builtin`（钉 commit） | **builtin**，默认钉 commit |
| SUSFS | 构建时 clone + Sony fixup | 仓内 vendored + compat | **默认 vendored**；可选 `upstream` |
| Baseband-guard | 有 | 无 | **有**（`full` profile） |
| BBR / LZ4KD / LZ4 1.10 | 有 | 无 | **有**（`full` profile） |
| KPM | 文案有、实际基本未开 | 关 | **默认关**（不稳） |
| 产物 | AnyKernel3 | `boot-new.img` | **两者都出** |
| 刷写分区 | AK3 / recovery | 只刷 `boot` | **只允许改 `boot`**，禁止 `init_boot` |

## 构建剖面（profile）

| profile | 内容 | 何时用 |
|---|---|---|
| `compatible` | Root(SU) + SUSFS only | 先求稳、排查兼容性 |
| `full`（默认） | SukiSU：BBG + BBR + LZ4KD/LZ4 1.10；**BakaSU：仅 BBR + LZ4KD**（已砍 BBG / LZ4 1.10 / 多余 ZRAM crypto） | 复现或瘦身 23.2 体验 |

`full` 会改动更多 `CONFIG_*`。若出现 Wi‑Fi/相机异常，先用 `compatible` 二分。

## 双流水线（互不交叉）

| | SukiSU | BakaSU |
|---|---|---|
| Workflow | `build-kernel.yml` | `build-kernel-bakasu.yml` |
| Env | `build.env` | `build-bakasu.env` |
| SU 集成 | tar 拷贝 `drivers/kernelsu` | git checkout + symlink（Kbuild 要 `.git`） |
| Hook | SukiSU builtin + SUSFS 附加 | **SUSFS Inline Hook**（choice） |
| Compat 补丁 | `patches/51_fix_sukisu_builtin_compat.patch` | `patches/bakasu/51_fix_sys_read_signature.patch` |
| 产物名 | `AnyKernel3-*-sukisu-*.zip` | `AnyKernel3-*-bakasu-*.zip` |
| 管理器 | SukiSU Manager Releases | BakaSU Manager nightly |
| 依赖获取 | SukiSU 仍有 tar/vendored；clang 用 archive | **一律 git**（clang sparse / SUSFS / LZ4KD）；仅 `boot.img` 仍 HTTP |
| `full` 增强 | BBG + BBR + LZ4 1.10 + LZ4KD 等 | **BBR + LZ4KD**（无 BBG / 无 LZ4 1.10 / 无多余 ZRAM crypto） |
| WireGuard | 跟官方 `CONFIG_WIREGUARD=y` | **强制关闭** |
| LTO | 固定 ThinLTO（hosted 16G） | 可选 `lto=thin\|full`（full 建议 ≥32G runner） |

设备基线（`KERNEL_COMMIT` / vermagic / clang 指纹）由 **Update baseline** 同时写进两份 env；SU 钉死项各自维护。

## 流水线概览

```text
configs/pdx234.config
        │
   ┌────┴────┐
   ▼         ▼
build.env   build-bakasu.env
   │         │
   ▼         ▼
 SukiSU     BakaSU          ← 独立 workflow，无共享 job
   │         │
   ├─ SUSFS (vendored | upstream+Sony fixup)
   ├─ [full] SukiSU: BBG/BBR/LZ4* ；BakaSU: BBR+LZ4KD
   ├─ LOCALVERSION = 官方后缀（强制）
   ├─ Clang 22 + banner 指纹伪装
   ▼
 Image ──┬── repack → boot-new.img
         └── AnyKernel3 → *-sukisu|bakasu-*.zip
```

## 工具链对齐

| 组件 | 钉死版本 | 来源 |
|---|---|---|
| Clang / LLD | **r596125 / 22.0.2** | AOSP `prebuilts/clang/host/linux-x86` @ `android17-release` |
| pahole | **≥ 1.25**（官方 config 记 `CONFIG_PAHOLE_VERSION=125`） | Ubuntu `dwarves`，启动时校验 |
| 内核源码 | `build.env` → `KERNEL_COMMIT` | LineageOS `lineage-24.0` |
| SukiSU | `SUKISU_COMMIT`（`build.env`） | 可单独升级，与工具链无关 |
| BakaSU | `BAKASU_COMMIT`（`build-bakasu.env`） | 可单独升级；与 SukiSU 流水线无关 |

不再使用 `apt.llvm.org` 的通用 LLVM 22，避免与 Android 预编译 clang 的 CFI/补丁集不一致。

## 安全红线

1. **绝不刷写 `init_boot`**（LKM 管理器改坏后 recovery/fastbootd 可全挂）。  
2. 刷入前保留官方同版本 `boot.img` 以便回滚。  
3. OTA 后核对 `uname -r`；若 hash 变了，先跑 **Update baseline** 再编译。  

## 非目标

- 不编完整 LineageOS ROM（只编内核）。  
- 不提供通用 GKI / `android17-6.18` LKM（本机内核是 5.15）。  
- 不保证跨 Nightly 二进制通用（vermagic 绑定）。  
