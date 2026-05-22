"""
解析72封.eml邮件，原封不动提取正文，生成合同预审系统SQL导入脚本
"""
import email
import os
import re
import json
from email.header import decode_header
from email.utils import parsedate_to_datetime
from pathlib import Path
from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
    def handle_data(self, data):
        self.result.append(data)
    def get_text(self):
        return ' '.join(self.result)

def decode_str(s):
    if not s: return ''
    parts = decode_header(s)
    result = []
    for data, charset in parts:
        if isinstance(data, bytes):
            try: result.append(data.decode(charset or 'utf-8', errors='replace'))
            except: result.append(data.decode('utf-8', errors='replace'))
        else: result.append(data)
    return ''.join(result)

def extract_name(addr_str):
    if not addr_str: return ''
    decoded = decode_str(addr_str)
    match = re.match(r'^(.+?)\s*<', decoded)
    if match: return match.group(1).strip().strip('"').strip("'")
    return decoded.strip()

def extract_email_addr(addr_str):
    if not addr_str: return ''
    match = re.search(r'<(.+?)>', addr_str)
    if match: return match.group(1)
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', addr_str)
    if match: return match.group(0)
    return ''

def get_text_from_msg(msg):
    text_parts = []
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get('Content-Disposition', ''))
            if 'attachment' in cd: continue
            if ct == 'text/plain':
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    payload = part.get_payload(decode=True)
                    if payload: text_parts.append(payload.decode(charset, errors='replace'))
                except: pass
            elif ct == 'text/html' and not text_parts:
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_text = payload.decode(charset, errors='replace')
                        ext = HTMLTextExtractor()
                        ext.feed(html_text)
                        plain = ext.get_text()
                        plain = re.sub(r'\s+', ' ', plain).strip()
                        if plain: text_parts.append(plain)
                except: pass
    else:
        ct = msg.get_content_type()
        if ct in ('text/plain', 'text/html'):
            try:
                charset = msg.get_content_charset() or 'utf-8'
                payload = msg.get_payload(decode=True)
                if payload:
                    raw = payload.decode(charset, errors='replace')
                    if ct == 'text/html':
                        ext = HTMLTextExtractor()
                        ext.feed(raw)
                        raw = ext.get_text()
                        raw = re.sub(r'\s+', ' ', raw).strip()
                    text_parts.append(raw)
            except: pass
    return '\n'.join(text_parts)

def clean_body(text):
    """提取邮件正文：只保留发件人自己写的内容，去除所有引用和签名"""
    if not text: return ''

    # 策略1: 以 '-----原始邮件-----' 为分割线，只取之前的部分
    # 也匹配各种变体：----- Original Message -----, ---- 原始邮件 ---- 等
    for sep in ['-----原始邮件-----', '-----Original Message-----', '----- Original Message -----', '----原始邮件----']:
        if sep in text:
            text = text.split(sep)[0]
            break

    # 策略1.5: 以 '在 xxxx年xx月xx日 / 在 xxxx-xx-xx，xxx 写道：' 格式截断
    # 这是另一种引用格式，出现在正文的结尾
    text = re.split(r'\n\s*在\s*20\d{2}[年\-]', text)[0]
    # 也匹配 '在 xxxx-xx-xx xx:xx:xx，"xxx" <xxx> 写道：' 格式
    text = re.split(r'\n\s*在\s*20\d{2}-\d{2}-\d{2}', text)[0]

    # 策略2: 以 'Best Regards' / 'Best  Regards' 等签名开头的行，截断后面
    # 但要保留正文，只去掉签名部分
    lines = text.split('\n')
    cleaned = []
    in_signature = False
    for line in lines:
        # 检测签名行（Best Regards / Best  Regards 等）
        if re.match(r'^\s*Best\s+Regards', line, re.IGNORECASE):
            in_signature = True
        if in_signature:
            continue

        # 检测邮件头信息行（发件人：xxx / 发送时间：xxx 等），这类是引用漏网
        if re.match(r'^\s*(发件人|From|发件时间|发送时间|Date|收件人|To|抄送|Cc|主题|Subject)[：:]', line, re.IGNORECASE):
            # 从这行开始后面全是引用，直接截断
            break

        # 检测引用行（以 > 开头）
        if line.startswith('>'):
            continue

        # 跳过纯 nbsp 行
        if re.match(r'^\s*(&nbsp;|\u00a0)+\s*$', line):
            continue

        # 跳过免责声明
        if '收发邮件者请注意' in line or 'The information in this email is confidential' in line:
            break
        if '********************************************************' in line:
            break

        cleaned.append(line)

    result = '\n'.join(cleaned).strip()

    # 去掉尾部的空行和多余空白
    result = re.sub(r'\n{3,}', '\n\n', result)
    result = result.strip()

    # 去掉尾部签名模式
    # 1. 邮箱地址行
    result = re.sub(r'\n\s*\S+@\S+\s*$', '', result)
    # 2. 发送时间行
    result = re.sub(r'\n\s*发送时间[：:]\s*.*$', '', result, flags=re.MULTILINE)
    # 3. 名字 + 职位/部门（如 "赵迎春   内核部"）
    result = re.sub(r'\n\s*[\u4e00-\u9fff]{2,4}\s{2,}[\u4e00-\u9fff]+\s*$', '', result)
    # 4. 地址/电话/手机/E-mail开头的行以及后续行
    result = re.sub(r'\n\s*(地址|电话|手机|E-mail|邮箱|邮编)[：:].+$', '', result, flags=re.MULTILINE)
    # 5. 公司名行（北京易诚互动...）
    result = re.sub(r'\n\s*北京易诚互动.*$', '', result, flags=re.MULTILINE)
    # 6. 单独一个名字行（末尾2-4个中文字符，前面空行）
    result = re.sub(r'\n[\u4e00-\u9fff]{2,4}\s*$', '', result)
    # 6b. 名字 + 部门/职位（如 "赵迎春   内核部"、"胡首"）
    result = re.sub(r'\n[\u4e00-\u9fff]{2,4}(\s+[\u4e00-\u9fff]+)?\s*$', '', result)
    # 6c. 多行名字 + 部门残留
    result = re.sub(r'\n[\u4e00-\u9fff]{2,4}\s+[\u4e00-\u9fff]{1,10}\s*$', '', result)
    # 7. 日期格式行（如 20260331）
    result = re.sub(r'\n\s*20\d{6}\s*$', '', result)
    result = result.strip()

    # 多轮清理尾部签名残留
    for _ in range(3):
        prev = None
        while prev != result:
            prev = result
            # 单独名字行（可能有前导空白）
            result = re.sub(r'\n\s*[\u4e00-\u9fff]{2,4}\s*$', '', result)
            # 名字+部门
            result = re.sub(r'\n\s*[\u4e00-\u9fff]{2,4}\s+[\u4e00-\u9fff]{1,10}\s*$', '', result)
            # 邮箱
            result = re.sub(r'\n\s*\S+@\S+\s*$', '', result)
            # 地址/电话等
            result = re.sub(r'\n\s*(地址|电话|手机|E-mail|邮箱|邮编|mail)[：:].+$', '', result, flags=re.MULTILINE)
            # 公司名
            result = re.sub(r'\n\s*北京易诚互动.*$', '', result, flags=re.MULTILINE)
            # 日期
            result = re.sub(r'\n\s*20\d{6}\s*$', '', result)
            # 分隔线
            result = re.sub(r'\n\s*-{3,}\s*$', '', result)
            # "原始邮件"行
            result = re.sub(r'\n\s*原始邮件\s*$', '', result)
            # 多余空行
            result = re.sub(r'\n{3,}', '\n\n', result)
            result = result.strip()

    # 去掉 \r 字符
    result = result.replace('\r', '')

    return result

def escape_sql(s):
    """转义SQL字符串"""
    if not s: return ''
    return s.replace("'", "''").replace("\\", "\\\\")

# ============ 主逻辑 ============
folder = Path('/Users/cm/Documents/kiro/project/YCHD2026-033 九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器')

# 收件人邮箱 → 用户ID映射
EMAIL_TO_ID = {
    'changjy@belink.com': 'c75af014-ff4e-4720-8199-c779720cccb8',  # 常佳宇
    'zhaoyc1@belink.com': '6216d133-4017-41e4-8f27-b714cd72ab25',  # 赵迎春
    'mengtao@belink.com': '15f0dc3b-1473-4523-b698-4419ea5f45ef',  # 孟涛
    'changhx@belink.com': 'e5cf05ea-df4f-47fc-9adf-2e0e231f5168',  # 畅红霞
    'zhouxc@belink.com': 'd09f90a5-7652-44e6-bf2b-4b9d13b04d56',  # 周喜春
    'wangjl1@belink.com': '39caab2c-d43c-4f89-88ed-02c53bcffe89',  # 王建磊
    'wangyh@belink.com': 'aebe2c36-6588-4613-9b35-8fcfe160562a',  # 王娅惠
    'lvhq@belink.com': '6dcbeb05-9274-4469-b16c-d32d4553548b',     # 吕海青
    'wuqy@belink.com': '1abd0dda-55cd-4d4f-8e4a-7cb6520e5835',     # 吴起玥
    'wangyh3@belink.com': '7baf87ae-539c-4801-9e47-75dc4a07732a',  # 王宇航
    'bianying@belink.com': '05feb500-8e9d-4bd6-8592-db5550234dfa',  # 边莹
    'chenyu@belink.com': '39c2b898-b143-4f16-801b-9379bebf6d01',   # 陈宇
    'maofj@belink.com': '895cfce6-059e-4d64-9c5c-5ba54236fe73',    # 毛福建
    'zengshuo@belink.com': 'f9c21e4f-11eb-4793-b0f2-02219bcb4542', # 曾硕
    'hushou@belink.com': 'a0000001-0000-0000-0000-000000000001',   # 胡首
    'wangpeng@belink.com': 'a0000001-0000-0000-0000-000000000002', # 王朋
    'kongfq@belink.com': 'a0000001-0000-0000-0000-000000000003',   # 孔繁强
    'chenmin@belink.com': '90a8199b-df52-460e-a339-019c569a5d6c',  # 陈敏
    'xiemy@belink.com': '5a81730a-0421-40f8-af82-bb25436c4ec5',   # 谢明宇
}

# 解析所有邮件
all_emails = []
for eml_file in sorted(folder.glob('*.eml')):
    with open(eml_file, 'rb') as f:
        msg = email.message_from_bytes(f.read())
    
    subject = decode_str(msg.get('Subject', ''))
    from_addr = decode_str(msg.get('From', ''))
    from_email = extract_email_addr(from_addr)
    from_name = extract_name(from_addr)
    date_str = msg.get('Date', '')
    in_reply_to = (msg.get('In-Reply-To') or '').strip()
    message_id = (msg.get('Message-ID') or '').strip()
    is_subject_reply = subject.startswith('Re:') or subject.startswith('回复：') or subject.startswith('Re_') or subject.startswith('Re_Re_')
    
    try:
        dt = parsedate_to_datetime(date_str)
        date_iso = dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        date_iso = '2026-01-01 00:00:00'
    
    body_raw = get_text_from_msg(msg)
    body_clean = clean_body(body_raw)
    
    user_id = EMAIL_TO_ID.get(from_email)
    
    all_emails.append({
        'date': date_iso,
        'subject': subject,
        'from_name': from_name,
        'from_email': from_email,
        'user_id': user_id,
        'body': body_clean,
        'is_subject_reply': is_subject_reply,
        'in_reply_to': in_reply_to,
        'message_id': message_id,
    })

# 按日期排序
all_emails.sort(key=lambda x: x['date'])

# 分类：找出第一封（发起邮件）
first_email = None
changjy_comments = []  # 常佳宇后续发起（无Re:但有In-Reply-To）
other_replies = []     # 其他人的回复

for i, e in enumerate(all_emails):
    if not e['in_reply_to'] and not e['is_subject_reply']:
        first_email = e
        continue
    
    if e['from_email'] == 'changjy@belink.com' and not e['is_subject_reply']:
        # 常佳宇的无Re:邮件 = 评论
        changjy_comments.append(e)
    else:
        other_replies.append(e)

print(f"第一封: 1")
print(f"常佳宇评论: {len(changjy_comments)}")
print(f"其他回复: {len(other_replies)}")
print(f"总计: {1 + len(changjy_comments) + len(other_replies)}")

# ============ 生成SQL ============
contract_id = 'b0000001-0001-0001-0001-000000000001'
changjy_id = 'c75af014-ff4e-4720-8199-c779720cccb8'
sql_lines = []

# 1. 合同（描述=第一封邮件原文）
desc = escape_sql(first_email['body'])
sql_lines.append(f"-- 第一封邮件作为合同描述")
sql_lines.append(f"UPDATE contracts SET description = E'{desc}' WHERE id = '{contract_id}';")
sql_lines.append("")

# 2. 先删除旧的评论和评审回复
sql_lines.append("DELETE FROM comments WHERE contract_id = '{}';".format(contract_id))
sql_lines.append("")

# 3. 评审记录（6位关键评审人）
reviews = [
    ('c0000001-0001-0001-0001-000000000001', 'a0000001-0000-0000-0000-000000000001', '副总裁', '领导审批', 'approved'),
    ('c0000001-0001-0001-0001-000000000002', 'd09f90a5-7652-44e6-bf2b-4b9d13b04d56', '项目管理', '业务确认', 'approved'),
    ('c0000001-0001-0001-0001-000000000003', '6216d133-4017-41e4-8f27-b714cd72ab25', '内核部', '法务审核', 'pending'),
    ('c0000001-0001-0001-0001-000000000004', '15f0dc3b-1473-4523-b698-4419ea5f45ef', '内核部', '内核审核', 'pending'),
    ('c0000001-0001-0001-0001-000000000005', 'e5cf05ea-df4f-47fc-9adf-2e0e231f5168', '财务', '财务审批', 'approved'),
    ('c0000001-0001-0001-0001-000000000006', 'f9c21e4f-11eb-4793-b0f2-02219bcb4542', '销售', '销售确认', 'approved'),
]

review_id_map = {}
reviewer_ids = set()
for rid, uid, role, step, status in reviews:
    reviewer_ids.add(uid)
    review_id_map[uid] = rid

# 评审意见 - 从邮件中提取各评审人的关键审核意见
review_opinions = {
    'a0000001-0000-0000-0000-000000000001': '同意！',  # 胡首
    'd09f90a5-7652-44e6-bf2b-4b9d13b04d56': None,  # 周喜春 - 从邮件提取
    '6216d133-4017-41e4-8f27-b714cd72ab25': None,  # 赵迎春 - 从邮件提取
    '15f0dc3b-1473-4523-b698-4419ea5f45ef': None,  # 孟涛 - 从邮件提取
    'e5cf05ea-df4f-47fc-9adf-2e0e231f5168': None,  # 畅红霞 - 从邮件提取
    'f9c21e4f-11eb-4793-b0f2-02219bcb4542': None,  # 曾硕 - 从邮件提取
}

# 为每个评审人找最关键的审核意见邮件
reviewer_key_emails = {
    'd09f90a5-7652-44e6-bf2b-4b9d13b04d56': None,
    '6216d133-4017-41e4-8f27-b714cd72ab25': None,
    '15f0dc3b-1473-4523-b698-4419ea5f45ef': None,
    'e5cf05ea-df4f-47fc-9adf-2e0e231f5168': None,
    'f9c21e4f-11eb-4793-b0f2-02219bcb4542': None,
}

# 找赵迎春最详细的审核意见（03/30那封6点意见）
for e in other_replies:
    if e['from_email'] == 'zhaoyc1@belink.com' and '上下游合同有多项核心条款' in e['body']:
        reviewer_key_emails['6216d133-4017-41e4-8f27-b714cd72ab25'] = e
        break

# 找孟涛最详细的意见
for e in other_replies:
    if e['from_email'] == 'mengtao@belink.com' and '合同基础性错误' in e['body']:
        reviewer_key_emails['15f0dc3b-1473-4523-b698-4419ea5f45ef'] = e
        break
if not reviewer_key_emails['15f0dc3b-1473-4523-b698-4419ea5f45ef']:
    for e in other_replies:
        if e['from_email'] == 'mengtao@belink.com' and '鉴于此合同倒置问题' in e['body']:
            reviewer_key_emails['15f0dc3b-1473-4523-b698-4419ea5f45ef'] = e
            break

# 找畅红霞的意见
for e in other_replies:
    if e['from_email'] == 'changhx@belink.com' and '无遗漏' in e['body']:
        reviewer_key_emails['e5cf05ea-df4f-47fc-9adf-2e0e231f5168'] = e
        break

# 找周喜春的确认
for e in other_replies:
    if e['from_email'] == 'zhouxc@belink.com' and '已与客户沟通目标成交价' in e['body']:
        reviewer_key_emails['d09f90a5-7652-44e6-bf2b-4b9d13b04d56'] = e
        break

# 找曾硕的意见
for e in other_replies:
    if e['from_email'] == 'zengshuo@belink.com':
        reviewer_key_emails['f9c21e4f-11eb-4793-b0f2-02219bcb4542'] = e
        break

# 写入评审记录
sql_lines.append("-- ============ 评审记录 ============")
for rid, uid, role, step, status in reviews:
    key_email = reviewer_key_emails.get(uid)
    if key_email:
        opinion = escape_sql(key_email['body'])
        updated = key_email['date']
    else:
        opinion = ''
        updated = first_email['date']
    
    # 胡首特殊处理
    if uid == 'a0000001-0000-0000-0000-000000000001':
        opinion = '同意！'
        updated = '2026-04-27 18:25:11'
    
    sql_lines.append(f"INSERT INTO reviews (id, contract_id, reviewer_id, role, step, opinion, status, likes, liked_by, created_at, updated_at)")
    sql_lines.append(f"VALUES ('{rid}', '{contract_id}', '{uid}', '{role}', '{step}', E'{opinion}', '{status}', 0, ARRAY[]::varchar[], '{first_email['date']}', '{updated}');")
    sql_lines.append("")

# 4. 评审下的回复 - 其他人的审核相关讨论
# 确定哪些回复属于评审讨论（赵迎春、孟涛的review下的讨论）
review_comment_emails = {
    '6216d133-4017-41e4-8f27-b714cd72ab25': [],  # 赵迎春review下的回复
    '15f0dc3b-1473-4523-b698-4419ea5f45ef': [],  # 孟涛review下的回复
}

# 王娅惠、王建磊针对赵迎春审核意见的回复 → 赵迎春review下
# 常佳宇回复孟涛的 → 孟涛review下
for e in other_replies:
    if e['from_email'] == 'wangyh@belink.com' and '关于集成改造' in e['body']:
        review_comment_emails['6216d133-4017-41e4-8f27-b714cd72ab25'].append(e)
    elif e['from_email'] == 'wangjl1@belink.com' and '标的物拆分' in e.get('body',''):
        review_comment_emails['6216d133-4017-41e4-8f27-b714cd72ab25'].append(e)
    elif e['from_email'] == 'wangjl1@belink.com' and '采购范围确认' in e.get('body',''):
        review_comment_emails['6216d133-4017-41e4-8f27-b714cd72ab25'].append(e)
    elif e['from_email'] == 'changjy@belink.com' and '灵码私有化平台交付' in e.get('body','') and e['date'] < '2026-04-23':
        review_comment_emails['15f0dc3b-1473-4523-b698-4419ea5f45ef'].append(e)
    elif e['from_email'] == 'wangyh@belink.com' and '所有软件已部署完成' in e.get('body',''):
        review_comment_emails['15f0dc3b-1473-4523-b698-4419ea5f45ef'].append(e)

sql_lines.append("-- ============ 评审下的回复 ============")
rc_idx = 100
for uid, emails in review_comment_emails.items():
    rid = review_id_map[uid]
    for e in sorted(emails, key=lambda x: x['date']):
        rc_idx += 1
        cid = f'd0000010-0001-0001-0001-{rc_idx:012d}'
        content = escape_sql(e['body'])
        sql_lines.append(f"INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)")
        sql_lines.append(f"VALUES ('{cid}', '{contract_id}', '{rid}', NULL, '{e['user_id']}', E'{content}', 0, ARRAY[]::varchar[], '{e['date']}', '{e['date']}');")
        sql_lines.append("")

# 5. 常佳宇的评论（后续发起邮件）
sql_lines.append("-- ============ 常佳宇的评论（后续发起邮件） ============")
comment_id_map = {}  # date -> comment_id，用于建立回复关系
cm_idx = 200
for e in changjy_comments:
    cm_idx += 1
    cid = f'd0000020-0001-0001-0001-{cm_idx:012d}'
    comment_id_map[e['date']] = cid
    content = escape_sql(e['body'])
    # 主题前缀作为标签
    subject_prefix = ''
    if '特批申请' in e['subject']: subject_prefix = '【特批申请】'
    elif '合同预审' in e['subject'] and 'ZB' in e['subject']: subject_prefix = '【合同预审-灵码】'
    elif '合同预审' in e['subject']: subject_prefix = '【合同预审】'
    elif '投标申请' in e['subject']: subject_prefix = '【投标申请】'
    elif '用印特批' in e['subject']: subject_prefix = '【用印特批】'
    elif '开放权限' in e['subject']: subject_prefix = '【开放权限申请】'
    
    if subject_prefix and not content.startswith(subject_prefix):
        content = subject_prefix + content
    
    sql_lines.append(f"INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)")
    sql_lines.append(f"VALUES ('{cid}', '{contract_id}', NULL, NULL, '{changjy_id}', E'{content}', 0, ARRAY[]::varchar[], '{e['date']}', '{e['date']}');")
    sql_lines.append("")

# 6. 其他人的回复 - 挂在最近的前一条常佳宇评论下
sql_lines.append("-- ============ 评论回复 ============")
rp_idx = 300
# 建立时间线，找每条回复前最近的常佳宇评论
changjy_dates = sorted(comment_id_map.keys())

for e in sorted(other_replies, key=lambda x: x['date']):
    # 跳过已归入评审回复的
    already_in_review = False
    for uid, emails in review_comment_emails.items():
        if e in emails:
            already_in_review = True
            break
    if already_in_review: continue
    
    # 跳过没有user_id的
    if not e['user_id']: continue
    
    # 跳过评审人（他们的意见已在review中体现）
    if e['user_id'] in reviewer_ids and e['from_email'] not in ['changjy@belink.com']:
        # 简单"同意"/"确认"类的回复可以作为评论回复
        body_short = e['body'].strip()
        if len(body_short) > 200:
            continue  # 长内容评审意见已在review中，跳过
    
    rp_idx += 1
    cid = f'd0000030-0001-0001-0001-{rp_idx:012d}'
    
    # 找最近的常佳宇评论作为parent
    parent_id = 'NULL'
    for d in reversed(changjy_dates):
        if d <= e['date']:
            parent_id = f"'{comment_id_map[d]}'"
            break
    
    content = escape_sql(e['body'])
    if not content: continue  # 跳过空内容
    
    sql_lines.append(f"INSERT INTO comments (id, contract_id, review_id, parent_comment_id, author_id, content, likes, liked_by, created_at, updated_at)")
    sql_lines.append(f"VALUES ('{cid}', '{contract_id}', NULL, {parent_id}, '{e['user_id']}', E'{content}', 0, ARRAY[]::varchar[], '{e['date']}', '{e['date']}');")
    sql_lines.append("")

# 写入文件
output_path = '/Users/cm/Documents/kiro/project/backend/scripts/import_email_data_v4.sql'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(sql_lines))

print(f"\nSQL written to {output_path}")
print(f"Total SQL lines: {len(sql_lines)}")