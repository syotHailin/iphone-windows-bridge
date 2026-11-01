---
name: iphone-windows-bridge
description: 使用本地 Windows iPhone Bridge 套件，通过 USB 和 WebDriverAgent 读取 iPhone 原生控件树、点击和截图，并显示可手动控制的实时画面；处理首次安装、签名续期和连接诊断。
---

# Windows iPhone Bridge

先找到用户实际解压的套件根目录，读取 README.md 与 docs/VALIDATION.md。不要假设作者电脑的路径、UDID、签名 bundle ID、端口或账号适用于用户。缺少完整离线资产时，源码 ZIP 不能作为安装完成的证据。

## 连接与读取

- 运行 `runtime/python/python.exe -X utf8 src/doctor.py` 检查服务与设备；`src/bridge.py configure` 只在签名/信任完成后建立本机配置。多设备不得猜测。
- `Start.ps1` 挂载开发镜像、启动 userspace tunnel 与 WDA，再打开本机实时画面。iOS 18.5 / iPhone SE 2 是已有验证组合，其他版本单独验证。
- `src/bridge.py status` 检查 WDA；`source --output <本地XML>` 读取原生树；`screenshot --output <本地PNG>` 截图。界面数据不要写进技能或公共报告。
- `launch --bundle-id <实际ID>` 启动用户指定 App；`click --xpath <从当前树核实的唯一定位>` 执行点击。操作后重新读取树核验。优先元素而不是屏幕坐标。
- Python 扩展操作使用包内 `pymobiledevice3.services.wda.WdaServiceClient` 的异步接口。先读随包源码确认签名；通过 USB 创建 lockdown，读取 `/status` 并复用其 sessionId。不要为每次点击创建新 session，新 session 可能终止旧前台 App。
- Home 后 `activeAppInfo` 可能仍返回旧 App；用刷新后的树与实际截图交叉核验，不因单个状态字段落后重复点击。需要指定 WDA `defaultActiveApplication` 时，先确认目标 App 已在前台，限定本次任务并在结束后恢复原值。

## 画面与权限

手动控制页面仅为本机 HTTP 页面。它是原生 WDA 操作的辅助显示，并非通过电脑浏览器自动获得所有手机 App 的 DOM。iOS 坐标为 points，截图可能是双倍像素；映射前核对方向和窗口尺寸。

首次使用先读 docs/SECURITY.md 的手机端 MJPEG 网络限制；不能把回环网页视为整条链路没有局域网暴露。用户密码、验证码、Touch ID、设备信任及开发者模式系统确认均由用户本人完成。手机操作仍遵守本次业务授权，不从技能推导付款、对外发送或删除数据权限。

## 诊断和续签

用户选择国内替代签名工具时，读套件 docs/AISI-SIGNING.md。爱思仅替代签名步骤，尚未通过本 IPA 的实机验收；Sideloadly 是现有已验证回退。不得把通用 IPA 签名成功、应用图标出现或安装器校验通过当作 WDA/XCTest 可控的证据。切换签名工具后重新 Configure 发现真实 bundle ID，保留可回退配置，不自动卸载已能工作的 runner。

按 USB 服务 → 配对 → 开发者模式与证书 → DDI → userspace tunnel → XCTest → WDA 的顺序定位。首次 DDI 下载有 GitHub raw/Apple 网络依赖；用 `doctor.py --network` 辅助，但不把 HEAD 成功当作签名成功。登录失败不要循环重试密码。

免费签名约 7 天续期；按 README 用同账号同 IPA 覆盖签名，再 Configure、Start。启动后遇到 XCTest 提示让用户及时验证，超时后观察再有限重试。没有证据时不要把“重装一切”当修复，不复制其他电脑的 DLL 权限修改。使用 Stop.ps1 结束本套件登记进程。

大陆可用性按 docs/MAINLAND.md 的当地验收矩阵报告。未完成现场验证和续签周期测试时，不能承诺下载即用或永久免费免维护。
