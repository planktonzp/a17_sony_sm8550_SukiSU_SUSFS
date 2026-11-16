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
| `compatible` | SukiSU + SUSFS only | 先求稳、排查兼容性 |
| `full`（默认） | 上述 + BBG + BBR + LZ4KD/LZ4 | 复现 23.2 增强体验 |

`full` 会改动更多 `CONFIG_*`。若出现 Wi‑Fi/相机异常，先用 `compatible` 二分。

## 流水线概览

```text
build.env + configs/pdx234.config
        │
        ▼
 LineageOS kernel @ KERNEL_COMMIT
        │
        ├─ SukiSU Ultra (builtin, pinned)
        ├─ SUSFS (vendored | upstream+Sony fixup)
        ├─ [full] Baseband-guard / BBR / LZ4*
        ├─ LOCALVERSION = 官方后缀（强制）
        ├─ Clang 22 + banner 指纹伪装
        ▼
   Image ──┬── repack → boot-new.img
           └── AnyKernel3 → *.zip
```

## 工具链对齐

| 组件 | 钉死版本 | 来源 |
|---|---|---|
| Clang / LLD | **r596125 / 22.0.2** | AOSP `prebuilts/clang/host/linux-x86` @ `android17-release` |
| pahole | **≥ 1.25**（官方 config 记 `CONFIG_PAHOLE_VERSION=125`） | Ubuntu `dwarves`，启动时校验 |
| 内核源码 | `build.env` → `KERNEL_COMMIT` | LineageOS `lineage-24.0` |
| SukiSU | `SUKISU_COMMIT` | 可单独升级，与工具链无关 |

不再使用 `apt.llvm.org` 的通用 LLVM 22，避免与 Android 预编译 clang 的 CFI/补丁集不一致。

## 安全红线

1. **绝不刷写 `init_boot`**（LKM 管理器改坏后 recovery/fastbootd 可全挂）。  
2. 刷入前保留官方同版本 `boot.img` 以便回滚。  
3. OTA 后核对 `uname -r`；若 hash 变了，先跑 **Update baseline** 再编译。  

## 非目标

- 不编完整 LineageOS ROM（只编内核）。  
- 不提供通用 GKI / `android17-6.18` LKM（本机内核是 5.15）。  
- 不保证跨 Nightly 二进制通用（vermagic 绑定）。  
