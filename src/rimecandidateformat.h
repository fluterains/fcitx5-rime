// SPDX-License-Identifier: LGPL-2.1-or-later
#ifndef FCITX_RIME_CANDIDATEFORMAT_H
#define FCITX_RIME_CANDIDATEFORMAT_H

#include <fcitx-utils/textformatflags.h>

namespace fcitx {
// Private extension shared with patches/fcitx5-5.1.7-muted-highlight.patch.
// Stock UIs ignore this bit and retain their normal theme rendering.
constexpr auto RimeMutedHighlight = static_cast<TextFormatFlag>(1 << 9);
} // namespace fcitx

#endif
