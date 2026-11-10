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

配套 Classic UI 修改维护在 `fluterains/fcitx5` 的
`4fa62ba2fae3de3dd1c44a4f94260e7cf558cfc3` 提交中，基于 Fcitx5 5.1.7：
一次 Rime 组合开始时记录锚点；输入字母、左右移动光标、切换候选时保持该锚点。
清空、上屏、切换输入上下文后重新取位置。屏幕边缘仍保留原有的防溢出处理。
应用上报的光标矩形不被改写，因此应用内的光标可以正常移动。

这项定位修改不覆盖 Kimpanel、应用自绘候选框或由 Wayland 合成器定位的面板。
X11、Wayland 绘制后端都保留编译，但本次只在独立 X11 会话验证定位。

## 构建与安装

```sh
docker buildx build --output type=local,dest=out/stable-composition-7 -f Dockerfile.build .
docker buildx build --output type=local,dest=out/stable-composition-7 -f Dockerfile.build-classicui .
python3 tools/package-linear-highlight.py --revision 7 \
  --build-dir out/stable-composition-7 \
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

## 实时伸缩与稳定画布（linear7）

候选背景仍按当前布局实时增宽、缩窄，不保留上一段或本段的最大可见宽度。
变化的只是绘制后的可见区域，不再是 X11 顶层窗口的几何尺寸。

X11 候选窗在首次显示时建立一个显示器宽度、当前内容高度的固定画布。
每次候选内容更新仍会重绘，因为文字和背景像素确实已经改变；但在另一张
pixmap 中画完整下一帧后，只通过一次 CopyArea 更新画布中的可见区域。
画布右侧保持透明，并通过 X Shape input region 限定为当前可见宽高，
不会拦截其后的鼠标点击。

由于顶层窗口不再逐键 resize，合成器不会先收到窗口尺寸变化、显示新暴露的
透明区域，再等待下一次绘制补上内容。输入过程中的宽度变化只产生一个完整的
新像素帧，不再产生空白或旧内容的中间帧。Expose 直接复制缓存帧，也不重新
计算布局。

```sh
docker buildx build --output type=local,dest=out/canvas-resize-7 -f Dockerfile.build-classicui .
python3 tools/package-linear-highlight.py --modules-only --revision 7 \
  --build-dir out/canvas-resize-7 \
  --modules-base out/linear-highlight/fcitx5-modules_5.1.7-1build3_amd64.deb
```

独立 X11/GTK 验证中，顶层画布保持 `1920x78`，X Shape 可见宽度仍按
`434 -> 527 -> 449 -> 467` 实时变化；输入过程中没有 width resize。
固定锚点、原始字母光标、左右导航、提交、取消及 ClearArea 像素完整性测试通过。
该自动化检查不等同于 Mutter 下的逐帧录像，最终仍需在实际桌面确认合成效果。
