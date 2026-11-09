# 稳定的拼音预编辑与候选窗定位

当前行为使用 Rime 原生线性导航（`_linear` 默认启用）：

- 输入末尾按 → 选择下一个候选，按 ← 返回前一个候选。
- 在第一个候选按 ← 进入拼音编辑；光标未到末尾时，左右键移动拼音光标。
- 到拼音末尾后，再按 → 进入候选选择。
- 上下键保留 Rime 原有行为，不切换额外模式。
- 候选统一使用当前 Catppuccin 主题高亮，不再区分灰色、紫色两种模式。

## 应用内预编辑

新增 `PreeditMode="Raw input"`（中文选项为“原始输入字母”）：
应用收到 Rime 的原始输入字母及对应的光标位置，不再收到候选汉字预览。
候选框拼音栏仍使用 Rime 的格式化预编辑，例如应用内 `nihao`、候选栏 `ni'hao`。
两处光标对应相同的输入位置，显示的字节偏移可能因分隔符不同而不同。
`PreeditCursorPositionAtBeginning=False` 保留可移动的预编辑光标。

## 固定候选窗锚点

配套 Classic UI 补丁基于 Fcitx5 5.1.7，只修改 X11 候选窗定位：
一次 Rime 组合开始时记录锚点；输入字母、左右移动光标、切换候选时保持该锚点。
清空、上屏、切换输入上下文后重新取位置。屏幕边缘仍保留原有的防溢出处理。
应用上报的光标矩形不被改写，因此应用内的光标可以正常移动。

这项定位修改不覆盖 Kimpanel、应用自绘候选框或由 Wayland 合成器定位的面板。
X11、Wayland 绘制后端都保留编译，但本次只在独立 X11 会话验证定位。

## 构建与安装

```sh
docker buildx build --output type=local,dest=out/stable-composition-3 -f Dockerfile.build .
docker buildx build --output type=local,dest=out/stable-composition-3 -f Dockerfile.build-classicui .
python3 tools/package-linear-highlight.py --revision 3 \
  --build-dir out/stable-composition-3 \
  --rime-base out/fcitx5-rime_5.1.4-2build2+patched.1_amd64.deb \
  --modules-base out/linear-highlight/fcitx5-modules_5.1.7-1build3_amd64.deb
```

安装这两个本地包后重新启动 Fcitx5。modules 包内部版本仍为 `5.1.7-1build3`，
以满足发行版的精确依赖，只有 `libclassicui.so` 与发行版 payload 不同。
文件名和 Rime 包保留历史 `+linear3` 修订后缀，该后缀不代表旧的上下切换功能。
不要把针对 5.1.7 编译的模块直接用于其他 ABI 版本。

把 `data/rime-ice-linear.custom.yaml` 中的隐藏开关追加项合并到实际 custom 的 patch 中，
删除旧 `Down -> set_option: _linear`、`Up -> unset_option: _linear` 两条绑定，重新部署。
不要覆盖已有 custom 文件。隐藏开关不带 states，不增加用户可见模式选项。

`tools/verify-composition-navigation.cpp` 验证真实 librime 的左右导航、七候选、
数字上屏及上下键不改变 `_linear`。界面验证使用隔离 D-Bus、Xvfb 和 GTK
IMMulticontext，检查原始字母、预编辑光标、输入过程中固定位置，以及提交后重新定位。
不接触真实用户词库。
