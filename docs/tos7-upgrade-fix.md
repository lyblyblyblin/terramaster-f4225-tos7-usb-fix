# 铁威马F4-225升级TOS7，实际上的可以的（日志上没有报错），只是U盘里面的镜像无法引导TOS7导致进入系统安装界面，重启后提示初始化安装系统，只能安装TOS6

铁威马F4-225升级TOS7，实际上的可以的（日志上没有报错），只是U盘里面的镜像无法引导TOS7导致进入系统安装界面，重启后提示初始化安装系统，只能安装TOS6

[update2026-01-10-18-57-05.log](../logs/01_update2026-01-10-18-57-05.log)[update2026-05-11-18-40-25.log](../logs/02_update2026-05-11-18-40-25.log)[update2026-05-11-19-18-54.log](../logs/03_update2026-05-11-19-18-54.log)[update2026-07-04-22-04-16.log](../logs/04_update2026-07-04-22-04-16.log)

2026年10月30日 升级U盘后，升级成功的日志

[update2026-10-30-16-10-53.log](../logs/06_update2026-10-30-16-10-53.log)[update_before_reboot_2026-10-30-16-22-40.log](../logs/05_update_before_reboot_2026-10-30-16-22-40.log)

# 铁威马 F4-225 TOS6→TOS7 排查档案

## 问题 1：TOS6→TOS7 升级后开机回安装页（原主问题，已解决）

**现象**：手动升级 TOS 7.0.0747，第一阶段显示成功；重启后网页打开是初始化 / 安装页面，只能装回 TOS 6。

**排查命令与真实返回**（SSH linyb@TNAS）：

① 确认引导模式：

[ -d /sys/firmware/efi ] && echo "UEFI 启动" || echo "Legacy (BIOS/CSM) 启动"

\# → UEFI 启动

② 系统盘布局（内置 U 盘运行期不可见）：

lsblk -o NAME,SIZE,TRAN,MODEL,MOUNTPOINT

\# → sda/sdb 两块 1.7T SATA 系统盘（sda1/sdb1 285M 引导分区，sda2/sdb2=md9 挂 /），无任何 USB 设备

③ BIOS 固件来源：

dmesg | grep -i -E "usb|efi" | head -40

\# → [0.000000] efi: EFI v2.50 by American Megatrends

④ BIOS 启动项表（决定性证据）：

efibootmgr -v 2>/dev/null

\# → BootCurrent: 0001 / BootOrder: 0001

\# → Boot0001* UEFI:  USB DISK 2.0 DL17, Partition 1 PciRoot(0x0)/Pci(0x15,0x0)/USB(3,0)/...

**判定**：机器唯一引导路径 = 内置 USB Initboot（UEFI），升级包无渠道刷它 → 必须手动刷 TOS7 版 U 盘镜像。

## 问题 2：先刷哪个镜像（UEFI / Legacy）—— 已闭环

官方机型表给 F4-225 配 **Legacy 230MB**（BIOS MAPL0304V16 命中官方区间）；实测引导路径为 **UEFI** → 以实测为准，**UEFI 版优先、Legacy 备选**，新 U 盘 + 空盘安全试错。最终成功。

## 问题 3：6→7 正式升级成功 + 7→7 新机制实证

**16:10 日志（update2026-10-30-16-10-53.log）——6.0.794 → 7.0.0747，成功**

关键行（注意：**安装器行为与 5 月 / 7 月失败时完全一致**）：

All files verified successfully!

Current system version  = TOS_X642.0_6.0.794

Update package version  = TOS_X642.0_7.0.0747

Current kernel version  = 6.1.120+          ← TOS6 内核

tos7 update kernel → sda1/sdb1 为引导分区

filesystem type: ext4                        ← 引导分区已是 ext4（印证 5 月两版日志之间 ext2→ext4 的转换）

Delete .../vmlinuz-6.12.41+tos-amd64 → exit status 1   ← 仍删"不存在"的 TOS7 内核

exec: tar --no-same-owner -xvf boot/grub.bz2           ← 仍只写 grub/EFI，无 vmlinuz/initrd

**结论 A**：同一安装器、同样 "只写 grub/EFI 不写内核" 的行为 —— 这次成功，差异**只有 U 盘**。正面证明：缺的内核由新 TOS7 U 盘在开机第二阶段补上（16:22 时盘上已存在 6.12.41 版本内核文件，见下），旧 U 盘加载不了 → 回安装页。早期 "新内核依赖重启后第二阶段安装" 的判断被证实。

**16:22 日志（update_before_reboot_2026-10-30-16-22-40.log）——7.0.0747 → 7.0.1341，成功**

这是 TOS7 **原生更新器**（不再是 install 工具），关键行：

Boot version: MAPL0304V16                     ← 更新器读取 BIOS/Initboot 版本，不要求改动

System version: 7.0.0747 → package 7.0.1341

checkKernelVersion: current kernel version: 6.12.63+   ← TOS7 运行内核

Starting kernel update (tos7 -> tos7)...

updateKernelX86: tosloader file found at /update/boot/.tosloader

found GRUB partition at /dev/sda1 (ext4)

updateBootFiles: cleaned up legacy kernel files (6.12.41+tos-amd64)  ← 清掉 6→7 第二阶段留下的旧内核

updateBootFiles: updated vmlinuz, /update/boot/vmlinuz -> /tmp/bootdev/boot/vmlinuz

updateBootFiles: updated initrd.img, /update/boot/initrd.img -> /tmp/bootdev/boot/initrd.img

all devices processed, kernel update finished

**结论 B（重要修正 / 细化）**：**进入 TOS7 后，TOS7→TOS7 的更新会自己把 vmlinuz + initrd 直接写进盘上引导分区**—— 系统回到 "自洽" 状态，U 盘不再需要动。也就是说：**"刷 U 盘" 只在 TOS6→TOS7 这个跨代边界需要做一次；之后 TOS7 内部升级（如本次 7.0.1341）不依赖 U 盘**。这比之前 "每次大版本都要刷" 更精确。

## 六份日志对照总表

表格

|       |                 |                               |                                                                                                     |                           |                                      |
|-------|-----------------|-------------------------------|-----------------------------------------------------------------------------------------------------|---------------------------|--------------------------------------|
| #    | 日志            | 升级路径                      | 安装器行为                                                                                          | 结果                      | 定位作用                             |
| 1     | 01-10           | 6.0.783→6.0.794               | tos6 updateKernel updateImage **写内核**到 sda1/sdb1；带 Asmedia 固件刷写工具（本机无此硬件，跳过） | 成功                      | 同代升级系统自洽，U 盘不用动         |
| 2     | 05-11 18:40     | 6.0.794→7.0.0517（beta）      | tos7 update kernel **只写 grub/EFI**；缺 INFO 报错                                                  | 失败回安装页              | 与正式版失败模式一致                 |
| 3     | 05-11 19:18     | 6.0.794→7.0.0517（beta 重试） | 同上；sda1 已变 ext4                                                                                | 失败回安装页              | 同上                                 |
| 4     | 07-04           | 6.0.794→7.0.0747（正式）      | 校验通过；kernel versions=[]；**只写 grub/EFI**                                                   | 失败回安装页              | 正式版与 beta 一致 → 问题不在安装包  |
| **5** | **10-30 16:10** | **6.0.794→7.0.0747（正式）**  | **同上，只写 grub/EFI**                                                                             | **成功（U 盘已刷 TOS7）** | **同一行为不同结果 → 差异只在 U 盘** |
| **6** | **10-30 16:22** | **7.0.0747→7.0.1341**         | **新更新器：写 grub/EFI + 写 vmlinuz + 写 initrd**                                                  | **成功**                  | **TOS7 内部更新自洽，U 盘不再依赖**  |

## 排除清单（维持不变）

表格

|                      |                                                                    |
|----------------------|--------------------------------------------------------------------|
| 候选原因             | 排除依据                                                           |
| 硬盘 / 阵列故障      | 盘阵正常（md9=/、md0 数据卷），官方同案确认非硬盘故障              |
| 升级包损坏           | 正式版校验通过；与 beta 失败模式一致；今日成功版与失败版同包同行为 |
| 安装器执行错误       | 5 次尝试行为一致（今日成功版与 4 次失败版完全相同），差异仅在 U 盘 |
| BIOS 需要更新        | 16:22 更新器读 MAPL0304V16 并正常继续；F4-225 不支持改启动顺序     |
| 缺 INFO 文件（beta） | 正式版无此问题仍失败，非根因                                       |

## 一句话总结

> **"刷 U 盘" 是跨代边界（TOS6→7）的一次性必要动作**：旧安装器只写盘上 grub/EFI、不写内核，内核靠新 U 盘在开机第二阶段补上（今日两日志互相印证：16:10 只写 grub/EFI + 16:22 清理到 6.12.41 遗留内核）；**进入 TOS7 后系统更新自动写 vmlinuz/initrd，U 盘不再需要动**。整条链：现象（回安装页）→ 日志（只写盘不写 U 盘）→ 实机（唯一引导项 = U 盘）→ 官方（旧 U 盘旧内核）→ 处置（刷 TOS7 U 盘镜像）→ 今日成功实证。

[铁威马 F4-225信息 约等于F4-221](f4-225-info.md)

[删除铁威马img镜像后面的110MB空分区，只保留120MB分区，让U盘够空间刷入](trim-120mb.md)
