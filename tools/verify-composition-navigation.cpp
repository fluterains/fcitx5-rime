// SPDX-License-Identifier: LGPL-2.1-or-later
// Real librime navigation regression, using a disposable deployed schema.
#include <rime_api.h>
#include <cassert>
#include <cstring>
#include <iostream>
int main(int argc, char **argv) {
    assert(argc == 2);
    auto *a = rime_get_api();
    RIME_STRUCT(RimeTraits, traits);
    traits.shared_data_dir = "/usr/share/rime-data";
    traits.user_data_dir = argv[1]; traits.app_name = "rime.composition-test";
    traits.min_log_level = 3; traits.log_dir = "";
    a->setup(&traits); a->initialize(&traits);
    auto s = a->create_session(); assert(s && a->select_schema(s, "rime_ice"));
    a->set_option(s, "ascii_mode", false);
    assert(a->get_option(s, "_linear"));
    auto index = [&] {
        RIME_STRUCT(RimeContext, c); assert(a->get_context(s, &c));
        assert(c.menu.num_candidates == 7);
        int n=c.menu.highlighted_candidate_index; a->free_context(&c);return n;
    };
    for (char k : std::string("nihao")) a->process_key(s,k,0);
    assert(std::strcmp(a->get_input(s), "nihao") == 0);
    assert(a->get_caret_pos(s) == 5 && index() == 0);
    a->process_key(s,0xff51,0); // Left enters pinyin immediately.
    assert(a->get_caret_pos(s) < 5 && index() == 0);
    for (int i=0;a->get_caret_pos(s)<5 && i<10;++i) a->process_key(s,0xff53,0);
    assert(a->get_caret_pos(s)==5 && index()==0);
    a->process_key(s,0xff53,0); assert(index()==1);
    a->process_key(s,0xff51,0); assert(index()==0);
    a->process_key(s,0xff51,0); assert(a->get_caret_pos(s)<5);
    a->process_key(s,0xff54,0); assert(a->get_option(s,"_linear"));
    a->process_key(s,0xff52,0); assert(a->get_option(s,"_linear"));
    a->clear_composition(s);
    for(char k:std::string("nihao"))a->process_key(s,k,0);
    a->process_key(s,'2',0);
    RIME_STRUCT(RimeCommit, c);assert(a->get_commit(s,&c));assert(c.text&&*c.text);
    a->free_commit(&c);a->destroy_session(s);a->finalize();
    std::cout << "PASS: native Left/Right edit and select; Up/Down do not toggle modes; seven candidates; numeric commit\n";
}
