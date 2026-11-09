# 拼音编辑与候选选择的两种高亮

Rime 的 `_linear` 选项作为唯一的模式来源：

| `_linear` | 方向键 | 当前候选 |
| --- | --- | --- |
| 未设置或 false | 左右移动拼音插入点；↓ 进入选词 | 低对比灰色背景，保留可读文字 |
| true | 左右移动候选；↑ 返回拼音编辑 | 主题原有高亮背景及选中文字颜色 |

候选索引始终使用 Rime 返回的 `highlighted_candidate_index`，不隐藏索引，
也不在插件中模拟方向键或维护第二份模式状态。七个候选、水平布局仍由原配置决定。
模式在当前 Rime 会话中保持，直到按 ↑ 关闭；本功能不强制在每次上屏后重置。

## 构建与配置

本功能包含 fcitx5-rime 和配套 Fcitx5 Classic UI 修改：

```sh
docker buildx build --output type=local,dest=out/linear-highlight -f Dockerfile.build .
docker buildx build --output type=local,dest=out/linear-highlight -f Dockerfile.build-classicui .
```

把 `data/rime-ice-linear.custom.yaml` 中的两条追加绑定合并到实际
`rime_ice.custom.yaml` 的 `patch` 中，再重新部署 Rime。
不要用示例文件覆盖已有的 custom 配置。

Classic UI 补丁基于上游 Fcitx5 5.1.7，保留 X11 和 Wayland 绘制后端。
只需安装生成的 `libclassicui.so`，不替换 Fcitx5 核心共享库。
灰色高亮复用当前主题高亮图片的 alpha 形状，保持圆角、间距和 DPI；
灰色强度和文字从当前主题颜色计算，所以支持深浅色自动切换。
选词模式直接使用主题原本的高亮图片、背景及文字颜色。

## 插件与 UI 的约定

`src/rimecandidateformat.h` 和 Classic UI 补丁约定使用文本格式位 `1 << 9`
作为私有 `MutedHighlight` 扩展。只修改带有此标志的候选渲染，其他输入法
保持原来的绘制行为。未打补丁的 UI 会忽略该标志并显示原主题高亮；
IBus、Kimpanel 等外部候选界面也不会自动获得这个效果。
未来升级 Fcitx5 时需要检查该位是否仍未被上游使用，重新基于匹配版本构建。

本功能不改变候选排序、数字选词、鼠标点击或翻页，也不恢复 Caps Lock 的 A 标签。
分发或迁移时必须同时携带 Rime 插件、匹配版本的 Classic UI 补丁和键位配置。

## Ubuntu 24.04 安装包

可以用 `tools/package-linear-highlight.py` 把构建结果放入对应版本的基础 deb，
生成文件名带 `+linear1` 后缀的本地包及 SHA256SUMS。Classic UI 包只替换
`fcitx5-modules` 中的绘制插件，其他模块保留发行版文件。
由于 fcitx5 及开发包对 modules 有精确版本依赖，modules 包内部版本号保持
`5.1.7-1build3`，通过 `X-Local-Variant: linear-highlight-1` 字段标记本地重建；
Rime 包版本添加 `+linear1`。安装本地 deb 会替换原 modules 包。

```sh
python3 tools/package-linear-highlight.py \
  --rime-base out/fcitx5-rime_5.1.4-2build2+patched.1_amd64.deb \
  --modules-base out/linear-highlight/fcitx5-modules_5.1.7-1build3_amd64.deb
sudo apt install ./out/linear-highlight/fcitx5-rime_*+linear1_amd64.deb \
                 ./out/linear-highlight/fcitx5-modules_*+linear1_amd64.deb
```

修改后的模块依赖本机匹配的 Fcitx5 5.1.7 ABI；不应直接用于其他发行版版本。
系统更新可能替换本地包，届时应针对新版本重新构建。

`tools/verify-linear-mode.cpp` 是对真实 librime 的集成验证，使用隔离的用户目录
和已部署的雾凇方案，验证七候选、拼音插入点移动、上下切换模式、左右选词及数字上屏。
