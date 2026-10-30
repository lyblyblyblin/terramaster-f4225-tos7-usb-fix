# 铁威马 F4-225 TOS7 升级：U 盘引导镜像 110MB 空分区裁剪实战

> 铁威马 TOS7 升级 / 自带 128MB U 盘 / usb_initboot_legacy 镜像裁剪 / TOS6 升 TOS7
> 2026-10-30 在铁威马 F4-225 上测试成功（主板设置为 UEFI+Legacy）。

## 文档

- [TOS6→TOS7 升级排查档案（问题现象 + 全部排查命令与 6 个日志）](docs/tos7-upgrade-fix.md)
- [删除 img 镜像后面 110MB 空分区（120MB 裁剪教程，含 trim.py）](docs/trim-120mb.md)
- [F4-225 机型信息（≈F4-221、适用机型与 BIOS 版本要求）](docs/f4-225-info.md)

## 下载

| 文件 | 说明 |
| --- | --- |
| [usb_initboot_legacy_2037_120mb.7z](https://github.com/lyblyblyblin/terramaster-f4225-tos7-usb-fix/releases/download/v1.0.0/usb_initboot_legacy_2037_120mb.7z) | 裁剪后的 **120MB 引导镜像**（7z 压缩，约 98.8MB）。解压得到 `usb_initboot_legacy_2037_120mb.img`，用 rufus / BalenaEtcher 写入 U 盘即可 |
| [trim.py](trim.py) | 裁剪脚本（Python 3，仅标准库）：保留 MBR+GPT+primary 分区，重建自洽的 GPT 备份头与备份分区表 |
| [01_update2026-01-10-18-57-05.log](logs/01_update2026-01-10-18-57-05.log) ~ [06_update2026-10-30-16-10-53.log](logs/06_update2026-10-30-16-10-53.log) | 6 个升级/排查日志（正文在 `docs/tos7-upgrade-fix.md` 有逐条解读） |

> 解压后建议核对 SHA-256：`sha256sum usb_initboot_legacy_2037_120mb.img`
> 裁剪成品镜像校验值：`6dc2f5a6118ca6f7845e6cc70cb2769aafe3b932080553ccee6a89273ac22e17`

## 问题背景

铁威马（TerraMaster）F4-225 等机型**自带的启动 U 盘只有 128MB**。

- 新版引导镜像（`usb_initboot_legacy_2037.img`）是 **230MB**，末尾约 **110MB 是空分区**（未分配区域）；
- 镜像太大 → 无法完整写入 128MB 的自带 U 盘 → 升级后无法引导 → 开机回到初始化/安装界面，只能装回 TOS 6。

**结论：** 镜像里唯一有用的是那个约 120MB 的 `primary` 分区（ext 文件系统），后面约 110 MiB 全是未分配空间。把镜像裁剪成"分区表 + 120MB 分区 + 自洽的备份 GPT"，就能装进 128MB 的 U 盘。

## 裁剪原理（详见 trim.py 与 docs/trim-120mb.md）

1. 只保留扇区 `0 ~ 245,726`：MBR 引导扇区 + GPT 头 + 分区表 + `primary` 分区（内容**逐字节不变**）；
2. 丢弃后面约 110 MiB 未分配区域；
3. **重建自洽的 GPT**：补上备份分区表与备份 GPT 头，更新主头字段并重算 CRC32；
4. 输出 **245,760 扇区 = 125,829,120 字节 = 正好 120 MiB** 的镜像。

## 使用步骤

```bash
# 1. 下载并解压 Release 里的 7z（得到 120MB 镜像），或自行裁剪：
python3 trim.py <官方下载的230MB镜像.img> usb_initboot_legacy_120mb.img

# 2. 校验
sha256sum usb_initboot_legacy_120mb.img

# 3. 用 rufus / BalenaEtcher 把镜像写入 F4-225 自带的 U 盘
```

注意事项（来自实测笔记）：

- 直接 UEFI 模式无法引导该 Legacy 镜像，需在主板设置 **UEFI+Legacy** 兼容模式；
- 升级 U 盘后在系统里看 BIOS 版本仍是 MAPL0304V16 —— 那是**主板固件版本**，不是 U 盘版本，系统下没有地方能看 U 盘具体版本；
- TOS 系统与 U 盘系统存在绑定关系：**U 盘系统过低无法启动硬盘系统**，需对应升级；
- 更换 U 盘只能换体积小的（原装就是体积很小的 128MB U 盘）；
- 升级 TOS6 用的 U 盘镜像是 `USB_Initboot_UEFI-229.img`，需要切换到 UEFI 模式才能启动。

## 适用机型

F2-221、F2-421、F4-221、F5-221、F5-421、F2-422、F4-422、F5-422（共 8 个机种）

BIOS 版本要求：`MAPL0304V16` 至 `MAPL0304V22`，或 `MAPL0303V16` 至 `MAPL0303V22`（可在 TOS 控面板 → 通用设置 → 系统 → 更新 → BIOS/InitBoot 位置查看；也可在技术支持 → 问题反馈收集系统报告，解压后打开 `device.txt` 查看）。

## 免责声明

- 操作前请自行备份数据；刷写 U 盘有一定风险，本仓库内容仅供参考，风险自负。
- 原始镜像版权归铁威马（TerraMaster）所有，本仓库仅提供裁剪脚本、使用说明与实测记录。
- 不同型号/版本请先核对你的镜像分区表（可参考 docs/trim-120mb.md 的结构确认是否一致）。
