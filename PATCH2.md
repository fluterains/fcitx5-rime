# Fcitx5 Rime 5.1.4 Patch2

基于官方 fcitx5-rime 5.1.4，累计包含 Patch1 的托盘定制。本次正式发布替代
本机的 `5.1.4-2build2+patched.1+linear3` 开发包，正式包版本为
`5.1.4-2build2+patched.2`，变体标记为 `patch2`。

## 功能与范围

- 保留中文界面的“中／英”和英文界面的“zh／en”托盘文字。
- 输入法菜单保留方案全名；英文状态显示英文模式。保留 Patch1 移除 Caps Lock
  “A”覆盖的决定，Caps Lock 的输入行为仍由 Rime 和系统处理。
- 新增“原始输入字母”（Raw input）预编辑模式：应用收到原始拼音和对应光标位置，
  候选框仍显示 Rime 格式化后的拼音。此模式始终使用真实输入光标，不使用
  PreeditCursorPositionAtBeginning 把它固定到开头。
- 通过示例启用 Rime 原生 `_linear` 左右导航：第一个候选按左键进入拼音编辑；
  拼音末尾再按右键进入候选选择。上下键保持方案原有行为。
- 提供七候选和单引号拼音分隔符配置示例，供合并到雾凇拼音配置。
- 不包含已放弃的上下键切换编辑模式或灰色候选高亮原型。

候选框稳定绘制、宿主窗口跟随和边缘避让由独立的
[Fcitx5 5.1.7 Patch1](https://github.com/fluterains/fcitx5/releases/tag/v5.1.7-patched.1)
提供。配置窗口适配由独立的
[Configtool 5.1.4 Patch1](https://github.com/fluterains/fcitx5-configtool/releases/tag/v5.1.4-patched.1)
提供。本仓库不再携带 Fcitx5 核心的试验补丁或构建脚本。

## 安装与个人配置

下载本 Release 的 deb，在 Ubuntu 24.04 amd64 上安装：

```sh
sudo apt install ./fcitx5-rime_5.1.4-2build2+patched.2_amd64.deb
systemctl --user restart app-org.fcitx.Fcitx5@autostart.service
```

本包使用 Ubuntu 24.04 的 Fcitx5 5.1.7 和 librime 1.10.0 ABI；其他发行版应按
本机依赖重新构建。它不捆绑雾凇词库、主题或个人数据，也不会覆盖用户配置。

示例位于 `examples/`，并作为单独的配置示例附件发布：

1. 将 `rime.conf` 中两项合并到 `~/.config/fcitx5/conf/rime.conf`。
2. 将 `default.custom.yaml` 中七候选设置合并到 Rime 的同名 custom 文件。
3. 将 `rime_ice.custom.yaml` 的补丁合并到现有雾凇方案 custom 文件；如还保留旧的
   Down/Up 对 `_linear` 的 set_option/unset_option 绑定，删除这两条旧绑定。
4. 重新部署 Rime。已有 `_linear` switch 时不要重复追加。

配置文件中同一层只应有一个 `patch:`，合并其内容即可。不要用示例整文件替换
已有个人配置。主题、横排候选和托盘描边仍由 Fcitx5 Classic UI 配置控制。

## Docker 构建、打包与测试

```sh
docker buildx build -f Dockerfile.build --output type=local,dest=out/patch2 .
apt download fcitx5-rime=5.1.4-2build2
python3 tools/package-patch2.py fcitx5-rime_5.1.4-2build2_amd64.deb \
  out/patch2/fcitx5-rime-5.1.4-patched.2-runtime.tar.gz \
  out/patch2/fcitx5-rime_5.1.4-2build2+patched.2_amd64.deb
fixture=$(mktemp -d)
cp tests/fixtures/* "$fixture/"
out/patch2/verify-navigation "$fixture"
mkdir -p out/patch2/root
tar -xzf out/patch2/fcitx5-rime-5.1.4-patched.2-runtime.tar.gz -C out/patch2/root
RIME_PATCH2_PLUGIN="$PWD/out/patch2/root/usr/lib/x86_64-linux-gnu/fcitx5/librime.so" \
FCITX_ADDON_DIRS="$PWD/out/patch2/root/usr/lib/x86_64-linux-gnu/fcitx5:/usr/lib/x86_64-linux-gnu/fcitx5" \
  /usr/bin/python3 tests/verify-preedit.py
```

打包脚本要求 Ubuntu 原始 5.1.4-2build2 amd64 包及 Python 3.12，重新计算文件校验值，
保留发行版依赖。构建产物包含运行文件和导航验证程序，不打包测试程序到运行 deb。
预编辑测试自动启动独立 Xvfb、D-Bus 和临时 Rime 数据目录；依赖系统 fcitx5、
python3-dbus、Xvfb、xauth 及 librime。使用微型测试词典，不读取个人用户词库。
验证原始字母、光标、左右导航、七候选、数字上屏、取消和中英文状态切换。
这些测试不等同于原生 Wayland 或每种应用的兼容性验证。

## 提交组织

从正式 Patch1 标签出发：一个提交加入 Raw input 功能和翻译；另一个提交加入
构建、打包、配置示例及测试。历史试验分支保留，Release 不带旧的临时核心补丁。
