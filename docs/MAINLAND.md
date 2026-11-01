# 中国大陆可用性核查

核查日：2026-11-01。结论是“技术路线具备使用条件；大陆全链路未实测”，不是“下载后任何大陆网络均保证成功”。本机当前的网络探测不代表中国大陆电信、联通、移动或公司网络。

## 理论判断

理论上可行。当前实现把 UI 树读取、点击和画面传输放在 Windows 与 iPhone 的 USB 链路上；已经运行的桥接服务不需要海外远控服务器。本机已验证 Windows 原生 userspace tunnel、XCTest/WDA 和 USB 画面路线，未发现本地控制必须在境外进行的技术前提。

这一判断不能推导出所有大陆网络都能完成首次配置。软件获取、Apple 账号签名与信任、开发镜像下载/个性化处理，以及后续续签，仍取决于相关服务器在当地的实际可达性、账号状态和设备兼容性。把安装文件提前拷入电脑能减少下载依赖，不能替代 Apple 在线验证。

这也不等于必须改成海外 Apple 账号或切换 App Store 地区。商店地区决定应用获取范围，WDA 开发签名是另一条流程；不把切换地区当作本地 USB 控制的安装步骤，实际签名资格以 Apple 响应为准。助手服务本身在当地能否使用，同样独立于手机 USB 桥。

安装前提与操作注意事项集中在 [PREREQUISITES.md](PREREQUISITES.md)。

| 环节 | 依赖 | 当前处理 / 未完成项 |
|---|---|---|
| 下载套件 | GitHub Release 及其资产域名 | 本地提供完整 ZIP，可通过用户自己的合规文件分发渠道传递；GitHub 本身不构成大陆下载稳定性的保证 |
| Python、控制程序、go-ios | 包内固定文件 | 离线安装、SHA-256 校验；不临时访问 pip、GitHub raw |
| Apple USB 驱动 | Apple 官网、Windows 安装权限 | 官方安装器；已有组件检测；不能用驱动下载成功冒充已配对 |
| Sideloadly | sideloadly.io、更新或 Anisette 依赖 | 固定安装器哈希；Local Anisette 可减少远程服务依赖，但仍须在当地测试；不自动切换账号验证方式 |
| 爱思助手（替代签名） | i4.cn 官方下载及 Apple 签名服务 | 已加入[替代指南](AISI-SIGNING.md)；当前 WDA 签名、XCTest 启动及到期续签尚未实测 |
| Apple 登录、签名、信任 | Apple 服务、账号状态、两步验证 | 每位使用者亲自操作自己的账号；不能制作跨设备通用的已签名 WDA |
| 开发镜像 DDI | 当前库的 raw.githubusercontent.com/doronz88/DeveloperDiskImage 路径；Apple TSS | 首次挂载仍可能联网；不公开打包 Apple 开发镜像或别人的个性化票据。断网的首次挂载不受保证 |
| 已启动后的 UI 树、点击、画面 | USB、Apple 设备服务、运行中的 WDA | 不使用云控中转；实际手机 App 的联网另行计算 |
| 免费续签 | Sideloadly 与 Apple 服务 | 约 7 天一次；同账号覆盖续签。自动刷新与跨周期稳定性待实测 |
| 助手本身 | 用户所选 AI 服务 | 本地手机桥不等于 AI 服务在大陆可用；手动网页控制不依赖 AI 登录 |

## 当地验收方法

在一台没有本套件的 Windows x64 电脑上，以实际大陆网络运行，记录运营商/大致地区（不收集公网 IP）：

1. 完整下载安装 ZIP、核对 ZIP SHA-256，离线执行 Install。
2. 安装 Apple 组件与所选签名工具；USB 配对；用自己的账号首次签名，完成开发者模式及信任。爱思与 Sideloadly 分别记录结果。
3. 运行 Doctor -Network；另外实际完成 DDI 首次下载、挂载及 XCTest 验证。HEAD/端口探测不能代替此步骤。
4. 验证原生 XML、点击、滑动、截图和持续画面；拔插 USB 后恢复；手机重启后恢复。用非敏感页面测试。
5. 至少跨过一次免费签名到期周期，确认续签后恢复；记录人工参与步骤。

只有这些项目有当地实测记录后，才能把某个已测试组合标为大陆可用。遇到网络错误保留域名和错误类型，不使用来历不明的下载镜像，不关闭 TLS 校验，也不修改系统安全保护。

## 一手依据

- [Sideloadly 官方页面](https://sideloadly.io/) 与 [FAQ](https://sideloadly.io/faq.html)：Windows 组件、免费签名期限、刷新和 Anisette 条件。
- [go-ios v1.3.2](https://github.com/danielpaulus/go-ios/tree/v1.3.2)：Windows 原生设备与 XCTest 路线。
- [pymobiledevice3](https://github.com/doronz88/pymobiledevice3)：设备协议；本包锁定 11.49.1，具体 DDI 地址已从随包源码核对。
- [Python Windows 发布](https://www.python.org/downloads/windows/)：便携 Python 官方来源。
- [Apple 开发者模式](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device)：系统要求。
