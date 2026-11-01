# Windows 控制 iPhone：本地安装套件

> **公开源码预览版**：此仓库提供控制程序、技能、安装辅助脚本及指南，尚未公开发布完整离线运行资产。GitHub 的 Source code ZIP 不能直接运行 Install.ps1；不要把源码下载成功当作安装完成。爱思签名路线尚未实机验收。详情见 [公开发布范围](docs/PUBLICATION.md)。

版本：0.1.0-rc1。面向 Windows 10/11 x64、USB 连接的真实 iPhone。电脑显示实时手机画面，可点击、拖动；助手通过 WDA 元素树定位和操作。无需 Mac、越狱或付费开发者会员。**免费签名需要约每 7 天续签，首次配置和续签需要联网。**

这是候选安装包，不是“中国大陆全网络保证可用”的产品。已实测的手机是 iPhone SE 2 / iOS 18.5；其他 iOS、干净 Windows、新账号首签、中国大陆运营商网络与七天到期续签尚未完成验收。详见 [验证记录](docs/VALIDATION.md) 和 [大陆可用性](docs/MAINLAND.md)。

**理论上可以在中国大陆使用。** 已启动后的控制链路是电脑 → USB → 手机 WDA，画面返回电脑本地页面，不需要海外远控服务器。这是根据实现与本机测试作出的技术判断，前提是当地能够完成软件获取、Apple 签名/信任与开发镜像准备。安装前先看 [安装前提与注意事项](docs/PREREQUISITES.md)。

签名有两条路线：**Sideloadly 为本机已验证路线；[爱思助手为新增替代路线](docs/AISI-SIGNING.md)，尚待 WDA 实机与到期续签验收。** 选择爱思时用该指南替代下面第 4—5 步，其余设备配置和控制步骤相同。

## 包内与前置软件

本地完整候选包内有便携 Python 3.13.17、锁定的 Python 依赖、go-ios 1.3.2、去除调试符号的未签名 WDA IPA、本地控制程序、中文技能与检查工具。离线安装这些组件，不修改系统 Python、PATH、防火墙或系统 DLL 权限。

Apple Mobile Device Support（随网页版 iTunes 安装）、所选签名工具（Sideloadly 或爱思）及其需要的 Apple 组件应从官方安装。它们不属于此项目开源授权。`Fetch-Prerequisites.ps1` 提供官方地址下载和校验，不自动执行。若拿到本机准备的 `private-prerequisites` 文件夹，可使用其中已校验安装器；不要把该目录上传到公开仓库。

## 初次安装

1. 将完整安装 ZIP 解压到可写目录，例如 `C:\iPhoneBridge`。不要从 ZIP 内直接运行，也不要使用 GitHub 的 “Source code.zip” 代替完整包。本机完整包包含前置安装器，预留至少 3 GB 空间。
2. 在该文件夹打开 PowerShell，执行 `powershell -NoProfile -File .\Install.ps1`。它先核对依赖 SHA-256，再离线解压运行环境。如果运行脚本被组织策略阻止，联系管理员；本套件不修改执行策略。
3. 安装[网页版 iTunes](https://www.apple.com/itunes/download/win64) 的 Apple 设备组件，连接手机并解锁，手机提示时点“信任”。iTunes 应能识别这台手机。已有可用组件不必卸载重装；有 Microsoft Store 版冲突时按 [Sideloadly FAQ](https://sideloadly.io/faq.html) 排查。需要 iCloud/Anisette 时使用官网列出的 Apple 组件；不要因此退出手机 iCloud。
4. 从 [Sideloadly 官网](https://sideloadly.io/) 安装 Windows x64 版。可运行 `powershell -NoProfile -File .\Fetch-Prerequisites.ps1 -Component Sideloadly` 下载；固定文件哈希不匹配时会停止，不会自动信任新版本。本机已测试 v0.72，安装器没有 Windows 数字签名。
5. 在 Sideloadly 中选择本手机，载入 `vendor\WebDriverAgent-13.2.0-no-dsym.ipa`。在软件里亲自输入 Apple 账号、密码、验证码，点击 Start，直到 Done。无需把账号交给助手。本项目不会读取 Sideloadly 凭据，也不会提供共享签名证书。第三方签名工具仍有账号信任成本，不能承诺零风险。
6. iPhone 设置 → 隐私与安全性 → 开发者模式，开启并按提示重启、解锁、确认开启。菜单没有出现时先完成设备识别和 WDA 安装，再检查；不要反复重置手机。
7. 设置 → 通用 → VPN 与设备管理，信任刚才自己的开发者账号。需要联网验证时按手机系统提示完成。
8. 执行 `powershell -NoProfile -File .\Configure.ps1`。自动识别唯一 USB 手机和已签名 WDA 的实际 bundle ID；多设备/多 WDA 会停止，不会猜测。可用 `-Udid` / `-BundleId` 明确指定。设备标识只存在 `%LOCALAPPDATA%\iPhoneWindowsBridge` 私有配置中。
9. 执行 `powershell -NoProfile -File .\Start.ps1`。首次挂载开发镜像可能下载较大文件。手机出现 XCTest / Enable UI Automation 时，及时亲自完成 Touch ID/密码验证。浏览器随后打开 `http://127.0.0.1:19101`，点击画面或拖动即作用于手机。
10. 在手机打开计算器，测试电脑点击一个数字，再测试滑动。确认画面确实更新后使用；遇到过期画面先重连。结束时运行 `powershell -NoProfile -File .\Stop.ps1`。

**网络与画面隐私：** 电脑网页只监听本机回环地址，但现有第三方 WDA 的手机端 MJPEG 服务未证明只监听回环地址。只在自己信任、具备客户端隔离的网络使用，或在设置中关闭手机 Wi-Fi 后通过 USB 使用（需要联网的手机 App 可用蜂窝数据）。不要在公共 Wi-Fi 上展示敏感画面。详见 [安全说明](docs/SECURITY.md)。

## 自检与续签

`powershell -NoProfile -File .\Doctor.ps1` 检查 Apple 服务、USB 和 WDA；加 `-Network` 检查安装所需部分站点。HTTP 可达不等于 Apple 登录或签名成功，也不证明你位于大陆网络。

免费签名失效后：先 Stop，使用原 Apple 账号与同一 WDA IPA 在 Sideloadly 中覆盖续签，再 Configure、Start。不要先删除 WDA 或换账号。Sideloadly 有自动刷新功能，但本套件尚未验证一次完整到期续签周期，不承诺后台自动续签稳定。

启动超时先检查手机是否解锁、开发者模式和信任是否开启、是否漏掉 XCTest 确认、证书是否过期。重启手机后开发镜像可能需要重新挂载。保留本地日志排查；不要上传含设备标识的原始日志。AMDS 1053 属于主机环境问题，本包不会套用另一台电脑的 DLL ACL 修复。

## 给助手安装技能

把 `skills\iphone-windows-bridge` 复制到使用者自己的技能目录（Codex 通常为 `%USERPROFILE%\.codex\skills`），重新打开会话。告诉助手此套件的实际解压路径。技能本身不携带设备配置，也不自动授权付款、发消息或删除数据。

## 升级与移除

升级先 Stop，在另一个目录解压新版本，再 Install、Configure。保留旧目录可回退。卸载先 Stop，再删除你解压的套件目录；需要清除私有配置时自行删除 `%LOCALAPPDATA%\iPhoneWindowsBridge`。Apple 组件、Sideloadly、手机上的 WDA 不会被批量卸载。

## 公开发布

公开仓库为 [syotHailin/iphone-windows-bridge](https://github.com/syotHailin/iphone-windows-bridge)，本次仅发布源码与技能预览。完整候选安装包仍以本地交付为准。运行库为候选离线快照；在上传二进制 Release 前完成 `docs/RELEASE-CHECKLIST.md`。不要上传 `runtime`、`private-prerequisites`、用户配置、账号缓存、截图或配对文件。
