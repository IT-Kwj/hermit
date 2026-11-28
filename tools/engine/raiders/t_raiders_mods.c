#include "hle_raiders_mods.c"
#include <assert.h>

static module_t modules[1];
module_t *g_mod = modules;
int g_nmod;

static uint8_t heap[0x20000];
static void (*callbacks[OBS_MAX])(uint64_t *, int);
static unsigned writes;
static uint64_t tick = 1000000000, buttons;
static int32_t axis_x, axis_y;
static unsigned positions, velocities;
static unsigned position_counts[4], character_positions;
static float last_body[4][3];
static float last_velocity[4][3];
static unsigned equip_count, equip_id, equip_variant;
static int nested_gate;

static void equip(uint64_t event, uint64_t manager, uint64_t actor, uint64_t manager2,
                  unsigned kind, uint32_t id, unsigned variant, unsigned replace) {
    assert(nested_gate);
    assert(event == (uintptr_t)(heap + 0x1000 + 0x11c4));
    assert(actor == (uintptr_t)(heap + 0x1000 + 0x518));
    assert(manager == manager2 && manager == (uintptr_t)(heap + 0x15000));
    assert(kind == 1 && replace == 1);
    equip_count++;
    equip_id = id;
    equip_variant = variant;
}

uint64_t dm_gate_nest_enter(void) {
    assert(!nested_gate);
    nested_gate = 1;
    return 0x1234567890ull;
}

void dm_gate_nest_leave(uint64_t saved_top) {
    assert(nested_gate && saved_top == 0x1234567890ull);
    nested_gate = 0;
}

uint64_t now_ns(void) { return tick; }
void dm_input_current(uint64_t *b, int32_t *x, int32_t *y) { *b = buttons; *x = axis_x; *y = axis_y; }

static float radius(uint64_t collision) { (void)collision; return 1.0f; }
static void body_position(uint64_t body, const float *value) {
    assert(body >= (uintptr_t)(heap + 0x12000) && body < (uintptr_t)(heap + 0x12400));
    unsigned index = (body - (uintptr_t)(heap + 0x12000)) / 0x100;
    memcpy(last_body[index], value, 12);
    position_counts[index]++;
    positions++;
}
static void body_velocity(uint64_t body, const float *value, int flags) {
    assert(body >= (uintptr_t)(heap + 0x12000) && body < (uintptr_t)(heap + 0x12400));
    assert(!flags);
    memcpy(last_velocity[(body - (uintptr_t)(heap + 0x12000)) / 0x100], value, 12);
    velocities++;
}

int dm_guest_heap_readable(uint64_t p, size_t n) {
    uintptr_t base = (uintptr_t)heap;
    return p >= base && n <= sizeof heap && p - base <= sizeof heap - n;
}
void dm_guest_write_prepare(void *p, size_t n) {
    assert(dm_guest_heap_readable((uintptr_t)p, n));
    writes++;
}
void gate_obs_set(int id, void (*fn)(uint64_t *, int)) {
    assert(id > 0 && id < OBS_MAX);
    callbacks[id] = fn;
}
int gate_obs_present(int id) { return id > 0 && id < OBS_MAX && callbacks[id] != NULL; }

static void put64(void *p, uint64_t v) { memcpy(p, &v, 8); }
static void put32(void *p, uint32_t v) { memcpy(p, &v, 4); }
static uint32_t get32(void *p) { uint32_t v; memcpy(&v, p, 4); return v; }

int main(int argc, char **argv) {
    assert(DM_GAME_PROGRAM_ID == 0x0400380020056000ull);
    assert(!dm_raiders_mods_available());
    uint8_t *image = calloc(1, 0x4e40000);
    assert(image);
    g_nmod = 1;
    strcpy(g_mod[0].name, "main");
    strcpy(g_mod[0].build_id, argc > 1 ? argv[1] : RAIDERS_BUILD);
    g_mod[0].base = image;

    void (*ready)(uint64_t *, int) = callbacks[OBS_RAIDERS_SHOOT_READY];
    callbacks[OBS_RAIDERS_SHOOT_READY] = NULL;
    assert(!dm_raiders_mods_available());
    dm_raiders_mods_set(3);
    assert(!dm_raiders_mods_get());
    callbacks[OBS_RAIDERS_SHOOT_READY] = ready;
    if (argc > 1) {
        assert(!dm_raiders_mods_available());
        dm_raiders_mods_set(3);
        assert(!dm_raiders_mods_get());
        free(image);
        puts("wrong build rejected");
        return 0;
    }

    uint8_t *shooter = heap + 0x4000, *player = heap + 0x1000, *owner = heap + 0x5000;
    uint32_t key = 0x13735e37;
    put64(image + 0x4d24140, (uintptr_t)heap);
    put32(heap, key);
    put64(shooter, (uintptr_t)(image + 0x4b24de8));
    put64(player, (uintptr_t)(image + 0x4b1f698));
    put64(shooter + 0x2b0, (uintptr_t)owner);
    put64(owner + 0x108, (uintptr_t)player);
    put32(player + 0xd0, key);
    uint64_t regs[31] = {0};
    regs[19] = (uintptr_t)shooter;
    regs[0] = (uintptr_t)player + 0x614;
    put32(player + 0x614, key ^ 0x3e800000);
    put32(player + 0x61c, key ^ 0x3f000000);
    put32(shooter + 0x68, key ^ 0x3f000000);
    put32(shooter + 0x6c, 0x40800000);

    uint8_t before[sizeof heap];
    memcpy(before, heap, sizeof heap);
    callbacks[OBS_RAIDERS_SHOOTER](regs, 0);
    callbacks[OBS_RAIDERS_INK](regs, 0);
    assert(!memcmp(before, heap, sizeof heap) && writes == 0);

    dm_raiders_mods_set(DM_RAIDERS_INFINITE_INK);
    callbacks[OBS_RAIDERS_SHOOTER](regs, 0);
    assert(get32(player + 0x614) == (key ^ 0x3f800000));
    assert(get32(player + 0x61c) == (key ^ 0x3f800000));
    put32(player + 0x614, key ^ 0x3e800000);
    callbacks[OBS_RAIDERS_INK](regs, 0);
    assert(get32(player + 0x614) == (key ^ 0x3f800000));

    dm_raiders_mods_set(DM_RAIDERS_RAPID_FIRE);
    regs[0] = (uintptr_t)shooter;
    callbacks[OBS_RAIDERS_SHOOT_READY](regs, 0);
    assert(get32(shooter + 0x68) == (key ^ 0x3f800000) && get32(shooter + 0x6c) == 0);

    dm_raiders_mods_set(0);
    memcpy(before, heap, sizeof heap);
    unsigned writes_before = writes;
    callbacks[OBS_RAIDERS_SHOOTER](regs, 0);
    callbacks[OBS_RAIDERS_INK](regs, 0);
    callbacks[OBS_RAIDERS_SHOOT_READY](regs, 0);
    assert(!memcmp(before, heap, sizeof heap) && writes == writes_before);

    uint8_t *collision = heap + 0x8000, *wrapper = heap + 0x10000;
    uint8_t *character = heap + 0x10100, *shape = heap + 0x11000;
    put64(player + 0x1240, (uintptr_t)collision);
    put64(collision + 0x7428, (uintptr_t)owner);
    put64(collision + 0x7438, (uintptr_t)wrapper);
    put64(wrapper + 8, (uintptr_t)character);
    put64(character + 0x20, (uintptr_t)(heap + 0x12000));
    put64(collision + 0x28, (uintptr_t)shape);
    put64(player + 8, (uintptr_t)shape);
    put32(shape + 0x2d8, 0x3f000000);
    for (int i = 1; i < 4; i++) put64(collision + 0x7280 + (i - 1) * 8, (uintptr_t)(heap + 0x12000 + i * 0x100));
    uint8_t *camera = heap + 0x13000;
    put64(player + 0x1210, (uintptr_t)camera);
    put64(camera, (uintptr_t)(image + 0x4b20300));
    float orientation[] = {1, 0, 0, 0, 1, 0, 0, 0, 1};
    memcpy(camera + 0x3c, orientation, sizeof orientation);
    float origin[] = {10, 20, 30};
    memcpy(player + 0x10, origin, 12);
    for (int i = 0; i < 4; i++) {
        uint8_t *body = heap + 0x12000 + i * 0x100;
        memcpy(body + 0xac, &origin[0], 4);
        memcpy(body + 0xbc, &origin[1], 4);
        memcpy(body + 0xcc, &origin[2], 4);
        memcpy(body + 0xdc, &origin[0], 4);
        memcpy(body + 0xec, &origin[1], 4);
        memcpy(body + 0xfc, &origin[2], 4);
    }
    regs[0] = (uintptr_t)owner;
    g_body_position = body_position;
    g_body_velocity = body_velocity;
    g_collision_radius = radius;

    dm_raiders_mods_set(DM_RAIDERS_FLY);
    callbacks[OBS_RAIDERS_MOVE](regs, 0);
    uint64_t filtered = DM_BTN_R | DM_BTN_L | DM_BTN_LS | DM_BTN_ZR | DM_BTN_A;
    int32_t fx = 32767, fy = -32767;
    dm_raiders_mods_filter_input(&filtered, &fx, &fy);
    assert(filtered == (DM_BTN_ZR | DM_BTN_A) && !fx && !fy);
    assert(positions == 4 && velocities == 4 && character_positions == 0);
    assert(last_body[0][1] == 20.5f && last_body[1][1] == 20.f);
    buttons = DM_BTN_R;
    tick += 50000000;
    callbacks[OBS_RAIDERS_MOVE](regs, 0);
    assert(fabsf(last_body[0][1] - 20.5f) < 0.0001f);
    assert(fabsf(last_body[1][1] - 20.f) < 0.0001f);
    regs[28] = (uintptr_t)player;
    callbacks[OBS_RAIDERS_FINISH](regs, 0);
    float transformed;
    memcpy(&transformed, heap + 0x12000 + 0xbc, 4);
    assert(fabsf(transformed - 20.3f) < 0.0001f);
    memcpy(&transformed, heap + 0x12000 + 0xec, 4);
    assert(fabsf(transformed - 20.3f) < 0.0001f);
    float root_y;
    memcpy(&root_y, player + 0x14, 4);
    assert(fabsf(root_y - 20.3f) < 0.0001f);
    float source_y;
    memcpy(&source_y, shape + 0x2c0, 4);
    assert(fabsf(source_y - 20.3f) < 0.0001f);
    assert(fabsf(last_velocity[1][1] - 6.f) < 0.0001f);
    assert(fabsf(last_velocity[1][0]) < 0.0001f && fabsf(last_velocity[1][2]) < 0.0001f);

    unsigned before_swim_character = character_positions;
    dm_raiders_mods_set(DM_RAIDERS_SWIM);
    float on_ground[] = {10, 8, 30};
    memcpy(player + 0x10, on_ground, 12);
    buttons = DM_BTN_ZL;
    axis_x = 32767; axis_y = 0;
    tick += 50000000;
    callbacks[OBS_RAIDERS_MOVE](regs, 0);
    assert(character_positions == before_swim_character && position_counts[0] > 0);
    assert(fabsf(last_body[1][1] - 8.f) < 0.0001f);
    tick += 50000000;
    callbacks[OBS_RAIDERS_MOVE](regs, 0);
    assert(last_body[1][0] > 10.f);
    assert(fabsf(last_velocity[1][0] - 6.f) < 0.0001f);
    filtered = DM_BTN_ZL | DM_BTN_L | DM_BTN_R | DM_BTN_LS;
    fx = 32767; fy = -32767;
    dm_raiders_mods_filter_input(&filtered, &fx, &fy);
    assert(filtered == DM_BTN_ZL && !fx && !fy);
    buttons = DM_BTN_L;
    tick += 50000000;
    callbacks[OBS_RAIDERS_MOVE](regs, 0);
    assert(fabsf(last_velocity[1][1]) < 0.0001f);
    buttons = 0;
    tick += 50000000;
    unsigned before_release = positions;
    callbacks[OBS_RAIDERS_MOVE](regs, 0);
    assert(positions == before_release);
    filtered = 0; fx = 32767; fy = -32767;
    dm_raiders_mods_filter_input(&filtered, &fx, &fy);
    assert(filtered == 0 && fx == 32767 && fy == -32767);

    dm_raiders_mods_set(0);
    writes_before = writes;
    unsigned calls = positions;
    memcpy(before, heap, sizeof heap);
    callbacks[OBS_RAIDERS_MOVE](regs, 0);
    filtered = DM_BTN_R | DM_BTN_L | DM_BTN_LS;
    fx = 32767;
    fy = -32767;
    dm_raiders_mods_filter_input(&filtered, &fx, &fy);
    assert(filtered == (DM_BTN_R | DM_BTN_L | DM_BTN_LS) && fx == 32767 && fy == -32767);
    assert(!memcmp(before, heap, sizeof heap) && writes == writes_before && positions == calls);

    dm_raiders_mods_set(0);
    g_equip = equip;
    uint8_t *manager = heap + 0x15000, *slot = heap + 0x16000;
    put64(player + 0x13e0, (uintptr_t)manager);
    put64(manager, (uintptr_t)(image + 0x4a5cef8));
    put64(manager + 0x130, (uintptr_t)slot);
    put32(slot + 0x10, 1);
    put32(slot + 0x14, 0x12345678);
    put32(slot + 0x18, 3);
    assert(dm_raiders_weapon_count() > 10);
    assert(!strcmp(dm_raiders_weapon_label(0), "Game Loadout"));
    dm_raiders_weapon_set(dm_raiders_weapon_count());
    assert(!dm_raiders_weapon_get());
    dm_raiders_weapon_set(1);
    callbacks[OBS_RAIDERS_MOVE](regs, 0);
    assert(equip_count == 1 && equip_id == weapons[1].id && equip_variant == 0);
    dm_raiders_weapon_set(0);
    callbacks[OBS_RAIDERS_MOVE](regs, 0);
    assert(equip_count == 2 && equip_id == 0x12345678 && equip_variant == 3);

    free(image);
    puts("Raiders mods: gates, ink, rapid fire, flight input, weapon request/restore and build guards pass");
    return 0;
}
