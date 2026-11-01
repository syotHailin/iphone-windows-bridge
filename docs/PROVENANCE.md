# 文件来源及处理

`dependencies.json` 记录包内离线资产的 SHA-256、大小与来源。它能发现损坏或意外修改，不能替代发布者签名。下载 ZIP 时还应比较 ZIP 旁的 SHA256 文件。

- Python：python.org 的 3.13.17 Windows x64 embeddable ZIP；本机已验证 python.exe 的 PSF Authenticode 签名有效。未修改 Python 二进制；安装时配置 `_pth`，加入套件 src 和 site-packages。
- Python 依赖：从 PyPI 下载 Windows CPython 3.13 wheels，在全新独立运行时用 `pip --no-index --find-links` 安装，再打包 site-packages；保留 `.dist-info`、license 文件，不包含原作者电脑运行环境。99 个项目的固定版本见 `requirements.lock.txt` 与 `licenses/python-dependencies.json`。GPL/LGPL 对应源代码压缩包位于 `vendor/corresponding-source`；打包时排除 pycache。
- go-ios：官方 v1.3.2 Windows ZIP，原始 SHA-256 `939c6bcaafed183a92afb9f79cc11b1f935fa6389bfc94d3902e3f52c4dff3fe`，保留 MIT 许可证。运行 userspace tunnel，不安装 Wintun 或修改系统32目录。
- WDA：go-ios 引用的 deviceboxhq 预编译 ZIP，原始 SHA-256 `448ffe591cf64abf7ff0751897b6860cd45b8032b39677a5dd79f827c4d781cc`。将 .app 包入 Payload，再仅移除 .dSYM 调试符号，避免 Sideloadly 对 DWARF 数据执行 Mach-O 签名。所有保留文件字节与原包一致；包内无个人签名、证书或 provisioning profile。最终 IPA SHA-256 `78ea6cb77175279feec337238a9c8bec22ada928f9ff8239b54154854927c95c`。
- WDA 的文件名包含 13.2.0，但实机 `/status` 报告 13.1.3。此记录保留差异，不把第三方构建说成 Appium 官方可复现构建。上游 BSD 许可证附于 licenses。
- 本项目新增 Python/PowerShell/文档与技能以 GPL-3.0-or-later 提供，第三方组件遵循其原许可证。二进制公开分发待办见 RELEASE-CHECKLIST，不能省略原生传递依赖的来源与许可核查。

未采集 Apple 密码、双重验证码、签名私钥或 Sideloadly 登录缓存。没有复制用户手机数据。公开源码和候选 ZIP 使用显式文件白名单生成。
