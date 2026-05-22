"""
解析 .eml 邮件文件，提取关键信息用于导入合同预审系统
"""
import email
import os
import sys
import re
from email.header import decode_header
from datetime import datetime
from pathlib import Path
import html
from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    """从HTML中提取纯文本"""
    def __init__(self):
        super().__init__()
        self.result = []
    def handle_data(self, data):
        self.result.append(data)
    def get_text(self):
        return ' '.join(self.result)

def decode_str(s):
    """解码邮件头字符串"""
    if not s:
        return ''
    parts = decode_header(s)
    result = []
    for data, charset in parts:
        if isinstance(data, bytes):
            try:
                result.append(data.decode(charset or 'utf-8', errors='replace'))
            except:
                result.append(data.decode('utf-8', errors='replace'))
        else:
            result.append(data)
    return ''.join(result)

def extract_name(addr_str):
    """从邮件地址中提取人名"""
    if not addr_str:
        return ''
    # 尝试从<>前提取名字
    decoded = decode_str(addr_str)
    match = re.match(r'^(.+?)\s*<', decoded)
    if match:
        name = match.group(1).strip().strip('"').strip("'")
        return name
    # 尝试从邮箱前缀提取
    match = re.match(r'^[\s"]*([^<"]+?)[\s"]*$', decoded)
    if match:
        return match.group(1).strip()
    return decoded.strip()

def extract_email_addr(addr_str):
    """提取邮箱地址"""
    if not addr_str:
        return ''
    match = re.search(r'<(.+?)>', addr_str)
    if match:
        return match.group(1)
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.]+', addr_str)
    if match:
        return match.group(0)
    return ''

def get_text_from_msg(msg):
    """从邮件消息中提取纯文本正文"""
    text_parts = []
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get('Content-Disposition', ''))
            
            if 'attachment' in content_disposition:
                continue
                
            if content_type == 'text/plain':
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    payload = part.get_payload(decode=True)
                    if payload:
                        text_parts.append(payload.decode(charset, errors='replace'))
                except:
                    pass
            elif content_type == 'text/html' and not text_parts:
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_text = payload.decode(charset, errors='replace')
                        extractor = HTMLTextExtractor()
                        extractor.feed(html_text)
                        plain = extractor.get_text()
                        # 清理多余空白
                        plain = re.sub(r'\s+', ' ', plain).strip()
                        if plain:
                            text_parts.append(plain)
                except:
                    pass
    else:
        content_type = msg.get_content_type()
        if content_type in ('text/plain', 'text/html'):
            try:
                charset = msg.get_content_charset() or 'utf-8'
                payload = msg.get_payload(decode=True)
                if payload:
                    raw = payload.decode(charset, errors='replace')
                    if content_type == 'text/html':
                        extractor = HTMLTextExtractor()
                        extractor.feed(raw)
                        raw = extractor.get_text()
                        raw = re.sub(r'\s+', ' ', raw).strip()
                    text_parts.append(raw)
            except:
                pass
    
    return '\n'.join(text_parts)

def clean_body(text, max_len=2000):
    """清理正文，去除引用和签名"""
    if not text:
        return ''
    
    lines = text.split('\n')
    cleaned = []
    skip = False
    
    for line in lines:
        # 跳过引用行
        if line.startswith('>'):
            continue
        # 跳过分隔线
        if re.match(r'^-{3,}$', line.strip()):
            continue
        # 跳过常见签名标记
        if 'Best Regards' in line or 'Best  Regards' in line:
            skip = True
        if '北京易诚互动' in line and skip:
            continue
        if skip and ('手机：' in line or 'E-mail：' in line or '电话：' in line or '地址：' in line):
            continue
        # 跳过邮件头信息引用
        if re.match(r'^\s*(发件人|发件时间|收件人|抄送|主题)：', line):
            skip = True
            continue
        if skip and line.strip().startswith('&'):
            continue
        # 跳过原始邮件标记
        if '---------' in line and '原始邮件' in line:
            skip = True
            continue
        if skip:
            if not line.strip():
                skip = False
            continue
        # 跳过免责声明
        if 'The information in this email is confidential' in line:
            skip = True
            continue
        if '收发邮件者请注意' in line:
            skip = True
            continue
        if '********************************************************' in line:
            skip = True
            continue
            
        cleaned.append(line)
    
    result = '\n'.join(cleaned).strip()
    # 去掉连续空行
    result = re.sub(r'\n{3,}', '\n\n', result)
    if len(result) > max_len:
        result = result[:max_len] + '...'
    return result

def parse_date(date_str):
    """解析邮件日期"""
    if not date_str:
        return None
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return None

def classify_email(subject):
    """根据主题分类邮件"""
    if '合同预审' in subject:
        if 'YCHD-ZB-2026-037' in subject or 'YCHD-ZB-2026-048' in subject:
            return '合同预审-灵码'
        return '合同预审-033'
    elif '特批申请' in subject:
        return '特批申请'
    elif '投标申请' in subject:
        return '投标申请'
    elif '用印特批' in subject:
        return '用印特批'
    elif '开放权限' in subject:
        return '开放权限'
    else:
        return '其他'

def main():
    folder = Path('/Users/cm/Documents/kiro/project/YCHD2026-033 九江银行2026年鄱阳湖数据中心灾备完善项目-GPU算力服务器')
    
    emails_data = []
    
    for eml_file in sorted(folder.glob('*.eml')):
        try:
            with open(eml_file, 'rb') as f:
                msg = email.message_from_bytes(f.read())
            
            subject = decode_str(msg.get('Subject', ''))
            from_addr = msg.get('From', '')
            to_addr = msg.get('To', '')
            cc_addr = msg.get('Cc', '')
            date_str = msg.get('Date', '')
            
            sender_name = extract_name(from_addr)
            sender_email = extract_email_addr(from_addr)
            date_parsed = parse_date(date_str)
            category = classify_email(subject)
            
            body = get_text_from_msg(msg)
            body_clean = clean_body(body, max_len=3000)
            
            emails_data.append({
                'file': eml_file.name,
                'date': date_parsed or '未知',
                'subject': subject,
                'sender_name': sender_name,
                'sender_email': sender_email,
                'category': category,
                'body': body_clean,
            })
        except Exception as e:
            print(f"  解析失败: {eml_file.name}: {e}", file=sys.stderr)
    
    # 按日期排序
    emails_data.sort(key=lambda x: x['date'] if x['date'] != '未知' else '9999')
    
    # 按分类输出
    categories = {}
    for e in emails_data:
        cat = e['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(e)
    
    print(f"共解析 {len(emails_data)} 封邮件\n")
    
    for cat, items in sorted(categories.items()):
        print(f"\n{'='*60}")
        print(f"【{cat}】({len(items)}封)")
        print(f"{'='*60}")
        for i, e in enumerate(items, 1):
            print(f"\n--- [{i}] {e['date']} ---")
            print(f"  主题: {e['subject'][:80]}")
            print(f"  发件人: {e['sender_name']} <{e['sender_email']}>")
            if e['body']:
                # 只打印前500字
                body_preview = e['body'][:500]
                print(f"  正文: {body_preview}")
            else:
                print(f"  正文: (空或无法解析)")

if __name__ == '__main__':
    import io
    buf = io.StringIO()
    sys.stdout = buf
    try:
        main()
    finally:
        output = buf.getvalue()
        sys.stdout = sys.__stdout__
        out_path = '/Users/cm/Documents/kiro/project/backend/scripts/eml_analysis.txt'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f'Output written to {out_path} ({len(output)} chars)')
