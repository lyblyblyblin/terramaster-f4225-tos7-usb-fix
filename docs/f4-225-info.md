# 铁威马 F4-225信息 约等于F4-221

铁威马 F4-225≈F4-221

在里面下载镜像是230MB的，但实际上后面有110MB分区是空的，让AI删除后，再使用rufus写入即可，为了兼容性铁威马 F4-225主板设置启动模式已经是UEFI+Legacy，直接UEFI不能启动 [USB Initboot Image(TOS 7 Legacy 230MB)](https://download2.terra-master.com/usb_initboot_legacy_2037.img) 这个镜像，并且升级U盘后，再进去看 TOS控面板>通用设置>系统>更新>BIOS/InitBoot位置查看BIOS版本 依然是 MAPL0304V16 ，也就是 MAPL0304V16 是主板的BIOS固件版本，而非U盘的版本信息，系统下可能没有地方能看U盘具体的版本信息

铁威马系统存在U盘系统与硬盘系统绑定关系，U盘系统过低无法启动硬盘系统，要对应升级

铁威马 F4-225 BIOS默认是legacy模式，里面自带的U盘128MB，而且是体积很小的那种U盘，假如更换不能换体积大的，只能体积小的更换

升级TOS6使用U盘镜像 USB_Initboot_UEFI-229.img 要切换到UEFI模式才能启动。 铁威马 Windows PC 上制作 TOS 的 USB 引导

使用TOS7使用U盘镜像（默认镜像大小230MB，里面有110MB空分区，要删除他才行，因为铁威马 F4-225自带U盘空间不够，只有128MB） [删除铁威马img镜像后面的110MB空分区](trim-120mb.md)

[USB Initboot Image(TOS 7 Legacy 230MB)](https://download2.terra-master.com/usb_initboot_legacy_2037.img)

适用机型：F2-221、F2-421、F4-221、F5-221、F5-421、F2-422、F4-422、F5-422

(此 8 个机种的 BIOS 版本必须为 MAPL0304V16 至 MAPL0304V22，或 MAPL0303V16 至 MAPL0303V22，可前往 TOS控面板>通用设置>系统>更新>BIOS/InitBoot位置查看BIOS版本。也可以在技术支持>问题反馈处收集系统报告, 下载, 解压, 找到device.txt并打开查看BIOS版本.)
