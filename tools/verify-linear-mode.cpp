// SPDX-License-Identifier: LGPL-2.1-or-later
// Integration test against a deployed rime_ice schema in an isolated user dir.
#include <rime_api.h>
#include <cassert>
#include <iostream>
#include <string>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    auto *api = rime_get_api();
    RIME_STRUCT(RimeTraits, traits);
    traits.shared_data_dir = "/usr/share/rime-data";
    traits.user_data_dir = argv[1];
    traits.app_name = "rime.linear-mode-test";
    traits.min_log_level = 3;
    traits.log_dir = "";
    api->setup(&traits);
    api->initialize(&traits);
    const auto session = api->create_session();
    assert(session && api->select_schema(session, "rime_ice"));
    api->set_option(session, "ascii_mode", false);
    assert(!api->get_option(session, "_linear"));
    for (char key : std::string("nihao")) api->process_key(session, key, 0);
    auto index = [&]() {
        RIME_STRUCT(RimeContext, context);
        assert(api->get_context(session, &context));
        assert(context.menu.num_candidates == 7);
        auto result = context.menu.highlighted_candidate_index;
        api->free_context(&context);
        return result;
    };
    assert(index() == 0);
    const auto originalCaret = api->get_caret_pos(session);
    api->process_key(session, 0xff51 /* Left */, 0);
    const auto leftCaret = api->get_caret_pos(session);
    assert(leftCaret < originalCaret);
    api->process_key(session, 0xff53 /* Right */, 0);
    assert(api->get_caret_pos(session) > leftCaret);
    api->clear_composition(session);
    for (char key : std::string("nihao")) api->process_key(session, key, 0);
    assert(api->process_key(session, 0xff54 /* Down */, 0));
    assert(api->get_option(session, "_linear"));
    const auto first = index();
    api->process_key(session, 0xff53 /* Right */, 0);
    assert(index() == first + 1);
    assert(api->get_caret_pos(session) == originalCaret);
    api->process_key(session, 0xff51 /* Left */, 0);
    assert(index() == first);
    assert(api->process_key(session, 0xff52 /* Up */, 0));
    assert(!api->get_option(session, "_linear"));
    api->process_key(session, 0xff51 /* Left */, 0);
    assert(api->get_caret_pos(session) < originalCaret);
    // A non-first candidate must still be selected by the number key.
    api->clear_composition(session);
    for (char key : std::string("nihao")) api->process_key(session, key, 0);
    api->process_key(session, 0xff54 /* Down */, 0);
    api->process_key(session, 0xff53 /* Right */, 0);
    RIME_STRUCT(RimeContext, context);
    assert(api->get_context(session, &context));
    std::string expected = context.menu.candidates[1].text;
    api->free_context(&context);
    api->process_key(session, '2', 0);
    RIME_STRUCT(RimeCommit, commit);
    assert(api->get_commit(session, &commit));
    assert(expected == commit.text);
    api->free_commit(&commit);
    api->destroy_session(session);
    api->finalize();
    std::cout << "PASS: 7 candidates; edit caret; Down/Up mode; Left/Right selection; numeric commit\n";
}
