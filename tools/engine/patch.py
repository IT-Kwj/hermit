#!/usr/bin/env python3
"""Hermit's additions in another nxnative checkout (upstream nxnative for Donkey Kong Bananza, pokopia-native's for Pokémon Pokopia), as hermit.py build applies them:

  - Mario Kart World's overlay (key 1) and settings panel (key 2): tools/engine/s2m_ui.m copied in, with the shared shader list's offer (tools/engine/s2m_share.m, a copy of hermit-builds' dm/host/s2m_share.m), two calls in front_mac.m, the file in the host's Makefile
  - the overlay's data: mtl_cur_frame (nvn_mtl.m) and nvn_game_size (hle_nvn.c), when the checkout lacks them
  - the "Performance overlay" row in the app's settings list (dm/games/settings.py)

  tools/engine/patch.py <nxnative checkout>

Each change is found by a line of the pinned commit's source and made once (a second run changes nothing); a line that is not there stops it, naming the file.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARK = '(switch2mac)'   # every inserted block names it, so a second run sees its own work


def edit(path, after, add, why):   # add the text after the first line holding `after`, once
    s = path.read_text()
    if MARK in add and add.strip() in s: return
    i = s.find(after)
    if i < 0: sys.exit(f'{path}: no line with {after!r} ({why}): this engine version is not one Hermit knows')
    j = s.index('\n', i) + 1
    path.write_text(s[:j] + add + s[j:])
    print(f'  {path.name}: {why}')


def main():
    if len(sys.argv) != 2: sys.exit(__doc__)
    nx = Path(sys.argv[1]).resolve(); host = nx / 'dm/host'; nvn = nx / 'dm/gfx/nvn'
    for f in (ROOT / 'tools/engine/s2m_ui.m', ROOT / 'tools/engine/s2m_share.m'):   # the overlay and panel; the shared shader list's offer (the same file as Mario Kart World's)
        src = f.read_bytes()
        if not (host / f.name).is_file() or (host / f.name).read_bytes() != src: (host / f.name).write_bytes(src); print(f'  {f.name} copied')
    mk = host / 'Makefile'; s = mk.read_text()
    if ' s2m_ui.m' not in s:
        if s.count('front_mac.m ') < 1: sys.exit(f'{mk}: no front_mac.m in the sources')
        mk.write_text(s.replace('front_mac.m ', 'front_mac.m s2m_ui.m s2m_share.m ', 1)); print('  Makefile: s2m_ui.m and s2m_share.m built with the host')
    fm = host / 'front_mac.m'
    edit(fm, '#include "front.h"', '// (switch2mac) overlay and settings panel: s2m_ui.m\n'
         'void s2m_ui_attach(NSWindow *win, NSView *view, CAMetalLayer *layer, void (*release)(void), void (*resume)(void)); int s2m_ui_key(NSEvent *e);\n', 'declarations')
    edit(fm, 'v.layer = g_layer; [(DmGameView *)v fitDrawable];', '        s2m_ui_attach(win, v, g_layer, input_release, input_resume);   // (switch2mac) the overlay and settings panel\n', 'overlay attached to the window')
    keys = ('if (e.type == NSEventTypeKeyDown && (e.modifierFlags & NSEventModifierFlagCommand)) return e;',   # nxnative's key monitor: ⌘ shortcuts go to the menu
            'if (cmd) return e;   // ⌘ shortcuts go to the menu')   # pokopia-native's (8c34a990: Shift, Control and Option as game keys, F1 its Settings window)
    edit(fm, next((k for k in keys if k in fm.read_text()), keys[0]),
         '            if (s2m_ui_key(e)) return nil;   // (switch2mac) keys 1 and 2, and every key while the settings panel is open\n', 'keys 1 and 2')
    mtl = nvn / 'nvn_mtl.m'
    if 's2m_fg_shown(void)' not in mtl.read_text():   # the overlay's shown frame rate with frame generation: the engine's count where it has one
        t = mtl.read_text()
        mtl.write_text(t.rstrip('\n') + '\nuint64_t s2m_fg_shown(void) { return %s; }   // (switch2mac) the overlay: pictures shown after a generated frame\n' % ('g_fg_shown' if 'static uint64_t g_fg_shown;' in t else '0'))
        print('  nvn_mtl.m: s2m_fg_shown')
    if 'mtl_cur_frame(void) {' not in mtl.read_text():
        edit(mtl, 'static _Atomic uint64_t g_cur_frame;', 'uint64_t mtl_cur_frame(void) { return atomic_load(&g_cur_frame); }   // (switch2mac) the overlay\'s frames per second\n', 'mtl_cur_frame')
    hn = nvn / 'hle_nvn.c'
    if 'void nvn_game_size(' not in hn.read_text():
        s = hn.read_text(); k = 'static const int *present_crop('
        if k not in s: sys.exit(f'{hn}: no present_crop')
        hn.write_text(s.replace(k, 'static _Atomic int g_game_w, g_game_h;   // (switch2mac) the size of the frame the game presents last (the overlay)\n'
                                   'void nvn_game_size(int *w, int *h) { *w = atomic_load(&g_game_w); *h = atomic_load(&g_game_h); }\n' + k, 1))
        edit(hn, 'const int *crop = present_crop(o->crop, (int)t->d.width, (int)t->d.height, lc);', '        atomic_store(&g_game_w, (int)t->d.width); atomic_store(&g_game_h, (int)t->d.height);   // (switch2mac)\n', 'nvn_game_size')
    bi = nx / 'scripts/build_ipa_from_nsp.py'   # a quick try (hermit.py --quick) also takes the game's shared shader list (S2M_SEEN), and builds a game whose profile has no shader_seen.tsv
    s = bi.read_text() if bi.is_file() else ''
    old = ("    return set(re.findall(r'^[0-9a-f]{16}\\b', g.table('shader_seen.tsv').read_text(errors='replace'), re.M))\n")
    if old in s:
        bi.write_text(s.replace(old, "    t = ''.join(f.read_text(errors='replace') for f in (g.table('shader_seen.tsv'), Path(os.environ.get('S2M_SEEN') or '/nonexistent')) if f.is_file())   # (switch2mac) and the shared list\n"
                                     "    return set(re.findall(r'^(?:[SC]\\t)?([0-9a-f]{16})(?:_[a-z]+)?\\b', t, re.M))\n", 1)); print('  build_ipa_from_nsp.py: quick tries take the shared shader list')
    elif s and 'S2M_SEEN' not in s: print('  build_ipa_from_nsp.py: no seen_listed of the known form: a quick try uses only the profile\'s own list')
    st = nx / 'dm/games/settings.py'
    s = st.read_text(); w = "    Path(sys.argv[4]).write_text(json.dumps(d,"
    if w not in s: sys.exit(f'{st}: no line with {w!r}')
    if MARK not in s:
        row = ("    # (switch2mac) the performance overlay's row, after Fullscreen (s2m_ui.m reads DM_OVERLAY)\n"
               "    ov = {'env': 'DM_OVERLAY', 'kind': 'choice', 'section': 'Game', 'label': '性能悬浮层', 'default': 'compact', 'level': 'basic',\n"
               "          'note': '游戏中按 1 键循环切换：紧凑（FPS + 分辨率）→ 详细（图表、GPU、帧时间、CPU、内存）→ 关闭。',\n"
               "          'options': [['compact', '紧凑'], ['detailed', '详细'], ['off', '关闭']]}\n"
               "    at = next((i + 1 for i, r in enumerate(d['settings']) if r.get('env') == 'DM_FULLSCREEN'), 0)\n"
               "    if not any(r.get('env') == 'DM_OVERLAY' for r in d['settings']): d['settings'].insert(at, ov)\n")
        st.write_text(s.replace(w, row + w, 1)); print('  settings.py: Performance overlay row')
    settings_zh(nx)
    settings_rows_zh(nx)
    game_marks_zh(nx)
    pokopia_language_zh(nx)
    hle_net_poll(nx)
    no_lag_pso_batch(nx)
    cheats_bundle(nx)
    cheats_zh(nx)


def cheats_bundle(nx):   # seed bundled cheats into Application Support so the signed app itself is never modified
    launcher = nx / 'dm/mac/launcher.c'; original_launcher = launcher.read_text(); s = original_launcher
    if '#include <dirent.h>' not in s:
        anchor = '#include <CoreFoundation/CoreFoundation.h>\n'
        if anchor not in s: sys.exit(f'{launcher}: no CoreFoundation include for bundled cheats')
        s = s.replace(anchor, anchor + '#include <dirent.h>   // (switch2mac) seed bundled cheats\n', 1)
    helper_anchor = 'static void mkdirs(const char *path) {   // mkdir -p\n'
    helper = '''// (switch2mac) Copy bundled cheat definitions once into the writable Application Support folder.
// The host stores .enabled/.values/.cheats-off files beside them, so DM_CHEATS must never point into the signed app.
static void seed_cheats(const char *src, const char *dst) {
    DIR *d = opendir(src); if (!d) return;
    mkdir(dst, 0755);
    for (struct dirent *e; (e = readdir(d));) {
        const char *dot = strrchr(e->d_name, '.');
        if (e->d_name[0] == '.' || !dot || (strcmp(dot, ".txt") && strcmp(dot, ".cheats.toml"))) continue;
        char a[PATH_MAX], b[PATH_MAX];
        int na = snprintf(a, sizeof a, "%s/%s", src, e->d_name), nb = snprintf(b, sizeof b, "%s/%s", dst, e->d_name);
        if (na < 0 || (size_t)na >= sizeof a || nb < 0 || (size_t)nb >= sizeof b || access(b, F_OK) == 0) continue;
        int fi = open(a, O_RDONLY), fo = open(b, O_WRONLY | O_CREAT | O_EXCL, 0644);
        if (fi < 0 || fo < 0) { if (fi >= 0) close(fi); if (fo >= 0) close(fo); continue; }
        char buf[65536]; ssize_t n; int ok = 1;
        while ((n = read(fi, buf, sizeof buf)) > 0) if (write(fo, buf, (size_t)n) != n) { ok = 0; break; }
        if (n < 0) ok = 0;
        close(fi); if (close(fo) && ok) ok = 0;
        if (!ok) unlink(b);
    }
    closedir(d);
}

'''
    if 'static void seed_cheats(' not in s:
        if helper_anchor not in s: sys.exit(f'{launcher}: no mkdirs anchor for bundled cheats')
        s = s.replace(helper_anchor, helper + helper_anchor, 1)
    olds = (
        ('\n    setenv("DM_ROOT", sup, 0); setenv("DM_ROMFS", romfs, 0); setenv("DM_SAVE", save, 0); setenv("DM_TEMP", temp, 0);\n',
         '\n    setenv("DM_ROOT", sup, 0); setenv("DM_ROMFS", romfs, 0); setenv("DM_SAVE", save, 0); setenv("DM_TEMP", temp, 0);\n'
         '    snprintf(cheats, sizeof cheats, "%s/cheats", sup);   // (switch2mac) writable cheat state\n'
         '    snprintf(p, sizeof p, "%s/cheats", res); seed_cheats(p, cheats); setenv("DM_CHEATS", cheats, 0);\n'),
        ('\n    setenv("DM_ROOT", sup, 0); setenv("DM_ROMFS", romfs, 0); setenv("DM_TEMP", temp, 0);\n',
         '\n    setenv("DM_ROOT", sup, 0); setenv("DM_ROMFS", romfs, 0); setenv("DM_TEMP", temp, 0);\n'
         '    snprintf(cheats, sizeof cheats, "%s/cheats", sup);   // (switch2mac) writable cheat state\n'
         '    snprintf(p, sizeof p, "%s/cheats", res); seed_cheats(p, cheats); setenv("DM_CHEATS", cheats, 0);\n'),
    )
    if 'seed_cheats(p, cheats)' not in s:
        old, add = next(((a, b) for a, b in olds if a in s), (None, None))
        if not old: sys.exit(f'{launcher}: no DM_ROOT line for bundled cheats')
        s = s.replace(old, add, 1)
    old_decl = '    char contents[PATH_MAX], res[PATH_MAX], host[PATH_MAX], dm[PATH_MAX], romfs[PATH_MAX], p[PATH_MAX];\n'
    new_decl = '    char contents[PATH_MAX], res[PATH_MAX], host[PATH_MAX], dm[PATH_MAX], romfs[PATH_MAX], p[PATH_MAX], cheats[PATH_MAX];\n'
    if 'cheats[PATH_MAX]' not in s:
        if old_decl not in s: sys.exit(f'{launcher}: no path declarations for bundled cheats')
        s = s.replace(old_decl, new_decl, 1)
    if s != original_launcher and 'seed_cheats(p, cheats)' in s and 'static void seed_cheats(' in s:
        launcher.write_text(s); print('  launcher.c: seed bundled cheats into Application Support')

    pack = nx / 'dm/mac/pack_app.py'; s = pack.read_text()
    if "add_argument('--cheats'" not in s:
        anchor = "    ap.add_argument('--env-file', help='environment switches baked in (Resources/dm/env.txt)')\n"
        if anchor not in s: sys.exit(f'{pack}: no --env-file argument for --cheats')
        s = s.replace(anchor, anchor + "    ap.add_argument('--cheats', help='(switch2mac) an Atmosphère cheat .txt bundled as Resources/cheats/<build ID>.txt')\n", 1)
        pack.write_text(s); print('  pack_app.py: --cheats argument')
    s = pack.read_text()
    old = "        for name in ('out', 'host', 'patched', 'romfs', 'msl', 'tables', 'font', 'aoc', 'pso', 'pso_pairs', 'env_file', 'settings', 'icon', 'html'):\n"
    new = "        for name in ('out', 'host', 'patched', 'romfs', 'msl', 'tables', 'font', 'aoc', 'pso', 'pso_pairs', 'env_file', 'settings', 'icon', 'html', 'cheats'):\n"
    if "'cheats')" not in s and old in s:
        s = s.replace(old, new, 1); pack.write_text(s); print('  pack_app.py: resolve the cheats path')
    s = pack.read_text()
    anchor = "        mods, msls, pso, tables, pairs, fonts, files = selected_inputs(a)\n"
    add = ("        if a.cheats:\n"
           "            cheat = Path(a.cheats)\n"
           "            if not cheat.is_file(): raise SystemExit(f'no cheat file at {cheat}')\n"
           "            files.append(cheat)\n")
    if 'cheat = Path(a.cheats)' not in s:
        if anchor not in s: sys.exit(f'{pack}: no selected_inputs line for --cheats')
        s = s.replace(anchor, anchor + add, 1); pack.write_text(s); print('  pack_app.py: cheats in the reuse key')
    s = pack.read_text()
    anchor = "    if a.settings: shutil.copyfile(a.settings, dm / 'launcher.json')\n"
    add = ("    if a.cheats:\n"
           "        step('cheats'); (res / 'cheats').mkdir(); shutil.copyfile(a.cheats, res / 'cheats' / Path(a.cheats).name)\n")
    if "res / 'cheats'" not in s:
        if anchor not in s: sys.exit(f'{pack}: no settings copy line for --cheats')
        s = s.replace(anchor, anchor + add, 1); pack.write_text(s); print('  pack_app.py: copy cheats into the app')

    build = nx / 'scripts/build_ipa_from_nsp.py'; s = build.read_text()
    if 'def mac_app(' not in s: sys.exit(f'{build}: no mac_app for --cheats')
    if not re.search(r'(?m)^def mac_app\([^\n]*cheats=None\):', s):
        s, n = re.subn(r'(?m)^(def mac_app\([^\n]*?)(\):)$', r'\1, cheats=None\2', s, count=1)
        if n != 1: sys.exit(f'{build}: mac_app signature not understood for --cheats')
        build.write_text(s); print('  build_ipa_from_nsp.py: mac_app cheats parameter')
    s = build.read_text()
    anchor = "        if v: cmd += [opt, v]\n"
    if "cmd += ['--cheats'" not in s:
        if anchor not in s: sys.exit(f'{build}: no mac_app option loop for --cheats')
        s = s.replace(anchor, anchor + "    if cheats: cmd += ['--cheats', Path(os.path.expanduser(cheats)).resolve()]\n", 1)
        build.write_text(s); print('  build_ipa_from_nsp.py: pass cheats to pack_app')
    s = build.read_text()
    anchor = "    ap.add_argument('--env-file', help='environment switches for a diagnostic build (one KEY=VALUE per line)')\n"
    if "add_argument('--cheats'" not in s:
        if anchor not in s: sys.exit(f'{build}: no --env-file argument for --cheats')
        s = s.replace(anchor, anchor + "    ap.add_argument('--cheats', help='(switch2mac) an Atmosphère cheat .txt bundled in the Mac app')\n", 1)
        build.write_text(s); print('  build_ipa_from_nsp.py: --cheats argument')
    s = build.read_text()
    calls = (
        ("                (args.gpu or PSO_GPUS).strip(), programs, control)\n",
         "                (args.gpu or PSO_GPUS).strip(), programs, control, args.cheats)\n"),
        ("                (args.gpu or PSO_GPUS).strip(), programs, control, PREBAKE if args.prebake is None else args.prebake)\n",
         "                (args.gpu or PSO_GPUS).strip(), programs, control, PREBAKE if args.prebake is None else args.prebake, args.cheats)\n"),
    )
    for old, new in calls:
        if old in s:
            s = s.replace(old, new, 1); build.write_text(s); print('  build_ipa_from_nsp.py: pass args.cheats to mac_app'); break
    else:
        if not re.search(r'mac_app\([^;]*args\.cheats\)', s, re.S): print('  build_ipa_from_nsp.py: mac_app call does not take cheats')


def cheats_zh(nx):   # the upstream Cheats window and load report, in Chinese
    front = nx / 'dm/host/front_mac.m'; s = front.read_text(); n = 0
    for old, new in (
        ('@"Cheats"', '@"金手指"'),
        ('@"Show Cheats Window"', '@"显示金手指窗口"'),
        ('@"Cheats On"', '@"启用金手指"'),
        ('@"Restore Saved Cheats (safe mode)"', '@"恢复已保存的金手指（安全模式）"'),
        ('@"Cheats for %@ (another version of the game)"', '@"%@ 的金手指（游戏其他版本）"'),
        ('@"No cheats for %@"', '@"%@ 没有可用金手指"'),
        ('@"Reload cheats"', '@"重新加载金手指"'),
        ('@"Open cheats folder"', '@"打开金手指文件夹"'),
        ('@"Last run ended unexpectedly with cheats on: all are off."', '@"上次启用金手指后异常退出；本次全部关闭。"'),
        ('@"Restore"', '@"恢复"'),
        ('@"Select All"', '@"全选"'),
        ('@"Deselect All"', '@"取消全选"'),
        ('@"Search"', '@"搜索"'),
        ('@"Open Folder"', '@"打开文件夹"'),
        ('@"Reload"', '@"重新加载"'),
        ('@"Find Cheats…"', '@"查找金手指…"'),
        ('@"Report"', '@"报告"'),
        ('@"Looking…"', '@"正在查找…"'),
        ('@"Apply"', '@"应用"'),
        ('@"Copy Command"', '@"复制命令"'),
        ('@"Show what it writes now, and its note"', '@"显示当前将写入的内容和说明"'),
        ('@"Details"', '@"详情"'),
        ('@"Value (%s, %s)"', '@"数值（%s，%s）"'),
        ('@"Left out of this build: %@ — %@"', '@"此构建未包含：%@ — %@"'),
        ('@"Cheats for %@: another version of the game, its addresses do not fit this one"', '@"%@ 的金手指属于另一个游戏版本，地址不适用于当前版本"'),
        ('@"%@: anchored cheats, not compiled for this build yet"', '@"%@：锚定金手指尚未针对此构建编译"'),
        ('@"Copied (run it in the nxnative folder): "', '@"已复制（请在 nxnative 目录运行）："'),
        ('@"Cheats are off: no cheats folder (DM_CHEATS or DM_ROOT is not set)"', '@"金手指已关闭：没有金手指文件夹（未设置 DM_CHEATS 或 DM_ROOT）"'),
        ('@"%@: %d cheats, %d on%@"', '@"%@：共 %d 个金手指，已启用 %d 个%@"'),
        ('@", %d master"', '@"，%d 个主代码"'),
        ('@"No cheat files of this game in Ryujinx, the yuzu family or an SD card"', '@"未在 Ryujinx、yuzu 系列或 SD 卡中找到此游戏的金手指文件"'),
        ('@"Cancel"', '@"取消"'),
        ('@"Is “%@” for this version of the game?"', '@"“%@”适用于当前游戏版本吗？"'),
        ('@"Its name does not say which build it is for. It will be used as the cheats of %@."', '@"文件名没有标明游戏版本。将作为 %@ 的金手指使用。"'),
        ('@"Use for This Build"', '@"用于当前构建"'),
        ('@"Replace %@?"', '@"替换 %@？"'),
        ('@"The current one is kept as %@.bak (an older %@.bak is replaced)."', '@"当前文件将保留为 %@.bak（旧的 %@.bak 会被替换）。"'),
        ('@"Replace"', '@"替换"'),
        ('@" (apply once)"', '@"（单次应用）"'),
        ('@" — master code (always on)"', '@" — 主代码（始终启用）"'),
        ('@" (nxnative only)"', '@"（仅 nxnative）"'),
        ('@"\\nRun by nxnative itself: it keeps the highest value seen since it was turned on; other engines see an empty entry."', '@"\\n由 nxnative 自身执行：保留启用后见过的最高值；其他引擎会显示为空条目。"'),
        ('@"\\nApplied once: it writes one pass, then turns itself off."', '@"\\n只应用一次：写入一个周期后自动关闭。"'),
        ('@"\\nSwitching it off puts the game\'s original code back."', '@"\\n关闭时会恢复游戏原始代码。"'),
        ('@"\\nResolved weakly for this build: check its effect."', '@"\\n此构建使用弱锚点定位，请确认实际效果。"'),
        ('@"%@ (build %@)"', '@"%@（构建 %@）"'),
        ('@"build %@"', '@"构建 %@"'),
        ('@"Window"', '@"窗口"'),
        ('@"Enter Full Screen"', '@"进入全屏"'),
        ('@"Quit "', '@"退出 "'),
    ):
        if old in s: n += s.count(old); s = s.replace(old, new)
    if n: front.write_text(s); print(f'  front_mac.m: Chinese cheats window ({n} strings)')

    host = nx / 'dm/host/hle_cheats.c'; s = host.read_text(); n = 0
    for old, new in (
        ('Build %s%s%s%s: %d cheats (%d on, %d master, %d broken)', '构建 %s%s%s%s：%d 个金手指（%d 已启用，%d 主代码，%d 损坏）'),
        (', %d labels (%d sections)', '，%d 个标签（%d 个分区）'),
        ('Duplicate names (saved as \\"Name #2\\", …):', '重复名称（后续保存为「名称 #2」等）：'),
        ('%d lines that are not code words were ignored (the first: line %d)\\n', '%d 行不是金手指代码，已忽略（首个位于第 %d 行）\\n'),
        ('%d headers glued to a code line were split off\\n', '%d 个与代码写在同一行的标题已拆分\\n'),
        ('Toggles carried over from %s (no %s.enabled yet)\\n', '开关状态继承自 %s（尚无 %s.enabled）\\n'),
        ('Safe mode: the last run ended without a clean exit while cheats were on; every cheat starts off\\n', '安全模式：上次启用金手指后异常退出，本次所有金手指默认关闭\\n'),
        ('The master switch is off: no cheat runs\\n', '主开关已关闭：不会执行金手指\\n'),
        ('%d cheats were left out when this file was compiled\\n', '编译此文件时排除了 %d 个金手指\\n'),
        ("Over Atmosphère's limits (a Switch refuses them): %d cheats (0x80), %d cheats over 0x100 words, %d words enabled (0x400)\\n", '超过 Atmosphère 上限（Switch 会拒绝）：%d 个金手指（0x80），%d 个超过 0x100 字，启用的代码共 %d 字（0x400）\\n'),
        ('a label, not a cheat', '这是分组标签，不是金手指'),
        ('does not run:%s', '不会执行：%s'),
        ('%s: not mapped right now', '%s：当前尚未映射'),
        ('%s: %s now, kept at least %s (the highest seen)', '%s：当前为 %s，至少保持为 %s（启用后见过的最高值）'),
        ('%s: %s now; turned on, it never goes below the highest value it reaches', '%s：当前为 %s；启用后不会低于曾达到的最高值'),
        ('writes nothing right now (a condition is not met, or a patch\'s code is not the original any more)', '当前没有写入（条件未满足，或补丁目标已不是原始代码）'),
        (' (already)', '（已是该值）'),
    ):
        if old in s: n += s.count(old); s = s.replace(old, new)
    if n: host.write_text(s); print(f'  hle_cheats.c: Chinese cheats report ({n} strings)')


def hle_net_poll(nx):   # cap the offline poll/select idle wait at 100 ms: Mario Kart World otherwise stalls for ~14 s at "return to home" / before the course select (0 fps)
    path = nx / 'dm/host/hle_net.c'; s = path.read_text()
    old = "static int sk_idle(int64_t ms) { dm_guest_sleep_ns((ms < 0 ? 100 : ms) * 1000000); return 0; }"
    new = "static int sk_idle(int64_t ms) { if (ms > 100) ms = 100; dm_guest_sleep_ns((ms < 0 ? 100 : ms) * 1000000); return 0; }"
    if old in s:
        path.write_text(s.replace(old, new, 1)); print('  hle_net.c: poll idle capped at 100 ms')


def no_lag_pso_batch(nx):   # No Lag Kart's 1.8.0 archive: a 1000-base batch spent over an hour in metal-tt on this Mac; 200-base batches finish it in about 2 minutes
    marker = nx / 'mkw/pso/pso_manifest_merged_180.tsv'
    path = nx / 'dm/gfx/tools/pso_offline.py'
    if not marker.is_file() or not path.is_file(): return
    s = path.read_text()
    old = "BATCH = 1000   # bases per metal-tt run: Odyssey's largest compiler lifetime footprint at this size was 2.065 GiB on an 8 GB M2"
    new = "BATCH = 200   # (switch2mac) No Lag Kart's 1.8.0 archive: 1000-base batch 3 spent over an hour in metal-tt on this Mac"
    if old in s:
        path.write_text(s.replace(old, new, 1)); print('  pso_offline.py: No Lag Kart pipeline batches capped at 200 bases')


def settings_zh(nx):   # switch2mac's Chinese labels/notes for the generic rows a game's key-2 panel shows (idempotent: the English lines are gone after the first run)
    path = nx / 'dm/games/settings.tsv'; s = path.read_text(); changed = False
    for old, new in (
        ("DM_OPMODE\tchoice\t1=Docked,0=Handheld\tDM_GAME_OPMODE\talways\tGame\tConsole mode\t\tlevel=basic",
         "DM_OPMODE\tchoice\t1=底座模式,0=掌机模式\tDM_GAME_OPMODE\talways\tGame\t主机模式\t\tlevel=basic"),
        ("DM_PRESENT_UPSCALE\tchoice\toff=Standard,metalfx=MetalFX\toff\talways\tGame\tUpscaling\tUses more GPU time and can increase heat.",
         "DM_PRESENT_UPSCALE\tchoice\toff=标准,metalfx=MetalFX\toff\talways\tGame\t画面放大\t会占用更多 GPU 时间，可能增加发热。"),
        ("DM_PRESENT_UPSCALE\tchoice\toff=Standard,metalfx=MetalFX\tDM_GAME_PRESENT_UPSCALE\talways\tGame\tUpscaling\tUses more GPU time and can increase heat.",
         "DM_PRESENT_UPSCALE\tchoice\toff=标准,metalfx=MetalFX\tDM_GAME_PRESENT_UPSCALE\talways\tGame\t画面放大\t会占用更多 GPU 时间，可能增加发热。"),
        ("DM_LANG\tchoice\tlanguages\tbuild:DM_LANG\tlanguages>1\tGame\tGame language\t\tlevel=basic",
         "DM_LANG\tchoice\tlanguages\tbuild:DM_LANG\tlanguages>1\tGame\t游戏语言\t\tlevel=basic"),
        ("DM_FULLSCREEN\tchoice\t0=Window,1=Fullscreen\t0\tplatform:mac\tGame\tDisplay mode\t\tlevel=basic",
         "DM_FULLSCREEN\tchoice\t0=窗口,1=全屏\t0\tplatform:mac\tGame\t显示模式\t\tlevel=basic"),
        ("DM_FULLSCREEN\tchoice\t0=Window,1=Fullscreen\tDM_GAME_FULLSCREEN\tplatform:mac\tGame\tDisplay mode\t\tlevel=basic",
         "DM_FULLSCREEN\tchoice\t0=窗口,1=全屏\tDM_GAME_FULLSCREEN\tplatform:mac\tGame\t显示模式\t\tlevel=basic"),
        ("DM_UPSCALER\tchoice\tgame=Game's own,metalfx=MetalFX\tgame\tDM_GAME_UPSCALER_N!=0\tGame\tGame's upscaler",
         "DM_UPSCALER\tchoice\tgame=游戏自带,metalfx=MetalFX\tgame\tDM_GAME_UPSCALER_N!=0\tGame\t游戏内置升频器"),
        ("DM_RUMBLE\ttoggle\t-\t1\talways\tControls\tGame rumble\t\tlevel=basic",
         "DM_RUMBLE\ttoggle\t-\t1\talways\tControls\t手柄震动\t\tlevel=basic"),
        ("DM_RUMBLE_GAIN\trange\t0:3:0.1\t1.0\talways\tControls\tRumble strength\t\tneeds=DM_RUMBLE=1",
         "DM_RUMBLE_GAIN\trange\t0:3:0.1\t1.0\talways\tControls\t震动强度\t\tneeds=DM_RUMBLE=1"),
        ("DM_RUMBLE_MIN\trange\t0:0.9:0.05\t0\talways\tControls\tRumble cutoff",
         "DM_RUMBLE_MIN\trange\t0:0.9:0.05\t0\talways\tControls\t震动阈值"),
        ("DM_PRESENT_SNAP\ttoggle\t-\tDM_GAME_PRESENT_SNAP\tgfxapi:nvn\tPerformance\tFrame buffering\tUp to one frame more display latency.",
         "DM_PRESENT_SNAP\ttoggle\t-\tDM_GAME_PRESENT_SNAP\tgfxapi:nvn\tPerformance\t帧缓冲\t最多增加一帧显示延迟。"),
        ("DM_PSO_MTL4\ttoggle\t-\tDM_GAME_PSO_MTL4|1\tgfxapi:nvn\tPerformance\tMetal 4 pipelines\tKeeps a pipeline archive; uses more memory.",
         "DM_PSO_MTL4\ttoggle\t-\tDM_GAME_PSO_MTL4|1\tgfxapi:nvn\tPerformance\tMetal 4 管线\t保留管线归档；占用更多内存。"),
        ("DM_PSO_PREBUILD\ttoggle\t-\t1\tgfxapi:nvn\tPerformance\tPipeline prebuild\tThe first start waits a few minutes for it, once.\tneeds=DM_PSO_MTL4=1",
         "DM_PSO_PREBUILD\ttoggle\t-\t1\tgfxapi:nvn\tPerformance\t管线预构建\t首次启动会为此等待几分钟，仅一次。\tneeds=DM_PSO_MTL4=1"),
        ("DM_NVN_ENC_THREAD\ttoggle\t-\t1|DM_GAME_ENC_THREAD\tgfxapi:nvn\tPerformance\tEncode thread",
         "DM_NVN_ENC_THREAD\ttoggle\t-\t1|DM_GAME_ENC_THREAD\tgfxapi:nvn\tPerformance\t编码线程"),
        ("DM_NVN_ENC_THREAD\ttoggle\t-\tDM_GAME_ENC_THREAD_IOS|DM_GAME_ENC_THREAD\tgfxapi:nvn\tPerformance\tEncode thread",
         "DM_NVN_ENC_THREAD\ttoggle\t-\tDM_GAME_ENC_THREAD_IOS|DM_GAME_ENC_THREAD\tgfxapi:nvn\tPerformance\t编码线程"),
        ("DM_NVN_TBDR\ttoggle\t-\t0\tgfxapi:nvn\tPerformance\tTile memory (TBDR)\tFaster on iPhone; may show glitches in games with bindless textures.",
         "DM_NVN_TBDR\ttoggle\t-\t0\tgfxapi:nvn\tPerformance\t瓦片内存（TBDR）\tiPhone 上更快；带 bindless 纹理的游戏可能出现画面问题。"),
        ("DM_NVN_TEX_DROP\ttoggle\t-\t1|0\talways\tPerformance\tFree texture memory\tLets the system move the game's copy of textures the GPU already holds out of memory first: less stutter. Turning it on sets Render scale 65% and Medium textures.",
         "DM_NVN_TEX_DROP\ttoggle\t-\t1|0\talways\tPerformance\t释放纹理内存\t优先把 GPU 已持有的纹理副本移出内存：减少卡顿。开启时会把渲染比例设为 65%、纹理质量设为中。"),
        ("DM_METAL_HUD\ttoggle\t-\t0\talways\tPerformance\tPerformance HUD",
         "DM_METAL_HUD\ttoggle\t-\t0\talways\tPerformance\t性能 HUD"),
        ("DM_FPS_TARGET\tchoice\t30=30 fps,60=60 fps,120=120 fps?DM_GAME_FPS_MAX==120&platform:mac\tDM_GAME_FPS_TARGET\tDM_GAME_FPS_TARGET!=0\tGame\tFrame rate\t\tlevel=basic",
         "DM_FPS_TARGET\tchoice\t30=30 帧,60=60 帧,120=120 帧?DM_GAME_FPS_MAX==120&platform:mac\tDM_GAME_FPS_TARGET\tDM_GAME_FPS_TARGET!=0\tGame\t帧率\t\tlevel=basic"),
        ("DM_FPS_TARGET\tchoice\t30=30 fps,60=60 fps\tDM_GAME_FPS_TARGET\tDM_GAME_FPS_TARGET!=0\tGame\tFrame rate\t\tlevel=basic",
         "DM_FPS_TARGET\tchoice\t30=30 帧,60=60 帧\tDM_GAME_FPS_TARGET\tDM_GAME_FPS_TARGET!=0\tGame\t帧率\t\tlevel=basic"),
        ("DM_PRESET\tchoice\tcustom=Custom,full=Full,high=High,medium=Medium,low=Low\tmedium\tplatform:ios\tGame\tGraphics preset\tSets texture quality, render scale, frame rate, upscaling and the performance switches together; changing one of them makes it Custom.\tlevel=basic",
         "DM_PRESET\tchoice\tcustom=自定义,full=完整,high=高,medium=中,low=低\tmedium\tplatform:ios\tGame\t画面预设\t同时设置纹理质量、渲染比例、帧率、放大方式和性能开关；修改其中一项后会变为“自定义”。\tlevel=basic"),
        ("DM_FPS_LOCK\tchoice\t0=Game decides,30=Locked 30 fps,60=Locked 60 fps\t30|0\tfixups:FPS_LOCK\tGame\tFrame rate\t30 locks the game's step and removes the jumping between 30 and 60; 60 runs in slow motion where the phone cannot keep up.\tlevel=basic",
         "DM_FPS_LOCK\tchoice\t0=游戏决定,30=锁定 30 帧,60=锁定 60 帧\t30|0\tfixups:FPS_LOCK\tGame\t帧率锁定\t30 帧会锁定游戏步进，避免在 30 和 60 之间跳动；60 帧在设备跟不上时会变成慢动作。\tlevel=basic"),
        ("DM_DYNAMIC_RESOLUTION\ttoggle\t-\t0\tfixups:DYNAMIC_RESOLUTION\tGame\tDynamic resolution\tAdjusts resolution between 70% and 100% under load. Turn off to keep full resolution for the selected console mode.",
         "DM_DYNAMIC_RESOLUTION\ttoggle\t-\t0\tfixups:DYNAMIC_RESOLUTION\tGame\t动态分辨率\t在高负载时把分辨率调整到 70%–100%；关闭后保持所选主机模式的完整分辨率。"),
        ("DM_RENDER_SCALE\trange\t0.5:1.0:0.05\tDM_GAME_RENDER_SCALE_IOS|1.0\tfixups:RENDER_SCALE\tGame\tRender scale\t\tlevel=basic",
         "DM_RENDER_SCALE\trange\t0.5:1.0:0.05\tDM_GAME_RENDER_SCALE_IOS|1.0\tfixups:RENDER_SCALE\tGame\t渲染比例\t\tlevel=basic"),
        ("DM_NVN_TEX_FLOOR\tchoice\tauto=Automatic,0=Full,1024=High,512=Medium,256=Low\t512|0\talways\tGame\tTexture quality\tLower uses less memory (fewer stutters); surfaces look blurrier up close. The picture stays as sharp as Render scale.\tlevel=basic",
         "DM_NVN_TEX_FLOOR\tchoice\tauto=自动,0=完整,1024=高,512=中,256=低\t512|0\talways\tGame\t纹理质量\t越低越省内存（更少卡顿）；近看表面会更模糊，但清晰度和渲染比例一致。\tlevel=basic"),
        ("DM_FRAMEGEN\ttoggle\t-\t0\tgfxapi:nvn\tGame\tFrame generation (30 shown as 60)\tThe game draws 30 frames a second and MetalFX makes a frame between each two, so the screen shows 60. Sets Frame rate to 30 while it is on. A little more input delay than real 60; fast motion can smear.\tlevel=basic",
         "DM_FRAMEGEN\ttoggle\t-\t0\tgfxapi:nvn\tGame\t帧生成\t游戏每秒绘制 30 帧，MetalFX 在每两帧之间生成一帧，屏幕显示 60 帧；开启时会把帧率设为 30。输入延迟比真正 60 帧稍高，快速运动可能有拖影。\tlevel=basic"),
        ("DM_FAST_720\ttoggle\t-\t0\tfixups:RENDER_SCALE\tGame\tFast mode (720p + MetalFX)\tDraws the 3D picture at about 720p and lets MetalFX scale it up: faster, a little softer. Replaces Render scale and Game's upscaler while it is on.\tlevel=basic",
         "DM_FAST_720\ttoggle\t-\t0\tfixups:RENDER_SCALE\tGame\t快速模式\t3D 画面约 720p，由 MetalFX 放大：更快但稍软。开启时替代渲染比例和游戏内置升频器。\tlevel=basic"),
        ("DM_FULL_DOCKED\ttoggle\t-\t0\tfixups:RENDER_SCALE\tGame\tFull docked picture (1080p)\tDraws the 3D picture at the Switch 2's full docked size, 1920x1080 instead of 1536x864: sharper, about 2-3 ms slower a frame.",
         "DM_FULL_DOCKED\ttoggle\t-\t0\tfixups:RENDER_SCALE\tGame\t完整底座画面\t以 Switch 2 完整底座尺寸 1920x1080 绘制（而非 1536x864）：更清晰，每帧约慢 2-3 ms。"),
        ("DM_DYNAMIC_RESOLUTION\ttoggle\t-\t0\tfixups:DYNAMIC_RESOLUTION\tGame\tDynamic resolution\tLets the game lower its resolution under load. Turn off to keep full resolution for the selected console mode.",
         "DM_DYNAMIC_RESOLUTION\ttoggle\t-\t0\tfixups:DYNAMIC_RESOLUTION\tGame\t动态分辨率\t让游戏在高负载时降低分辨率；关闭后保持所选主机模式下的完整分辨率。"),
        ("DM_RENDER_SCALE\trange\t0.5:1.0:0.05\t1.0\tfixups:RENDER_SCALE\tGame\tRender scale\t\tlevel=basic",
         "DM_RENDER_SCALE\trange\t0.5:1.0:0.05\t1.0\tfixups:RENDER_SCALE\tGame\t渲染比例\t\tlevel=basic"),
        ("DM_PICTURE_FIT\tchoice\tfit=Fit,fill=Fill\tfit\tplatform:ios\tGame\tPicture\tFill crops the game's 16:9 picture to cover the screen. Health bars, subtitles or maps near the edges can be cut off. A full-screen picture without cropping needs a patch for each game.",
         "DM_PICTURE_FIT\tchoice\tfit=适配,fill=填充\tfit\tplatform:ios\tGame\t画面\t“填充”会裁切游戏的 16:9 画面以铺满屏幕，边缘的血条、字幕或地图可能被切掉；不裁切的全屏画面需要为每个游戏单独打补丁。"),
        ("DM_SHOW_FPS\ttoggle\t-\tbuild:DM_SHOW_FPS\tplatform:ios\tGame\tFrame-rate counter",
         "DM_SHOW_FPS\ttoggle\t-\tbuild:DM_SHOW_FPS\tplatform:ios\tGame\t帧率显示"),
        ("DM_TOUCH_HAPTICS\ttoggle\t-\t1\tplatform:ios\tControls\tTouch feedback",
         "DM_TOUCH_HAPTICS\ttoggle\t-\t1\tplatform:ios\tControls\t触摸反馈"),
        ("DM_PAD_PRESS_TO_JOIN\ttoggle\t-\t0\talways\tControls\tPress a button to join",
         "DM_PAD_PRESS_TO_JOIN\ttoggle\t-\t0\talways\tControls\t按键加入"),
        ("DM_SW2\ttoggle\t-\t0\tplatform:mac\tControls\tSwitch 2 controllers\tPlays Joy-Con 2 and Pro Controller 2 over Bluetooth: hold Sync on one during the game to pair it. macOS asks once for Bluetooth access.",
         "DM_SW2\ttoggle\t-\t0\tplatform:mac\tControls\tSwitch 2 手柄\t通过蓝牙使用 Joy-Con 2 和 Pro Controller 2：游戏中按住手柄上的 Sync 键配对。macOS 会请求一次蓝牙权限。"),
        ("DM_SCREEN_ASPECT\tchoice\tauto=Match screen?platform:ios,1.43=iPhone Duo screen (1.43:1),0=16:9 (Switch)\tauto|0\tDM_GAME_SCREEN_ASPECT!=0\tGame\tPicture shape\tRenders about a quarter more pixels: a little slower and warmer.",
         "DM_SCREEN_ASPECT\tchoice\tauto=匹配屏幕?platform:ios,1.43=iPhone Duo 屏幕 (1.43:1),0=16:9 (Switch)\tauto|0\tDM_GAME_SCREEN_ASPECT!=0\tGame\t画面形状\t渲染像素约多四分之一：会稍慢、稍热。"),
        ("DM_FPS_HOLD\ttoggle\ton/off\tDM_GAME_FPS_HOLD\tDM_GAME_FPS_TARGET!=0\tPerformance\tHold frames when late",
         "DM_FPS_HOLD\ttoggle\ton/off\tDM_GAME_FPS_HOLD\tDM_GAME_FPS_TARGET!=0\tPerformance\t掉帧时保持帧"),
    ):
        if old in s:
            s = s.replace(old, new); changed = True
    if changed: path.write_text(s); print('  settings.tsv: Chinese labels/notes')

    # the note a language list without control data shows (settings.py), and the language names in the DM_LANG menu (nacp.py)
    sp = nx / 'dm/games/settings.py'; t = sp.read_text()
    old_note = "UNKNOWN_LANGUAGES = 'This game\\'s files do not list its languages, so some of these may not be in the game. It may then show another one.'"
    new_note = "UNKNOWN_LANGUAGES = '此游戏文件未列出其语言，因此其中一些可能不在游戏中；游戏可能显示为另一种语言。'"
    if old_note in t:
        sp.write_text(t.replace(old_note, new_note)); print('  settings.py: Chinese language note')
    np_ = nx / 'dm/tools/nacp.py'; n = np_.read_text()
    table = re.search(r'^LANGUAGES = \[(.*?)\]\s*$', n, re.M | re.S)
    if table:
        names = {
            'en-US': '美式英语', 'en-GB': '英式英语', 'ja': '日语', 'fr': '法语',
            'de': '德语', 'es-419': '拉美西班牙语', 'es': '西班牙语', 'it': '意大利语',
            'nl': '荷兰语', 'fr-CA': '加拿大法语', 'pt': '葡萄牙语', 'ru': '俄语',
            'ko': '韩语', 'zh-Hant': '繁体中文', 'zh-Hans': '简体中文',
            'pt-BR': '巴西葡萄牙语', 'pl': '波兰语', 'th': '泰语',
        }
        block = table.group(1)
        shown = re.sub(r"\('([^']+)', '([^']+)'\)", lambda x: f"('{x[1]}', '{names.get(x[1], x[2])}')", block)
        if shown != block:
            np_.write_text(n[:table.start(1)] + shown + n[table.end(1):]); print('  nacp.py: Chinese language names')


def settings_rows_zh(nx):   # by variable, not by the whole line: nxnative's capitalization and conditions differ between ports
    path = nx / 'dm/games/settings.tsv'; s = path.read_text()
    labels = {
        'DM_FPS_TARGET': '帧率',
        'DM_FRAMEGEN': '帧生成',
        'DM_DYNAMIC_RESOLUTION': '动态分辨率',
        'DM_RENDER_SCALE': '渲染比例',
        'DM_WIDE_VIEW': '宽屏视野',
        'DM_OPMODE': '主机模式',
        'DM_PRESENT_UPSCALE': '画面放大',
        'DM_UPSCALER': '游戏内置升频器',
        'DM_LANG': '游戏语言',
        'DM_FULLSCREEN': '显示模式',
        'DM_OVERLAY': '性能悬浮层',
        'DM_MIC': '麦克风',
        'DM_MIC_BOOST': '麦克风灵敏度',
        'DM_LOOK_SCALE': '视角灵敏度',
        'DM_LOOK_INVERT_Y': '上下反转视角',
        'DM_RUMBLE': '手柄震动',
        'DM_RUMBLE_GAIN': '震动强度',
        'DM_RUMBLE_MIN': '震动阈值',
        'DM_PAD_PRESS_TO_JOIN': '按键加入',
        'DM_SW2': 'Switch 2 手柄',
        'DM_PRESENT_SNAP': '帧缓冲',
        'DM_PSO_MTL4': 'Metal 4 管线',
        'DM_PSO_PREBUILD': '管线预构建',
        'DM_NVN_ENC_THREAD': '编码线程',
        'DM_NVN_TEX_MIP_SKIP': '纹理内存节省',
        'DM_FPS_HOLD': '掉帧时保持帧',
        'DM_METAL_HUD': '性能信息',
        'DM_PICTURE_FIT': '画面',
        'DM_SHOW_FPS': '帧率显示',
        'DM_TOUCH_HAPTICS': '触摸反馈',
        'DM_PAD_THEME': '触屏控制样式',
        'DM_SCREEN_ASPECT': '画面形状',
        'DM_PRESET': '画面预设',
        'DM_FPS_LOCK': '帧率锁定',
        'DM_NVN_TEX_FLOOR': '纹理质量',
        'DM_FAST_720': '快速模式',
        'DM_FULL_DOCKED': '完整底座画面',
        'DM_MIC_GAIN': '麦克风灵敏度',
    }
    notes = {
        'DM_FPS_TARGET': '60 帧更流畅；30 帧更省电。',
        'DM_FRAMEGEN': '游戏每秒绘制 30 帧，MetalFX 在每两帧之间生成一帧，因此屏幕显示 60 帧。它比真实 60 帧更省性能和发热，但输入延迟更高；快速运动可能出现拖影。',
        'DM_DYNAMIC_RESOLUTION': '让游戏在高负载时自动降低分辨率；关闭后保持所选主机模式的完整分辨率。',
        'DM_WIDE_VIEW': '以 iPhone 屏幕自身的比例铺满画面（约 19.5:9），视野更宽且没有黑边；3D 摄像机和界面会随屏幕形状调整，不会拉伸。渲染像素约增加五分之一，因此会稍慢、稍热。下一次启动游戏时生效。iPhone 默认开启；iPad 保持 16:9。',
        'DM_PRESENT_UPSCALE': '会使用更多 GPU 时间，可能增加发热。',
        'DM_OVERLAY': '游戏中按 1 键循环切换：紧凑（帧率 + 分辨率）→ 详细（图表、GPU、帧时间、CPU、内存）→ 关闭。',
        'DM_MIC': '让需要听声音的游戏能够听到你，例如通过哼唱或吹口哨来演奏时之笛。系统只会询问一次麦克风权限；在 iPhone 上，游戏声音会通过同时录音的音频会话播放。推荐开启以使用语音演奏时之笛。',
        'DM_MIC_GAIN': '提高较轻微的麦克风输入；过高时也会更容易收入环境声。',
        'DM_MIC_BOOST': '提高房间里较轻微、但仍能被识别出的哼唱和口哨声。高灵敏度还能听到更轻的音符，但也会收入更多环境声和游戏自身声音；关闭时把原始麦克风输入交给游戏。',
        'DM_SW2': '通过蓝牙使用 Joy-Con 2 和 Pro Controller 2：游戏中按住手柄上的 Sync 键配对。macOS 会请求一次蓝牙权限。',
        'DM_PRESENT_SNAP': '最多增加一帧显示延迟。',
        'DM_PSO_MTL4': '保留管线归档；占用更多内存。',
        'DM_PSO_PREBUILD': '首次启动会为此等待几分钟，仅一次。',
        'DM_NVN_TEX_MIP_SKIP': '大型纹理会省略最精细的层级：内存占用约为原来的四分之一，区域加载更短，近距离画面会稍软。iPhone 默认开启。',
        'DM_PICTURE_FIT': '“填充”会裁切游戏的 16:9 画面以铺满屏幕，边缘的血条、字幕或地图可能被切掉；不裁切的全屏画面需要为每个游戏单独打补丁。',
        'DM_PAD_THEME': '屏幕触控按键的颜色。',
        'DM_SCREEN_ASPECT': '渲染像素约多四分之一：会稍慢、稍热。',
        'DM_PRESET': '同时设置纹理质量、渲染比例、帧率、放大方式和性能开关；修改其中一项后会变为“自定义”。',
        'DM_FPS_LOCK': '30 帧会锁定游戏步进，避免在 30 和 60 之间跳动；60 帧在设备跟不上时会变成慢动作。',
        'DM_NVN_TEX_FLOOR': '越低越省内存（更少卡顿）；近看表面会更模糊，但清晰度和渲染比例一致。',
        'DM_FAST_720': '3D 画面约 720p，由 MetalFX 放大：更快但稍软。开启时替代渲染比例和游戏内置升频器。',
        'DM_FULL_DOCKED': '以 Switch 2 完整底座尺寸 1920x1080 绘制（而非 1536x864）：更清晰，每帧约慢 2-3 ms。',
    }
    options = (
        ('30 fps', '30 帧'), ('60 fps', '60 帧'), ('120 fps', '120 帧'),
        ('Docked', '底座模式'), ('Handheld', '掌机模式'),
        ("Game's own", '游戏自带'), ('Standard', '标准'),
        ('Window', '窗口'), ('Fullscreen', '全屏'),
        ('Normal', '正常'), ('High', '高'), ('Off', '关闭'),
        ('Classic', '经典'), ('Forest', '森林'),
        ('Custom', '自定义'), ('Full', '完整'), ('Medium', '中'), ('Low', '低'),
        ('Game decides', '游戏决定'), ('Locked 30 fps', '锁定 30 帧'), ('Locked 60 fps', '锁定 60 帧'),
        ('Match screen', '匹配屏幕'), ('iPhone Duo screen', 'iPhone Duo 屏幕'),
        ('Automatic', '自动'),
    )
    changed = False
    out = []
    for line in s.splitlines(True):
        ending = '\n' if line.endswith('\n') else ''
        body = line[:-1] if ending else line
        fields = body.split('\t')
        if len(fields) >= 7 and fields[0] in labels:
            fields[2] = fields[2]
            for old, new in options: fields[2] = fields[2].replace(old, new)
            fields[6] = labels[fields[0]]
            if fields[0] in notes: fields[7] = notes[fields[0]]
            body = '\t'.join(fields)
        out.append(body + ending)
    t = ''.join(out)
    if t != s:
        path.write_text(t); print('  settings.tsv: Chinese labels, notes and options by variable')


def game_marks_zh(nx):   # the render-scale preset name lives in each game profile, not settings.tsv
    for path in nx.glob('dm/games/*/game.tsv'):
        s = path.read_text()
        t = s.replace('0.25=Ultra Potato Mode 🥔', '0.25=超低画质模式 🥔')
        if t != s:
            path.write_text(t); print(f'  {path.parent.name}/game.tsv: Chinese render-scale mark')


def pokopia_language_zh(nx):   # Pokopia's generated control data lists only English; expose the game's language choices and default to Chinese
    path = nx.parent / 'nxs2.py'
    if not path.is_file(): return
    s = path.read_text()
    if '(switch2mac) Pokopia\'s generated control lists only English' in s: return
    old = ("    run([PY, NX / 'dm/games/settings.py', TITLE, b.patched, b.extract / 'control.nacp', settings], b.logs / 'settings.log',\n"
           "        env=b.env(GFXAPI='nvn', SETTINGS_PLATFORM='mac', DM_LANG='en-US'))\n")
    new = ("    run([PY, NX / 'dm/games/settings.py', TITLE, b.patched, b.extract / 'control.nacp', settings], b.logs / 'settings.log',\n"
           "        env=b.env(GFXAPI='nvn', SETTINGS_PLATFORM='mac', DM_LANG='zh-Hans'))\n"
           "    # (switch2mac) Pokopia's generated control lists only English, so settings.py omits\n"
           "    # DM_LANG. The game itself has the standard language list; expose it and default to Chinese.\n"
           "    data = json.loads(settings.read_text())\n"
           "    if not any(s.get('env') == 'DM_LANG' for s in data['settings']):\n"
           "        lang = {'env': 'DM_LANG', 'kind': 'choice', 'section': 'Game', 'label': '游戏语言',\n"
           "                'default': 'zh-Hans', 'level': 'basic',\n"
           "                'options': [['zh-Hans', '简体中文'], ['zh-Hant', '繁体中文'],\n"
           "                            ['en-US', '美式英语'], ['ja', '日语'], ['ko', '韩语'],\n"
           "                            ['fr', '法语'], ['de', '德语'], ['es', '西班牙语'],\n"
           "                            ['it', '意大利语'], ['pt', '葡萄牙语'], ['ru', '俄语']]}\n"
           "        at = next((i + 1 for i, s in enumerate(data['settings']) if s.get('env') == 'DM_OPMODE'), 0)\n"
           "        data['settings'].insert(at, lang)\n"
           "        settings.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\\n')\n")
    if old in s:
        s = s.replace(old, new, 1)
        s = s.replace("'--lang', 'en-US', '--sign'", "'--lang', 'zh-Hans', '--sign'", 1)
        path.write_text(s); print('  nxs2.py: Pokopia language list and default Simplified Chinese')


if __name__ == '__main__':
    main()
