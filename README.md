# a17_sukiSU-ultra

Sony Xperia 1 V（`pdx234`）· **LineageOS 24.0** 内核 CI 编排仓。

把两套方案揉在一起：

- 兼容性 / 刷写策略 ← [ljh195/xperia-1v-sukisu-builtin](https://github.com/ljh195/xperia-1v-sukisu-builtin)
- 23.2 增强功能 ← [planktonzp/a16_sony_sm8550_SukiSU_SUSFS](https://github.com/planktonzp/a16_sony_sm8550_SukiSU_SUSFS)

详细取舍见 [`docs/DESIGN.md`](docs/DESIGN.md)。版本钉死见 [`build.env`](build.env)。

## 特性

| 能力 | 说明 |
|---|---|
| SukiSU Ultra | `builtin` 编进内核（不用 LKM） |
| SUSFS | 默认仓内 vendored；可选上游 `susfs4ksu` |
| Baseband-guard / BBR / LZ4KD | `full` profile 开启（对齐 23.2 体验） |
| vermagic | 强制与官方 `uname -r` 一致 |
| 工具链 | AOSP **clang-r596125 / 22.0.2**（`android17-release`）+ pahole ≥ 1.25 |
| 产物 | `boot-new.img` **和** AnyKernel3 zip |

## 使用（GitHub Actions）

> Actions 要求 `.github/workflows/` 位于**仓库根目录**。请把 `a17_sukiSU-ultra/` **作为独立仓库根**推送（不要嵌在其它 repo 子目录里跑 CI）。

1. `gh repo create ... --source=a17_sukiSU-ultra --push`（或手动建仓后推送本目录内容）  
2. Actions → **Build kernel** → Run workflow：  
   - `profile`: `full`（默认）或 `compatible`  
   - `susfs_source`: `vendored`（默认）或 `upstream`  
3. 下载 Artifact：`boot-new.img` / `AnyKernel3-*.zip` / `Image`

### 刷入（推荐）

```bash
adb reboot bootloader
fastboot flash boot boot-new.img   # 只刷 boot
fastboot reboot
```

然后安装 [SukiSU Manager](https://github.com/SukiSU-Ultra/SukiSU-Ultra/releases)。

### 回滚

```bash
# 与 build.env 里 BOOT_DATE 对应的官方 boot
curl -LO https://mirrorbits.lineageos.org/full/pdx234/<BOOT_DATE>/boot.img
fastboot flash boot boot.img
```

> ⚠️ **不要刷 `init_boot`。**

### OTA / 换 Nightly 后

1. 跑 **Update baseline**（从最新 LOS 24.0 `boot.img` 刷新 `configs/` + `build.env`）  
2. 再跑 **Build kernel**

或本机确认：

```bash
uname -r   # 必须与 EXPECTED_RELEASE 一致，否则先更新 baseline
```

## 仓库结构

```text
a17_sukiSU-ultra/
├── build.env                 # Nightly / commit / vermagic 钉死
├── configs/pdx234.config     # 官方 boot 提取的 IKCONFIG
├── patches/                  # SUSFS + Sony fixup + compat
├── susfs/                    # vendored SUSFS 源文件
├── scripts/                  # boot 重打包 / 校验
├── docs/DESIGN.md
└── .github/workflows/
    ├── build-kernel.yml      # 主编译
    └── update-baseline.yml   # 刷新官方基线
```

## 本地不编译

完整内核构建在 Ubuntu runner 上进行（Clang 22、大内存/swap）。本仓只负责编排与补丁。

## License

内核改动遵循 GPLv2。编排脚本与文档以仓库声明为准。  
